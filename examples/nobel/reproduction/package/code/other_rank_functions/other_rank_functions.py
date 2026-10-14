#!/usr/bin/env python3
"""Alternative rank representations: below-threshold proportions and median trends (Appendix robustness).

Supplementary panels: A13. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Replicates a/graph_other_rank_functions.do. Produces two complementary
    views of the parental-rank data:

    1. below_threshold: For thresholds p in {80, 90} and each of 3 rank families
       (national income, education, global income), a binscatter of
       low{p} indicators vs prize_year AND an OLS regression on
       prize_year_rescaled with a projected value at prize_year=2023
       (prize_year_rescaled=122).

    2. median_by_bin: The median parental rank within each of 20 equal-count
       prize-year bins, for each of 3 rank variables. Matches the scatter +
       lfit graph of median ranks over time.

    Uses the paper's low80/low90 indicator columns directly. These preserve
    missing ranks as missing outcomes. The older bottom_{p}pct_* columns
    incorrectly encode missing ranks as zero and must not be used here.

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/other_rank_functions/output/other_rank_functions.json

Run:
    python code/other_rank_functions/other_rank_functions.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"

N_BINS = 20
# prize_year_rescaled value for 2023 = 2023 - 1901 = 122
RESCALED_2023 = 122

THRESHOLD_VARS = {
    80: {
        "med_inctot":        "low80_winner_inc",
        "educ":              "low80_winner_educ",
        "global_med_inctot": "low80_glo",
    },
    90: {
        "med_inctot":        "low90_winner_inc",
        "educ":              "low90_winner_educ",
        "global_med_inctot": "low90_glo",
    },
}

RANK_VARS = ["med_inctot_rank", "educ_rank", "global_med_inctot_rank"]


def binscatter(y: pd.Series, x: pd.Series) -> list[dict]:
    mask = y.notna() & x.notna()
    y_c, x_c = y[mask], x[mask]
    if len(x_c) < N_BINS:
        return []
    x_bin = pd.qcut(x_c, q=N_BINS, labels=False, duplicates="drop")
    bins = (
        pd.DataFrame({"y": y_c.values, "x": x_c.values, "bin": x_bin.values})
        .groupby("bin")[["x", "y"]]
        .mean()
        .reset_index(drop=True)
    )
    return [{"x": round(float(r.x), 2), "y": round(float(r.y), 6)} for _, r in bins.iterrows()]


def below_threshold_analysis(df: pd.DataFrame) -> dict:
    results: dict = {}
    for p, var_map in THRESHOLD_VARS.items():
        results[f"p{p}"] = {}
        for base, col in var_map.items():
            sub = df[[col, "prize_year", "prize_year_rescaled"]].dropna()
            pts = binscatter(sub[col], sub["prize_year"])

            model = smf.ols(f"Q('{col}') ~ prize_year_rescaled", data=sub).fit(cov_type="HC1")
            coef = float(model.params["prize_year_rescaled"])
            intercept = float(model.params["Intercept"])
            projected_2023 = intercept + coef * RESCALED_2023

            results[f"p{p}"][base] = {
                "column": col,
                "binscatter": pts,
                "regression": {
                    "coef": round(coef, 6),
                    "se": round(float(model.bse["prize_year_rescaled"]), 6),
                    "intercept": round(intercept, 6),
                    "projected_2023": round(projected_2023, 6),
                    "n": int(model.nobs),
                    "r2": round(float(model.rsquared), 6),
                },
            }
            print(f"  below_threshold p{p} {base}: coef={coef:.4f} projected_2023={projected_2023:.4f} n={int(model.nobs)}")
    return results


def median_by_bin(df: pd.DataFrame) -> dict:
    """Median parental rank within 20 equal-count prize-year bins."""
    sub = df[["prize_year"] + RANK_VARS].copy()
    # Create 20 equal-count bins on prize_year
    sub["prize_year_bin"] = pd.qcut(sub["prize_year"], q=N_BINS, labels=False, duplicates="drop")

    results: dict = {}
    for rank in RANK_VARS:
        grouped = (
            sub.dropna(subset=[rank, "prize_year_bin"])
            .groupby("prize_year_bin")
            .agg(median_rank=(rank, "median"), prize_year=("prize_year", "mean"))
            .reset_index(drop=True)
        )
        pts = [
            {"x": round(float(r.prize_year), 2), "y": round(float(r.median_rank), 4)}
            for _, r in grouped.iterrows()
        ]
        results[rank] = pts
        print(f"  median_by_bin {rank}: {len(pts)} bins")
    return results


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = pd.read_csv(dta)
    df["prize_year_rescaled"] = df["prize_year_rescaled"].astype(float)
    print(f"N total = {len(df)}")

    print("\n[1/2] Below-threshold proportions (binscatter + regression)")
    bt = below_threshold_analysis(df)

    print("\n[2/2] Median rank by prize-year bin")
    mb = median_by_bin(df)

    payload = {
        "meta": {
            "script": "other_rank_functions",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": int(len(df)),
            "source_dofile": "a/graph_other_rank_functions.do",
            "note": (
                "below_threshold uses low{p} columns (= 1 if father rank < p; missing if rank is unknown). "
                "median_by_bin collapses to median within 20 equal-count prize-year bins."
            ),
        },
        "data": {
            "below_threshold": bt,
            "median_by_bin": mb,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "other_rank_functions.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
