#!/usr/bin/env python3
"""Top-10 father occupations by frequency and over-representation ratio (Figure A1).

Supplementary panels: A5. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Recreates the occupation comparison in a/graph_most_common_occupations.do
    and a/graph_common_occup_ratio.do, correcting their census denominator to
    aggregate every detailed occupation code within the displayed group.
    Produces two views of the same data:
      - top10: the 10 most common father occupations sorted by laureate share, each
        with its population census share and an over-representation ratio (laureate
        share / census share).
      - stacked: the same 10 occupations plus an "Other" remainder category, formatted
        for a stacked-bar comparison between the laureate sample and census population.

    microocc_str labels from the dataset are overridden to match the manuscript's
    display labels (same substitutions as the Stata dofile).

Upstream dependencies:
    data/nobelists_analysis.csv
    data/microocc_census_shares.csv

Output:
    code/most_common_occupations/output/most_common_occupations.json

Run:
    python code/most_common_occupations/most_common_occupations.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"

# The dataset's `microocc` column was reclassified upstream from fine numeric
# codes into broad string groups identical to `microocc_str` (e.g. "Managers",
# "Engineers"), so the old numeric code overrides no longer apply. We now label
# each group by its string name, applying the manuscript's display labels.
LABEL_OVERRIDES: dict[str, str] = {
    "Officials, government and non-profit organizations": "Government officials",
    "Managers": "Business owners",
    "Jurists": "Lawyers and judges",
    "Health professionals": "Physicians and doctors",
    "Elementary and secondary school teachers": "K-12 school teachers",
}


def label_for(row: pd.Series) -> str:
    label = str(row["microocc_str"]).strip()
    return LABEL_OVERRIDES.get(label, label)


def build_top10(df: pd.DataFrame, census: pd.DataFrame) -> tuple[list[dict], int]:
    """Compare the same microocc groups in the laureate and full census samples."""
    df = df[df["microocc"].notna()].copy()
    total = len(df)

    # Count per microocc group
    counts = df.groupby("microocc").size().rename("count")
    df = df.merge(counts, on="microocc")

    collapsed = (
        df.groupby("microocc")
        .agg(
            count=("count", "first"),
            occ1950=("occ1950", "first"),
            microocc_str=("microocc_str", "first"),
            occ1950_label=("occ1950_label", "first"),
        )
        .reset_index()
    )

    # Use all detailed occupation codes in each U.S. group, including codes
    # with no laureate fathers, and weight each 1850–1970 decade equally.
    expected_years = list(range(1850, 1980, 10))
    if census.duplicated(['microocc', 'ipums_decade']).any():
        raise ValueError('Duplicate census group-decade keys.')
    if not census.groupby('microocc')['ipums_decade'].apply(
        lambda years: sorted(years.tolist()) == expected_years
    ).all():
        raise ValueError('Census groups must cover every decade from 1850 to 1970.')
    if census['census_share'].isna().any() or not census['census_share'].between(0, 1).all():
        raise ValueError('Invalid census group shares.')
    if not census.groupby('ipums_decade')['census_share'].sum().between(1 - 1e-8, 1 + 1e-8).all():
        raise ValueError('Census group shares must sum to one within each decade.')
    shares = census.groupby('microocc')['census_share'].mean().rename('occ_pop_share')
    collapsed = collapsed.merge(shares, on='microocc', how='left', validate='one_to_one')
    if collapsed['occ_pop_share'].isna().any():
        raise ValueError('A laureate occupation group is absent from the census crosswalk.')

    collapsed["nobelists_prop"] = collapsed["count"] / total
    collapsed = collapsed.sort_values(
        ['nobelists_prop', 'microocc'], ascending=[False, True]
    ).head(10).copy()
    if (collapsed['occ_pop_share'] <= 0).any():
        raise ValueError('A top-ten occupation has no census population.')
    collapsed["occ_share_ratio"] = collapsed["nobelists_prop"] / collapsed["occ_pop_share"]
    collapsed["label"] = collapsed.apply(label_for, axis=1)

    rows = []
    for _, r in collapsed.iterrows():
        rows.append(
            {
                "rank": int(_) + 1,  # position in the sorted list (set below)
                # `microocc` is now the broad string group key (== microocc_str),
                # not the former numeric code.
                "microocc": str(r["microocc"]).strip(),
                "occ1950": int(r["occ1950"]) if pd.notna(r["occ1950"]) else None,
                "label": r["label"],
                "occ1950_label": str(r["occ1950_label"]).strip(),
                "count": int(r["count"]),
                "nobelists_pct": round(100.0 * r["nobelists_prop"], 4),
                "census_pct": round(100.0 * r["occ_pop_share"], 4),
                "occ_share_ratio": round(r["occ_share_ratio"], 4),
            }
        )

    # Fix the rank field: it's the sort order (1 = most common)
    for i, row in enumerate(rows):
        row["rank"] = i + 1

    return rows, total


def build_stacked(top10_rows: list[dict]) -> dict:
    """Add an 'Other' category row (1 - sum of top-10 shares) for the stacked-bar chart."""
    laureate_sum = sum(r["nobelists_pct"] for r in top10_rows)
    census_sum = sum(r["census_pct"] for r in top10_rows)

    other = {
        "rank": 11,
        "microocc": "Other",
        "occ1950": None,
        "label": "Other",
        "occ1950_label": "Other",
        "count": None,
        "nobelists_pct": round(100.0 - laureate_sum, 4),
        "census_pct": round(100.0 - census_sum, 4),
        "occ_share_ratio": None,
    }

    return {"rows": top10_rows + [other]}


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = pd.read_csv(dta)
    print(f"N total = {len(df)}")

    census = pd.read_csv(DATA_DIR / 'microocc_census_shares.csv')
    top10_rows, n_valid = build_top10(df, census)
    print(f"N with non-missing microocc = {n_valid}")
    print()
    print(f"{'Label':<35} {'Laureate%':>10} {'Census%':>10} {'Ratio':>8}")
    for r in top10_rows:
        print(f"  {r['label']:<33} {r['nobelists_pct']:>10.2f} {r['census_pct']:>10.4f} {r['occ_share_ratio']:>8.1f}")

    stacked = build_stacked(top10_rows)

    payload = {
        "meta": {
            "script": "most_common_occupations",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": n_valid,
            "source_dofiles": [
                "a/graph_most_common_occupations.do",
                "a/graph_common_occup_ratio.do",
            ],
            "note": (
                "top10 sorted by laureate share descending. "
                "Census shares sum all OCC1950 codes in each microocc group within "
                "each U.S. decade, normalize the complete census distribution, "
                "and average equally across 1850–1970. Ratios compare identical "
                "occupation groups. stacked adds an Other row = 1 - sum(top10)."
            ),
        },
        "data": {
            "top10": top10_rows,
            "stacked": stacked,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "most_common_occupations.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
