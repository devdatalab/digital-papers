#!/usr/bin/env python3
"""Binscatter data for Figure 2: father rank by prize year and birth cohort.

Supplementary panels: A12. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Replicates a/graph_main_binscatter_ranks.do and
    a/graph_global_national_overlaid.do. Bins each father rank variable into
    fixed 5-year windows of prize year (and of birth cohort), plotting one point
    per window at the window midpoint. Fits a linear regression on the raw
    (unbinned) data and records predicted values at 1901 and 2023.
    Reproduces the paper's Figure 2 (by prize year) and Figure A2 (by birth
    cohort).

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/main_binscatter_ranks/output/binscatter_ranks.json

Run:
    python code/main_binscatter_ranks/main_binscatter_ranks.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"

RANKS = [
    ("med_inctot_rank", "Father's national income rank"),
    ("educ_rank", "Father's national education rank"),
    ("global_med_inctot_rank", "Father's global income rank"),
]
BIN_WIDTH_YEARS = 5  # fixed window width: one point every 5 years


def binscatter(y: pd.Series, x: pd.Series) -> tuple[list[dict], dict]:
    """Compute a fixed 5-year-window binscatter and linear fit.

    Bins x into fixed BIN_WIDTH_YEARS-wide windows (anchored to a multiple of
    the width) and plots one point per non-empty window at the window midpoint,
    with y = mean rank of observations in the window. The linear fit is still
    estimated on the raw, unbinned data (as in Stata's `binscatter ..., line(lfit)`).

    Returns:
        bins: list of {"x": window_midpoint, "y": bin_mean_y}
        lfit: {"coef": slope, "intercept": intercept, ...}
    """
    mask = y.notna() & x.notna()
    y_clean = y[mask]
    x_clean = x[mask]

    # Fixed-width windows anchored to a multiple of BIN_WIDTH_YEARS; each point
    # sits at the window midpoint (e.g. window [1900, 1905) -> x = 1902.5).
    anchor = np.floor(x_clean.min() / BIN_WIDTH_YEARS) * BIN_WIDTH_YEARS
    window_idx = np.floor((x_clean - anchor) / BIN_WIDTH_YEARS)
    midpoint = anchor + window_idx * BIN_WIDTH_YEARS + BIN_WIDTH_YEARS / 2

    bins = (
        pd.DataFrame({"y": y_clean, "x": midpoint})
        .groupby("x", observed=True)["y"]
        .mean()
        .reset_index()
        .sort_values("x")
        .round(4)[["x", "y"]]
        .to_dict("records")
    )

    # Linear fit on original (unbinned) data
    df_fit = pd.DataFrame({"y": y_clean, "x": x_clean})
    model = smf.ols("y ~ x", data=df_fit).fit()
    slope = float(model.params["x"])
    intercept = float(model.params["Intercept"])

    # Endpoint predictions (matching Stata's di _b["_cons"] + year * _b["prize_year"])
    x_min = float(x_clean.min())
    x_max = float(x_clean.max())
    pred_start = intercept + slope * x_min
    pred_end = intercept + slope * x_max

    lfit = {
        "coef": round(slope, 6),
        "intercept": round(intercept, 4),
        "pred_start": {"x": round(x_min, 0), "y": round(pred_start, 2)},
        "pred_end": {"x": round(x_max, 0), "y": round(pred_end, 2)},
        "r2": round(float(model.rsquared), 4),
    }
    return bins, lfit


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = pd.read_csv(dta)
    n = len(df)
    print(f"N = {n}")

    data = {}
    for col, label in RANKS:
        if col not in df.columns:
            raise SystemExit(f"Column '{col}' not found in dataset.")

        bins_year, lfit_year = binscatter(df[col], df["prize_year"])
        bins_cohort, lfit_cohort = binscatter(df[col], df["cohort"])

        # Stata reports predicted values at 1901 and 2023 specifically
        m_year = smf.ols(f"{col} ~ prize_year", data=df.dropna(subset=[col, "prize_year"])).fit()
        pred_1901 = float(m_year.params["Intercept"] + m_year.params["prize_year"] * 1901)
        pred_2023 = float(m_year.params["Intercept"] + m_year.params["prize_year"] * 2023)

        lfit_year["pred_1901"] = round(pred_1901, 2)
        lfit_year["pred_2023"] = round(pred_2023, 2)
        lfit_year["diff_1901_2023"] = round(pred_1901 - pred_2023, 2)

        data[col] = {
            "label": label,
            "by_prize_year": {"bins": bins_year, "lfit": lfit_year},
            "by_cohort": {"bins": bins_cohort, "lfit": lfit_cohort},
        }

    payload = {
        "meta": {
            "script": "main_binscatter_ranks",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": n,
            "bin_width_years": BIN_WIDTH_YEARS,
            "source_dofile": "a/graph_main_binscatter_ranks.do",
        },
        "data": data,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "binscatter_ranks.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
