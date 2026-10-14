#!/usr/bin/env python3
"""Extract the title-page scatter dataset from the Stata analysis file.

Why this file exists:
    The digital publication's primary visualization (a jittered scatter of
    laureates by prize year vs. their father's national rank, on the title page)
    needs a small, browser-friendly slice of the analysis data. Shipping the full
    1.2 MB Stata file to the client would be wasteful and would couple the static
    site to Stata. This script reads the replication dataset and emits a compact
    JSON the SvelteKit app imports.

Inputs (upstream dependency):
    package/data/nobelists_analysis.csv       -- the analysis dataset (Stata).
    package/data/laureates_grounded_search.csv -- per-laureate provenance from
        a Gemini grounded web search: the occupation it found for the father, the
        supporting quote, its reasoning, and the source URLs it consulted. Merged
        in by (normalized) laureate name so the Data Explorer can surface where
        each father-occupation classification came from.

Output:
    generators/extract_viz_data/output/nobelists.json
    Synced to src/lib/data/nobelists.json by sync_to_site.py (which the app
    imports via src/lib/data/index.ts and NobelRankScatter.svelte). This script
    never writes into src/lib/data itself — see package/code/README.md.

Run (manual regeneration step, not part of `npm run build`):
    conda activate nobel-prizes   # or the local base env
    python generators/extract_viz_data/extract_viz_data.py
    # or regenerate everything: python make_all.py

Notes / data caveats:
    - All 735 laureate rows are emitted. 22 have no computable percentile rank;
      the title-page scatter skips them per metric (a null rank can't be plotted),
      but the Data Explorer table still lists them.
    - Rank values are rounded to 1 decimal to keep the JSON small; missing ranks
      serialize as null.
    - The grounded-search merge is by normalized name (case/punctuation folded).
      Every analysis laureate matches exactly one grounded row and names are
      unique on both sides, so the join is unambiguous; laureates without a
      grounded match simply get empty provenance fields.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd

# --- Paths (resolved relative to the repo root, three levels up from this file) ---
REPO_ROOT = Path(__file__).resolve().parents[2]
DTA_PATH = REPO_ROOT / "package" / "data" / "nobelists_analysis.csv"
GROUNDED_PATH = REPO_ROOT / "package" / "data" / "laureates_grounded_search.csv"
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_PATH = OUT_DIR / "nobelists.json"

# --- Field configuration ------------------------------------------------------
# Rank metrics offered in the y-axis toggle. `key` matches the JSON field and
# the Stata column; `label` is the dropdown text; `axisLabel` labels the y-axis.
METRICS = [
    {
        "key": "med_inctot_rank",
        "column": "med_inctot_rank",
        "label": "National father-income rank",
        "axisLabel": "Father's income rank within country (percentile)",
    },
    {
        "key": "global_med_inctot_rank",
        "column": "global_med_inctot_rank",
        "label": "Global father-income rank",
        "axisLabel": "Father's income rank, global (percentile)",
    },
    {
        "key": "educ_rank",
        "column": "educ_rank",
        "label": "Father-education rank",
        "axisLabel": "Father's education rank within country (percentile)",
    },
    {
        "key": "prestige_rank",
        "column": "prestige_rank",
        "label": "Father-occupation prestige rank",
        "axisLabel": "Father's occupation prestige rank (percentile)",
    },
]

RANK_COLUMNS = [m["column"] for m in METRICS]


def _clean_str(value) -> str:
    """Return a stripped string, or '' for missing values."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def _norm_name(value) -> str:
    """Fold a laureate name to a join key: lowercase, punctuation stripped.

    The grounded-search file and the analysis file spell the same names with
    minor punctuation differences (e.g. "Marie Curie, ne Sklodowska"). Folding
    to alphanumerics + single spaces makes the join exact for all 735 rows.
    """
    s = _clean_str(value).lower()
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _split_sources(value) -> list[str]:
    """Parse the pipe-delimited `grounding_urls` field into a clean URL list."""
    return [u.strip() for u in _clean_str(value).split("|") if u.strip()]


