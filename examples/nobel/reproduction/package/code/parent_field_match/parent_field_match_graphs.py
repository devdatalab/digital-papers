#!/usr/bin/env python3
"""Parent-field occupation-share data for appendix figures.

Supplementary panels: A19. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Adapted from a/make_parent_field_match_graphs.py (the source repo's existing
    Python renderer). For each quality tier (good_match, prof_match, nonprof_match,
    weak_match) and each Nobel field (chemistry, physics, medicine, economics),
    computes the occupation share of father-field-matched laureates vs. the
    expected census share. Produces:
      - A JSON dataset of the plotted values (primary output)
      - Matplotlib figures matching the manuscript's appendix exhibits (secondary)

    Key difference from source: uses ipums_parent_field_census_shared.csv
    (pre-filtered subset) instead of the full ipums_global_sample.dta.

Variable derivation:
    Laureate parent fields and match types come from nobelists_analysis.csv,
    including the PDF paper's biographical overrides. The occupation crosswalk
    supplies the census comparison classifications only.

Upstream dependencies:
    data/nobelists_analysis.csv
    data/occ1950_sci_field_classification.csv
    data/ipums_parent_field_census_shared.csv

Output:
    code/parent_field_match/output/parent_field_match_shares.json

Run:
    python code/parent_field_match/parent_field_match_graphs.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"

FIELD_ORDER = ["chemistry", "physics", "medicine", "economics"]
FIELD_LABELS = {
    "chemistry": "Chemistry",
    "physics": "Physics",
    "medicine": "Physiology",
    "economics": "Economics",
}

QUALITY_CONFIG = {
    "good_match": {"match_types": {"prof_match", "nonprof_match"}},
    "prof_match": {"match_types": {"prof_match"}},
    "nonprof_match": {"match_types": {"nonprof_match"}},
    "weak_match": {"match_types": {"weak_match"}},
}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load laureate classifications with overrides, occ_map, and ipums CSV."""
    laureates = pd.read_csv(
        DATA_DIR / "nobelists_analysis.csv",
        usecols=["prize_year", "category", "occ1950", "country_name", "ipums_decade",
                 "parent_field", "parent_field_match_type"],
    )
    occ_map = pd.read_csv(
        DATA_DIR / "occ1950_sci_field_classification.csv",
        usecols=["occ1950", "match_type", "parent_field"],
    )
    ipums = pd.read_csv(DATA_DIR / "ipums_parent_field_census_shared.csv")

    # Preserve the final laureate classifications, including manual overrides.
    laureates = laureates.rename(columns={"parent_field_match_type": "match_type"})
    laureates["parent_field"] = laureates["parent_field"].fillna("none").str.strip().str.lower()
    laureates["match_type"] = laureates["match_type"].fillna("none").str.strip()
    laureates["category_key"] = laureates["category"].fillna("").str.strip().str.lower()

    # Keep only rows with a valid occ1950 and known field
    laureates = laureates[laureates["occ1950"].notna() & laureates["occ1950"].ne(9999)]
    laureates = laureates[laureates["category_key"].isin(FIELD_ORDER)]

    # Clean occ_map
    occ_map["match_type"] = occ_map["match_type"].fillna("").str.strip()
    occ_map["parent_field_key"] = occ_map["parent_field"].fillna("").str.strip().str.lower()
    occ_map = occ_map[occ_map["parent_field_key"].isin(FIELD_ORDER)]

    # Clean ipums CSV
    ipums["match_type"] = ipums["match_type"].fillna("").str.strip()
    ipums["parent_field"] = ipums["parent_field"].fillna("").str.strip().str.lower()
    ipums = ipums[ipums["occ1950"].notna()]

    return laureates, occ_map, ipums


def field_context(laureates: pd.DataFrame, field_key: str) -> pd.DataFrame:
    """For economics, restrict to prize_year >= 1969 (when the economics prize began)."""
    if field_key == "economics":
        return laureates[laureates["prize_year"] >= 1969].copy()
    return laureates.copy()


