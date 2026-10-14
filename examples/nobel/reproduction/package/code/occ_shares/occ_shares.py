#!/usr/bin/env python3
"""Occupation-share tables for the appendix (Appendix Tables, occ_shares exhibits).

Supplementary panels: A9, A10, A17. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Replicates a/tables_occ_shares.do, which reads three pre-built DTA files
    produced by b/prep_occ_shares.do and writes LaTeX table fragments.  This
    script reads the same DTA files and writes equivalent JSON, producing four
    outputs that together reproduce the occupation-share appendix Tables A2
    and A3:

      occ_shares_10group.json    — 10 broad occ1950 1-digit categories
      occ_shares_25group.json    — 24 finer 25-group categories
      occ_shares_occ1950_list.json — 269-row full occ1950 crosswalk table
      occupation_list.json       — compact id→label lookup used by other scripts

    The three tables were computed by the authors (b/prep_occ_shares.do) from
    the full IPUMS census sample and the laureate microdata, and are included
    in data/ as collapsed summaries.

Upstream dependencies:
    data/occ_shares_10group_table.csv
    data/occ_shares_25group_table.csv
    data/occ_shares_occ1950_table.csv

Output:
    code/occ_shares/output/occ_shares_10group.json
    code/occ_shares/output/occ_shares_25group.json
    code/occ_shares/output/occ_shares_occ1950_list.json
    code/occ_shares/output/occupation_list.json

Run:
    python code/occ_shares/occ_shares.py
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"


def _clean(v) -> float | None:
    """Return float or None for NaN/inf values."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else round(f, 6)
    except (TypeError, ValueError):
        return None


def build_10group(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "occ1950_1": int(r["occ1950_1"]) if pd.notna(r["occ1950_1"]) else None,
            "label": str(r["occ1950_1_str"]).strip(),
            "occ_count": int(r["occ_count"]) if pd.notna(r["occ_count"]) else None,
            "laureate_n": int(r["laureate_n"]) if pd.notna(r["laureate_n"]) else None,
            "laureate_share": _clean(r["laureate_share"]),
            "laureate_pct": _clean(100.0 * float(r["laureate_share"])) if pd.notna(r["laureate_share"]) else None,
            "census_share": _clean(r["census_share"]),
            "census_pct": _clean(100.0 * float(r["census_share"])) if pd.notna(r["census_share"]) else None,
            "avg_educ_rank": _clean(r["avg_educ_rank"]),
            "avg_med_inctot_rank": _clean(r["avg_med_inctot_rank"]),
            "avg_global_med_inctot_rank": _clean(r["avg_global_med_inctot_rank"]),
            "overrep_ratio": _clean(r["overrep_ratio"]),
        })
    return rows


def build_25group(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "label": str(r["occgroup_25_name"]).strip(),
            "occ_count": int(r["occ_count"]) if pd.notna(r["occ_count"]) else None,
            "laureate_n": int(r["laureate_n"]) if pd.notna(r["laureate_n"]) else None,
            "laureate_share": _clean(r["laureate_share"]),
            "laureate_pct": _clean(100.0 * float(r["laureate_share"])) if pd.notna(r["laureate_share"]) else None,
            "census_share": _clean(r["census_share"]),
            "census_pct": _clean(100.0 * float(r["census_share"])) if pd.notna(r["census_share"]) else None,
            "avg_educ_rank": _clean(r["avg_educ_rank"]),
            "avg_med_inctot_rank": _clean(r["avg_med_inctot_rank"]),
            "avg_global_med_inctot_rank": _clean(r["avg_global_med_inctot_rank"]),
            "overrep_ratio": _clean(r["overrep_ratio"]),
        })
    return rows


