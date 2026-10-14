#!/usr/bin/env python3
"""OLS regression results for Table 1: main specification.

Supplementary panels: A15. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Replicates a/table_main_spec.do. Regresses each father rank variable (and
    bottom-80/90 indicators) on prize_year_rescaled using OLS with HC1 robust
    SEs. Stores the coefficient, SE, N, and intercept for each specification.
    Reproduces the paper's Table 1 (and Table A7).

    Uses the paper's low80/low90 indicator columns directly. These preserve
    missing ranks as missing outcomes. The older bottom_{p}pct_* columns
    incorrectly encode missing ranks as zero and must not be used here.

    prize_year_rescaled = prize_year - 1901 (0–122; range 0 at 1901, 122 at 2023).
    Coefficient interpretation: change in rank per year since 1901.

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/main_spec/output/main_spec.json

Run:
    python code/main_spec/main_spec.py
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

# Maps (output_key, dataset_column, label)
# global_med_inctot_pregdp_rank is included only if present in the dataset.
SPECS = [
    ("med_inctot_rank", "med_inctot_rank", "Father's national income rank"),
    ("educ_rank", "educ_rank", "Father's national education rank"),
    ("global_med_inctot_rank", "global_med_inctot_rank", "Father's global income rank"),
    ("global_med_inctot_pregdp_rank", "global_med_inctot_pregdp_rank", "Father's global income rank (pre-GDP)"),
    ("low90_inc", "low90_winner_inc", "Share from bottom 90% (national income)"),
    ("low90_educ", "low90_winner_educ", "Share from bottom 90% (education)"),
    ("low90_glo", "low90_glo", "Share from bottom 90% (global income)"),
    ("low80_inc", "low80_winner_inc", "Share from bottom 80% (national income)"),
    ("low80_educ", "low80_winner_educ", "Share from bottom 80% (education)"),
    ("low80_glo", "low80_glo", "Share from bottom 80% (global income)"),
]


def run_spec(df: pd.DataFrame, col: str) -> dict:
    """OLS of col ~ prize_year_rescaled with HC1 SEs."""
    sub = df[["prize_year_rescaled", col]].dropna()
    model = smf.ols(f"Q('{col}') ~ prize_year_rescaled", data=sub).fit(cov_type="HC1")
    return {
        "coef": round(float(model.params["prize_year_rescaled"]), 6),
        "se": round(float(model.bse["prize_year_rescaled"]), 6),
        "intercept": round(float(model.params["Intercept"]), 4),
        # Appendix Table A7 prints the constant with its SE ("96.047*** (0.715)").
        # Table 1 doesn't show the constant at all, so this is unused there.
        "intercept_se": round(float(model.bse["Intercept"]), 4),
        "n": int(model.nobs),
        "sample_mean": float(sub[col].mean()),
        "r2": round(float(model.rsquared), 4),
    }


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = pd.read_csv(dta)
    print(f"N = {len(df)}")

    data = {}
    for key, col, label in SPECS:
        if col not in df.columns:
            print(f"  Skipping '{col}' — not in dataset.")
            continue
        result = run_spec(df, col)
        data[key] = {"label": label, "column": col, **result}
        print(
            f"  {col}: coef={result['coef']:.4f} (se={result['se']:.4f}), "
            f"intercept={result['intercept']:.2f}, n={result['n']}"
        )

    payload = {
        "meta": {
            "script": "main_spec",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": int(df.shape[0]),
            "rhs_variable": "prize_year_rescaled",
            "rhs_note": "prize_year - 1901; coefficient = change per year since 1901",
            "se_type": "HC1",
            "source_dofile": "a/table_main_spec.do",
        },
        "data": data,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "main_spec.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
