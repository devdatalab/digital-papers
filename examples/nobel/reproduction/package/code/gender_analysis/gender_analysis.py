#!/usr/bin/env python3
"""Father-rank trends, slope-equality tests, and distribution tests by gender.

Supplementary panels: A6. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Reproduces the supplementary gender comparison: separate male/female
    rank trends, robust Wald tests of equal slopes, and Wilcoxon rank-sum tests.
    Retains the relevant calculations
    from a/table_gender_spec.do and a/stat_test_gender_distributions.do.

All regressions use HC1 (robust) SEs, matching `reg y x, r` in Stata.

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/gender_analysis/output/gender_analysis.json

Run:
    python code/gender_analysis/gender_analysis.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import scipy.stats as stats
import statsmodels.formula.api as smf

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"

RANK_VARS = ["med_inctot_rank", "educ_rank", "global_med_inctot_rank"]
RANK_BASES = ["med_inctot", "educ", "global_med_inctot"]
FEMALE_CODES = {"male": 0, "female": 1}


def coerce_female(df: pd.DataFrame) -> None:
    """Normalize legacy numeric gender codes and current string labels in-place."""
    raw = df["female"]
    numeric = pd.to_numeric(raw, errors="coerce")
    label_codes = raw.astype("string").str.strip().str.lower().map(FEMALE_CODES)
    coded = numeric.where(numeric.notna(), label_codes)
    unknown = raw.notna() & coded.isna()
    if unknown.any():
        values = sorted(raw[unknown].astype(str).unique())
        raise ValueError(f"Unknown female labels: {values}")
    df["female"] = coded.astype(float)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "nobelists_analysis.csv")
    coerce_female(df)
    df["prize_year_rescaled"] = df["prize_year"] - 1901
    return df


def reg_result(model) -> dict:
    params = model.params
    bse = model.bse
    result = {}
    for k in params.index:
        result[k] = {"coef": round(float(params[k]), 6), "se": round(float(bse[k]), 6)}
    result["n"] = int(model.nobs)
    result["r2"] = round(float(model.rsquared), 6)
    return result


# ── 1. Gender-stratified rank trend ────────────────────────────────────────────

def gender_spec(df: pd.DataFrame) -> dict:
    """rank ~ prize_year_rescaled, separately for male (female==0) and female (female==1)."""
    results = {}
    for rank in RANK_VARS:
        results[rank] = {}
        for g, label in [(0, "male"), (1, "female")]:
            sub = df[df["female"] == g][["prize_year_rescaled", rank]].dropna()
            model = smf.ols(f"Q('{rank}') ~ prize_year_rescaled", data=sub).fit(cov_type="HC1")
            results[rank][label] = reg_result(model)
            print(f"  gender_spec {rank} {label}: coef={model.params['prize_year_rescaled']:.4f} "
                  f"se={model.bse['prize_year_rescaled']:.4f} n={int(model.nobs)}")
    return results


def slope_tests(df: pd.DataFrame) -> dict:
    """Test equal gender slopes with an HC1-robust interaction-model Wald F-test."""
    results = {}
    for rank in RANK_VARS:
        sub = df[[rank, "prize_year_rescaled", "female"]].dropna()
        model = smf.ols(
            f"Q('{rank}') ~ prize_year_rescaled * female", data=sub
        ).fit(cov_type="HC1")
        test = model.f_test("prize_year_rescaled:female = 0")
        results[rank] = {
            "p_equal_slopes": round(float(test.pvalue), 6),
            "difference_female_minus_male": reg_result(model)["prize_year_rescaled:female"],
            "n": int(model.nobs),
        }
        print(f"  slope_tests {rank}: p_equal_slopes={float(test.pvalue):.4f}")
    return results


# ── 2. Wilcoxon distribution tests ─────────────────────────────────────────────

def dist_tests(df: pd.DataFrame) -> dict:
    """Wilcoxon rank-sum (mannwhitneyu) by female for 3 rank vars."""
    results = {}
    for base in RANK_BASES:
        col = f"{base}_rank"
        sub = df[[col, "female"]].dropna()
        male = sub[sub["female"] == 0][col].values
        female = sub[sub["female"] == 1][col].values

        # Wilcoxon rank-sum (Mann–Whitney U, two-sided)
        _, p_wilcoxon = stats.mannwhitneyu(male, female, alternative="two-sided")

        results[base] = {
            "n_male": int(len(male)),
            "n_female": int(len(female)),
            "p_wilcoxon": round(float(p_wilcoxon), 6),
            "mean_male": round(float(male.mean()), 4),
            "mean_female": round(float(female.mean()), 4),
        }
        print(f"  dist_tests {base}: p_W={p_wilcoxon:.4f} "
              f"n_male={len(male)} n_female={len(female)}")
    return results


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = load_data()
    print(f"N total = {len(df)}, N female = {int(df['female'].sum())}")

    print("\n[1/3] Gender-stratified trend regressions")
    g_spec = gender_spec(df)

    print("\n[2/3] Gender slope-equality tests (robust Wald F)")
    s_tests = slope_tests(df)

    print("\n[3/3] Distribution tests (Wilcoxon)")
    d_tests = dist_tests(df)

    payload = {
        "meta": {
            "script": "gender_analysis",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_total": int(len(df)),
            "n_female": int(df["female"].sum()),
            "source_dofiles": [
                "a/table_gender_spec.do",
                "a/stat_test_gender_distributions.do",
            ],
        },
        "data": {
            "gender_spec": g_spec,
            "slope_tests": s_tests,
            "dist_tests": d_tests,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "gender_analysis.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