def weighted_census_share(
    context: pd.DataFrame,
    ipums: pd.DataFrame,
    field_key: str,
    match_types: set[str],
) -> float:
    """Weighted census occupation share, using laureate country-decade distribution as weights.

    Replicates the weighted_census_share() function from make_parent_field_match_graphs.py,
    adapted to use the pre-filtered CSV (which already has match_type and parent_field).
    """
    weights = (
        context.groupby(["country_name", "ipums_decade"], dropna=False)
        .size()
        .reset_index(name="laureates")
    )
    if weights.empty:
        return 0.0
    weights["cd_weight"] = weights["laureates"] / weights["laureates"].sum()

    # Filter the pre-filtered CSV to the relevant match_types and field
    selected = ipums[ipums["match_type"].isin(match_types) & (ipums["parent_field"] == field_key)]
    if selected.empty:
        return 0.0

    merged = selected.merge(weights[["country_name", "ipums_decade", "cd_weight"]], how="inner")
    if merged.empty:
        return 0.0

    return float((merged["occ_pop_share"] * merged["cd_weight"]).sum() * 100)


def build_panel(
    laureates: pd.DataFrame,
    ipums: pd.DataFrame,
    quality: str,
    field_key: str,
) -> dict:
    """Compute the bar-chart data for one quality × field panel."""
    config = QUALITY_CONFIG[quality]
    context = field_context(laureates, field_key)
    selected = context[
        context["match_type"].isin(config["match_types"])
        & (context["parent_field"] == field_key)
    ]

    overall_n = len(context)
    overall_selected = len(selected)
    census_share = weighted_census_share(context, ipums, field_key, config["match_types"])

    # Counts by prize category within this match-type filter
    cat_counts = context["category_key"].value_counts().to_dict()
    sel_cat_counts = selected["category_key"].value_counts().to_dict()

    bars = [
        {
            "row_id": "census",
            "label": "Census share",
            "share": round(census_share, 4),
            "count": None,
        },
        {
            "row_id": "overall",
            "label": "Overall laureate share",
            "share": round(100.0 * overall_selected / overall_n, 4) if overall_n else 0.0,
            "count": overall_selected,
        },
    ]
    for cat in FIELD_ORDER:
        denom = int(cat_counts.get(cat, 0))
        numer = int(sel_cat_counts.get(cat, 0))
        bars.append(
            {
                "row_id": cat,
                "label": f"{FIELD_LABELS[cat]} laureate share",
                "share": round(100.0 * numer / denom, 4) if denom else 0.0,
                "count": numer,
            }
        )

    return {
        "quality": quality,
        "field": field_key,
        "n_context": overall_n,
        "n_selected": overall_selected,
        "census_share": round(census_share, 4),
        "bars": bars,
    }


def main() -> None:
    for p in [
        DATA_DIR / "nobelists_analysis.csv",
        DATA_DIR / "occ1950_sci_field_classification.csv",
        DATA_DIR / "ipums_parent_field_census_shared.csv",
    ]:
        if not p.exists():
            raise SystemExit(f"Input not found: {p}")

    laureates, occ_map, ipums = load_data()
    print(f"Laureates (filtered): {len(laureates)}")

    panels = {}
    for quality in QUALITY_CONFIG:
        for field_key in FIELD_ORDER:
            key = f"{quality}_{field_key}"
            panels[key] = build_panel(laureates, ipums, quality, field_key)
            p = panels[key]
            print(
                f"  {key}: census={p['census_share']:.2f}%, "
                f"overall={p['bars'][1]['share']:.2f}% (n={p['n_selected']})"
            )

    payload = {
        "meta": {
            "script": "parent_field_match_graphs",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_laureates": len(laureates),
            "source_dofile": "a/graph_parent_field_match.do",
            "source_python": "a/make_parent_field_match_graphs.py",
        },
        "data": panels,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "parent_field_match_shares.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