def build_occ1950_list(df: pd.DataFrame) -> list[dict]:
    df_sorted = df.sort_values("occ1950")
    rows = []
    for _, r in df_sorted.iterrows():
        rows.append({
            "occ1950": int(r["occ1950"]) if pd.notna(r["occ1950"]) else None,
            "label": str(r["occ1950_label"]).strip(),
            "display": str(r["occ1950_display"]).strip(),
            "group_10": str(r["occ1950_1_str"]).strip() if pd.notna(r["occ1950_1_str"]) else None,
            "group_10_id": int(r["occ1950_1"]) if pd.notna(r["occ1950_1"]) else None,
            "group_25": str(r["occgroup_25_name"]).strip() if pd.notna(r["occgroup_25_name"]) else None,
            "group_6": str(r["occgroup_6_name"]).strip() if pd.notna(r["occgroup_6_name"]) else None,
            "educ_rank": _clean(r["educ_rank"]),
            "med_inctot_rank": _clean(r["med_inctot_rank"]),
            "global_med_inctot_rank": _clean(r["global_med_inctot_rank"]),
            "laureate_n": int(r["laureate_n"]) if pd.notna(r["laureate_n"]) else 0,
            "laureate_share": _clean(r["laureate_share"]),
            "laureate_pct": _clean(100.0 * float(r["laureate_share"])) if pd.notna(r["laureate_share"]) else None,
            "census_share": _clean(r["census_share"]),
            "census_pct": _clean(100.0 * float(r["census_share"])) if pd.notna(r["census_share"]) else None,
            "overrep_ratio": _clean(r["overrep_ratio"]),
        })
    return rows


def build_occupation_lookup(df: pd.DataFrame) -> dict:
    """Compact occ1950 → label dict for use as a reference by other modules."""
    lookup = {}
    for _, r in df.iterrows():
        code = int(r["occ1950"]) if pd.notna(r["occ1950"]) else None
        if code is not None:
            lookup[str(code)] = {
                "label": str(r["occ1950_label"]).strip(),
                "group_10": str(r["occ1950_1_str"]).strip() if pd.notna(r["occ1950_1_str"]) else None,
                "group_25": str(r["occgroup_25_name"]).strip() if pd.notna(r["occgroup_25_name"]) else None,
            }
    return lookup


def write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  Wrote {path.relative_to(PACKAGE_ROOT)}")


def main() -> None:
    required = [
        DATA_DIR / "occ_shares_10group_table.csv",
        DATA_DIR / "occ_shares_25group_table.csv",
        DATA_DIR / "occ_shares_occ1950_table.csv",
    ]
    for p in required:
        if not p.exists():
            raise SystemExit(f"Input not found: {p}")

    df10 = pd.read_csv(required[0])
    df25 = pd.read_csv(required[1])
    dfocc = pd.read_csv(required[2])

    print(f"10-group: {len(df10)} rows")
    print(f"25-group: {len(df25)} rows")
    print(f"occ1950 list: {len(dfocc)} rows")

    meta_base = {"generated": datetime.now(timezone.utc).isoformat(),
                 "source_dofiles": ["b/prep_occ_shares.do", "a/tables_occ_shares.do"]}

    rows10 = build_10group(df10)
    write_json(
        {"meta": {"script": "occ_shares", "table": "10group", "n": len(rows10), **meta_base},
         "data": rows10},
        OUT_DIR / "occ_shares_10group.json",
    )

    rows25 = build_25group(df25)
    write_json(
        {"meta": {"script": "occ_shares", "table": "25group", "n": len(rows25), **meta_base},
         "data": rows25},
        OUT_DIR / "occ_shares_25group.json",
    )

    rows_occ = build_occ1950_list(dfocc)
    write_json(
        {"meta": {"script": "occ_shares", "table": "occ1950_list", "n": len(rows_occ), **meta_base},
         "data": rows_occ},
        OUT_DIR / "occ_shares_occ1950_list.json",
    )

    lookup = build_occupation_lookup(dfocc)
    write_json(
        {"meta": {"script": "occ_shares", "table": "occupation_lookup",
                  "n": len(lookup), **meta_base},
         "data": lookup},
        OUT_DIR / "occupation_list.json",
    )

    # Print a quick sanity check
    print("\nTop 5 by overrep_ratio (10-group):")
    for r in sorted(rows10, key=lambda x: x["overrep_ratio"] or 0, reverse=True)[:5]:
        print(f"  {r['label']:<40} overrep={r['overrep_ratio']:.2f}  laureate%={r['laureate_pct']:.1f}")

    print("\nTop 5 by overrep_ratio (25-group):")
    for r in sorted(rows25, key=lambda x: x["overrep_ratio"] or 0, reverse=True)[:5]:
        print(f"  {r['label']:<40} overrep={r['overrep_ratio']:.2f}  laureate%={r['laureate_pct']:.1f}")


if __name__ == "__main__":
    main()