def load_grounded(path: Path) -> dict[str, dict]:
    """Map normalized laureate name -> grounded-search provenance fields.

    Returns the Gemini-found father occupation, the supporting quote, the
    occupation reasoning, and the list of source URLs, keyed so `build_payload`
    can attach them to the matching analysis row.
    """
    if not path.exists():
        return {}
    gdf = pd.read_csv(path)
    out: dict[str, dict] = {}
    for _, r in gdf.iterrows():
        out[_norm_name(r.get("subject_name"))] = {
            "foundOcc": _clean_str(r.get("found_father_occ")),
            "evidenceQuote": _clean_str(r.get("quote")),
            "occReasoning": _clean_str(r.get("occupation_reasoning")),
            "sources": _split_sources(r.get("grounding_urls")),
        }
    return out


# Empty provenance for laureates without a grounded-search match.
_EMPTY_GROUNDED = {"foundOcc": "", "evidenceQuote": "", "occReasoning": "", "sources": []}


def _opt_int(value):
    """Return an int, or None for missing/non-finite values."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return int(round(f)) if math.isfinite(f) else None


def _opt_rank(value):
    """Return a rank rounded to 1 decimal, or None for missing/non-finite."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return round(f, 1) if math.isfinite(f) else None


def build_payload(df: pd.DataFrame, grounded: dict[str, dict]) -> dict:
    """Transform the analysis frame into the compact JSON payload."""
    # Emit every laureate. The 22 rows with no computable rank cannot be plotted
    # on the title-page scatter (which skips null ranks per metric), but they are
    # still real laureates with identity + occupation + grounded-search fields, so
    # the Data Explorer table should list them. Downstream consumers filter nulls.
    kept = df.copy()

    rows = []
    for i, (_, r) in enumerate(kept.iterrows()):
        ranks = {m["key"]: _opt_rank(r.get(m["column"])) for m in METRICS}
        prov = grounded.get(_norm_name(r.get("name")), _EMPTY_GROUNDED)
        rows.append(
            {
                "id": i,
                "name": _clean_str(r.get("name")),
                "year": _opt_int(r.get("prize_year")),
                "category": _clean_str(r.get("category")),
                "country": _clean_str(r.get("country_name")),
                "fatherOcc": _clean_str(r.get("father_occupation")),
                "awardAge": _opt_int(r.get("award_age")),
                "share": _opt_int(r.get("prize_share")),
                "gender": _clean_str(r.get("gender")),
                "ranks": ranks,
                # Gemini grounded-search provenance for the father's occupation.
                "foundOcc": prov["foundOcc"],
                "evidenceQuote": prov["evidenceQuote"],
                "occReasoning": prov["occReasoning"],
                "sources": prov["sources"],
            }
        )

    # Deterministic order (year, then name) so the committed JSON has stable
    # diffs regardless of the source row order.
    rows.sort(key=lambda d: (d["year"] if d["year"] is not None else 0, d["name"]))
    for new_id, row in enumerate(rows):
        row["id"] = new_id

    years = [row["year"] for row in rows if row["year"] is not None]
    payload = {
        "meta": {
            "n": len(rows),
            "yearMin": min(years),
            "yearMax": max(years),
            "generatedFrom": DTA_PATH.name,
        },
        "metrics": [
            {"key": m["key"], "label": m["label"], "axisLabel": m["axisLabel"]}
            for m in METRICS
        ],
        "rows": rows,
    }
    return payload


def main() -> None:
    if not DTA_PATH.exists():
        raise SystemExit(f"Input not found: {DTA_PATH}")

    df = pd.read_csv(DTA_PATH)
    grounded = load_grounded(GROUNDED_PATH)
    payload = build_payload(df, grounded)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(
        f"Wrote {payload['meta']['n']} rows "
        f"({payload['meta']['yearMin']}-{payload['meta']['yearMax']}) to "
        f"{OUT_PATH.relative_to(REPO_ROOT)}"
    )


if __name__ == "__main__":
    main()
