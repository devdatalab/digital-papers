#!/usr/bin/env python3
"""Prize-share-by-occupation data for the "Father occupation across Nobel

Renders supplementary panel A10; pooled shares also appear in panels A8/A9.
fields" annotation pane.

Why this file exists:
    The occ_shares appendix tables give census and *overall* laureate share per
    occupation group, but not the per-Nobel-field breakdown the reference
    dashboard (nobel-agents/prize_share_by_occupation) visualises. This script
    computes, for each classification level (10 broad groups / 24-group / detailed occ1950) and
    each group, the share whose father falls in that group among: all laureates
    and each of the four fields (Chemistry, Economics, Medicine, Physics). The
    census bar and the canonical group set/order are taken from the existing
    occ_shares_{10,25}group.json so the pane stays consistent with Appendix
    PDF Tables A2/A3. All laureate quantities are computed from the linked microdata,
    so the pooled `all` share can differ from the Stata tables by ~1-2 pts.

Upstream dependencies:
    package/data/nobelists_analysis.csv                     (occ1950, category)
    package/code/occ_shares/output/occ_shares_occ1950_list.json  (occ1950 -> group crosswalk)
    package/code/occ_shares/output/occ_shares_10group.json       (10-group set + census_pct)
    package/code/occ_shares/output/occ_shares_25group.json       (24-group set + census_pct)
    These crosswalk/census inputs are the occ_shares script's own output, so this
    script depends on upstream generation output — not on the site copy. Run
    occ_shares.py before this one (run package/code/run_all.py first). Nothing here writes
    into src/lib/data; sync_to_site.py does that. See package/code/README.md.

Output:
    generators/occ_prize_shares/output/occ_prize_shares.json

Run:
    python generators/occ_prize_shares/occ_prize_shares.py
    # or regenerate everything: python make_all.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "package" / "data"
# Crosswalk/census come from the occ_shares script's output (not the site copy),
# keeping this script independent of src/lib/data. occ_shares.py must run first.
OCC_SHARES_OUT = REPO_ROOT / "package" / "code" / "occ_shares" / "output"
OUT_DIR = Path(__file__).resolve().parent / "output"

FIELDS = ["Chemistry", "Economics", "Medicine", "Physics"]


def load_crosswalk() -> dict[int, dict]:
    """occ1950 code -> broad groups and detailed occupation identifier."""
    rows = json.loads((OCC_SHARES_OUT / "occ_shares_occ1950_list.json").read_text())["data"]
    return {r["occ1950"]: {"group_10": r["group_10"], "group_25": r["group_25"],
                           "occ1950": str(r["occ1950"])} for r in rows}


def load_group_meta(fname: str, key: str) -> list[dict]:
    """Canonical group list (label, census_pct) in file order = sort order.

    `key` selects the crosswalk field this level groups on (group_10/group_25).
    """
    rows = json.loads((OCC_SHARES_OUT / fname).read_text())["data"]
    return [{"label": r["label"].strip(), "census_pct": r["census_pct"], "xw_key": key}
            for r in rows]


def load_laureates() -> list[dict]:
    with (DATA_DIR / "nobelists_analysis.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def occ_code(row: dict) -> int | None:
    v = row.get("occ1950", "")
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def build_level(level_label: str, groups: list[dict], xw_field: str,
                laureates: list[dict], crosswalk: dict[int, dict]) -> dict:
    # Per-population denominators (matched laureates) and per (group, pop) counts.
    denom: dict[str, int] = defaultdict(int)          # pop -> matched laureates
    count: dict[tuple[str, str], int] = defaultdict(int)  # (group_label, pop) -> n
    n_by_group: dict[str, int] = defaultdict(int)     # group_label -> matched fathers

    for lau in laureates:
        code = occ_code(lau)
        if code is None or code not in crosswalk:
            continue
        group = (crosswalk[code].get(xw_field) or "").strip()
        if not group:
            continue
        cat = lau["category"].strip()
        pops = ["all"] + ([cat] if cat in FIELDS else [])
        for pop in pops:
            denom[pop] += 1
            count[(group, pop)] += 1
        n_by_group[group] += 1

    out_groups = []
    for i, g in enumerate(groups):
        label = g["label"]
        group_id = g.get("id", label)
        shares = {}
        for pop in ["all", *FIELDS]:
            d = denom.get(pop, 0)
            shares[pop] = round(100.0 * count.get((group_id, pop), 0) / d, 4) if d else 0.0
        out_groups.append({
            "id": group_id,
            "label": label,
            "sort_order": i,
            "laureate_n": n_by_group.get(group_id, 0),
            "census_pct": g["census_pct"],
            "shares": shares,
        })
    return {"label": level_label, "groups": out_groups}


def main() -> None:
    crosswalk = load_crosswalk()
    laureates = load_laureates()
    n_total = len(laureates)
    n_matched = sum(1 for l in laureates if occ_code(l) in crosswalk)

    groups10 = load_group_meta("occ_shares_10group.json", "group_10")
    groups25 = load_group_meta("occ_shares_25group.json", "group_25")

    detailed_rows = json.loads((OCC_SHARES_OUT / "occ_shares_occ1950_list.json").read_text())["data"]
    occupations = [{"id": str(r["occ1950"]), "label": r["display"],
                    "census_pct": r["census_pct"]}
                   for r in sorted(detailed_rows, key=lambda r: r["occ1950"])]

    payload = {
        "meta": {
            "script": "occ_prize_shares",
            "fields": FIELDS,
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_total": n_total,
            "n_matched": n_matched,
        },
        "levels": {
            "group_10": build_level("10 broad groups", groups10, "group_10", laureates, crosswalk),
            "group_25": build_level("24-group classification", groups25, "group_25", laureates, crosswalk),
            "occ1950": build_level("Detailed occupations (occ1950)", occupations, "occ1950", laureates, crosswalk),
        },
    }

    # --- Reconciliation asserts (fail loudly if the join or numbers drift) ---
    assert n_matched >= 0.9 * n_total, f"only {n_matched}/{n_total} laureates matched crosswalk"
    for lvl_id, lvl in payload["levels"].items():
        for g in lvl["groups"]:
            for pop, s in g["shares"].items():
                assert 0.0 <= s <= 100.0, f"{lvl_id}/{g['id']}/{pop} share out of range: {s}"
        # per-population shares across groups sum to ~100%
        for pop in ["all", *FIELDS]:
            tot = sum(g["shares"][pop] for g in lvl["groups"])
            assert 95.0 <= tot <= 105.0, f"{lvl_id} {pop} shares sum to {tot:.1f}, expected ~100"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "occ_prize_shares.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  Wrote {out.relative_to(REPO_ROOT)}")

    # --- Printed sanity check ---
    print(f"\nmatched {n_matched}/{n_total} laureates")
    g10 = payload["levels"]["group_10"]["groups"]
    top = max(g10, key=lambda x: x["shares"]["all"])
    print(f"top 10-group by all-laureate share: {top['label']} "
          f"all={top['shares']['all']:.1f}%  census={top['census_pct']:.1f}%")
    print("  by field:", {f: top["shares"][f] for f in FIELDS})


if __name__ == "__main__":
    main()
