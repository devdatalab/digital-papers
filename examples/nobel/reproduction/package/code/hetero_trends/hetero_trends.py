#!/usr/bin/env python3
"""Heterogeneity in time trends by gender, prize category, and region (Appendix Table 15).

Supplementary panels: A8. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Replicates a/table_hetero_trends.do. For each of 9 outcome variables (3 rank
    variables + 3 top-decile indicators × 100 + 3 top-20pct indicators × 100),
    estimates four slope-interaction models:
      1. full_sample:  yvar ~ prize_year_rescaled, HC1
      2. gender:       yvar ~ female + male_year + female_year, HC1
                       + Wald test: male_year == female_year
      3. category:     yvar ~ cat_*_year + C(prize_category), HC1
                       + Wald test: all 4 slopes equal
      4. region:       yvar ~ reg_*_year + C(region), HC1
                       + Wald test: all 5 slopes equal

    The top_decile_* and top_20pct_* indicators are multiplied by 100 before
    regression (matching Stata's pct_ transform) so slopes are in percentage points.

    Region is the 5-way heterogeneity_spec categorization:
        1=USA, 2=Western Europe, 3=Eastern Europe, 4=Global South, 5=All others

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/hetero_trends/output/hetero_trends.json

Run:
    python code/hetero_trends/hetero_trends.py
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

# (key, actual regression yvar)
OUTCOMES = [
    ("med_inctot_rank",             "med_inctot_rank"),
    ("educ_rank",                   "educ_rank"),
    ("global_med_inctot_rank",      "global_med_inctot_rank"),
    ("top_decile_med_inctot",       "pct_top_decile_med_inctot"),
    ("top_decile_educ",             "pct_top_decile_educ"),
    ("top_decile_global_med_inctot","pct_top_decile_global_med_inctot"),
    ("top_20pct_med_inctot",        "pct_top_20pct_med_inctot"),
    ("top_20pct_educ",              "pct_top_20pct_educ"),
    ("top_20pct_global_med_inctot", "pct_top_20pct_global_med_inctot"),
]

EASTERN_EUROPE = {"Czechoslovakia", "Poland", "Hungary", "Romania", "Lithuania"}
CAT_NAMES = {1: "chemistry", 2: "economics", 3: "medicine", 4: "physics"}
REGION_NAMES = {1: "usa", 2: "western_europe", 3: "eastern_europe", 4: "global_south", 5: "other"}
FEMALE_CODES = {"male": 0, "female": 1}
BLOC_CODES = {"west": 0, "east": 1, "south": 2}
PRIZE_CATEGORY_CODES = {"chemistry": 1, "economics": 2, "medicine": 3, "physics": 4}


def coerce_coded_column(df: pd.DataFrame, column: str, labels: dict[str, int]) -> None:
    """Normalize legacy numeric codes and current string labels in-place."""
    raw = df[column]
    numeric = pd.to_numeric(raw, errors="coerce")
    label_codes = raw.astype("string").str.strip().str.lower().map(labels)
    coded = numeric.where(numeric.notna(), label_codes)
    unknown = raw.notna() & coded.isna()
    if unknown.any():
        values = sorted(raw[unknown].astype(str).unique())
        raise ValueError(f"Unknown {column} labels: {values}")
    df[column] = coded.astype(float)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "nobelists_analysis.csv")
    df["prize_year_rescaled"] = df["prize_year_rescaled"].astype(float)
    coerce_coded_column(df, "female", FEMALE_CODES)
    coerce_coded_column(df, "bloc", BLOC_CODES)
    coerce_coded_column(df, "prize_category", PRIZE_CATEGORY_CODES)

    # top_20pct indicators (not in dataset, derived)
    for base in ["med_inctot", "educ", "global_med_inctot"]:
        col = f"{base}_rank"
        df[f"top_20pct_{base}"] = np.where(df[col].notna(), (df[col] >= 80).astype(float), np.nan)

    # pct_ versions (×100) for binary outcomes
    for prefix in ["top_decile", "top_20pct"]:
        for base in ["med_inctot", "educ", "global_med_inctot"]:
            src = f"{prefix}_{base}"
            df[f"pct_{src}"] = df[src] * 100.0

    # male indicator
    df["male"] = (1.0 - df["female"]).astype(float)

    # 5-way region (matches heterogeneity_spec.py)
    region = pd.Series(np.nan, index=df.index)
    region[df["country_name"] == "USA"] = 1
    mask = region.isna()
    region[mask & ((df["europe"] == 1) | df["country_name"].isin(["Finland"]))] = 2

    # Eastern Europe takes precedence over the broad European assignment.
    region[(df["bloc"] == 1) | df["country_name"].isin(EASTERN_EUROPE)] = 3
    mask = region.isna()
    region[mask & ((df["bloc"] == 2) | df["country_name"].isin(["China"]))] = 4
    region[region.isna()] = 5
    df["region"] = region.astype(float)

    # pre-compute all slope-interaction terms
    pyr = df["prize_year_rescaled"]
    df["male_year"]   = df["male"] * pyr
    df["female_year"] = df["female"] * pyr

    for code, name in CAT_NAMES.items():
        df[f"cat_{name}_year"] = ((df["prize_category"] == code).astype(float)) * pyr

    for code, name in REGION_NAMES.items():
        df[f"reg_{name}_year"] = (df["region"] == code).astype(float) * pyr

    return df


def reg_coef(model, name: str) -> dict:
    if name not in model.params:
        return {"coef": None, "se": None}
    return {
        "coef": round(float(model.params[name]), 6),
        "se": round(float(model.bse[name]), 6),
    }


def wald_p(model, constraints: str) -> float:
    try:
        return round(float(model.f_test(constraints).pvalue), 6)
    except Exception:
        return float("nan")


def run_outcome(df: pd.DataFrame, key: str, yvar: str) -> dict:
    sub_base = df[[yvar, "prize_year_rescaled",
                   "male", "female", "male_year", "female_year",
                   "prize_category",
                   "cat_chemistry_year", "cat_economics_year",
                   "cat_medicine_year", "cat_physics_year",
                   "region",
                   "reg_usa_year", "reg_western_europe_year", "reg_eastern_europe_year",
                   "reg_global_south_year", "reg_other_year"]].dropna(subset=[yvar])

    results: dict = {}

    # 1. Full sample
    s = sub_base.dropna(subset=["prize_year_rescaled"])
    m = smf.ols(f"Q('{yvar}') ~ prize_year_rescaled", data=s).fit(cov_type="HC1")
    results["full_sample"] = {
        **reg_coef(m, "prize_year_rescaled"),
        "n": int(m.nobs),
    }

    # 2. Gender heterogeneity
    s = sub_base.dropna(subset=["male_year", "female_year", "female"])
    m = smf.ols(f"Q('{yvar}') ~ female + male_year + female_year", data=s).fit(cov_type="HC1")
    results["gender"] = {
        "male":   reg_coef(m, "male_year"),
        "female": reg_coef(m, "female_year"),
        "p_equal": wald_p(m, "male_year = female_year"),
        "n": int(m.nobs),
    }

    # 3. Category heterogeneity
    cat_cols = ["cat_chemistry_year", "cat_economics_year", "cat_medicine_year", "cat_physics_year", "prize_category"]
    s = sub_base.dropna(subset=cat_cols)
    m = smf.ols(
        f"Q('{yvar}') ~ cat_chemistry_year + cat_economics_year + cat_medicine_year + cat_physics_year + C(prize_category)",
        data=s,
    ).fit(cov_type="HC1")
    results["category"] = {
        "chemistry": reg_coef(m, "cat_chemistry_year"),
        "economics": reg_coef(m, "cat_economics_year"),
        "medicine":  reg_coef(m, "cat_medicine_year"),
        "physics":   reg_coef(m, "cat_physics_year"),
        "p_equal": wald_p(
            m,
            "cat_chemistry_year = cat_economics_year, "
            "cat_economics_year = cat_medicine_year, "
            "cat_medicine_year = cat_physics_year",
        ),
        "n": int(m.nobs),
    }

    # 4. Region heterogeneity
    reg_cols = [
        "reg_usa_year", "reg_western_europe_year", "reg_eastern_europe_year",
        "reg_global_south_year", "reg_other_year", "region",
    ]
    s = sub_base.dropna(subset=reg_cols)
    m = smf.ols(
        f"Q('{yvar}') ~ reg_usa_year + reg_western_europe_year + reg_eastern_europe_year"
        f" + reg_global_south_year + reg_other_year + C(region)",
        data=s,
    ).fit(cov_type="HC1")
    results["region"] = {
        "usa":            reg_coef(m, "reg_usa_year"),
        "western_europe": reg_coef(m, "reg_western_europe_year"),
        "eastern_europe": reg_coef(m, "reg_eastern_europe_year"),
        "global_south":   reg_coef(m, "reg_global_south_year"),
        "other":          reg_coef(m, "reg_other_year"),
        "p_equal": wald_p(
            m,
            "reg_usa_year = reg_western_europe_year, "
            "reg_western_europe_year = reg_eastern_europe_year, "
            "reg_eastern_europe_year = reg_global_south_year, "
            "reg_global_south_year = reg_other_year",
        ),
        "n": int(m.nobs),
    }

    return results


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = load_data()
    print(f"N total = {len(df)}")

    data: dict = {}
    for key, yvar in OUTCOMES:
        print(f"\n  [{key}]")
        data[key] = run_outcome(df, key, yvar)
        fs = data[key]["full_sample"]
        g = data[key]["gender"]
        print(f"    full: coef={fs['coef']:.4f} se={fs['se']:.4f} n={fs['n']}")
        print(f"    gender: male={g['male']['coef']:.4f} female={g['female']['coef']:.4f} p_equal={g['p_equal']:.3f}")

    payload = {
        "meta": {
            "script": "hetero_trends",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_total": int(len(df)),
            "source_dofile": "a/table_hetero_trends.do",
            "outcome_keys": [k for k, _ in OUTCOMES],
            "note": (
                "top_decile_* and top_20pct_* outcomes multiplied by 100 before "
                "regression so slopes are in percentage points (matching Stata pct_ transform)."
            ),
        },
        "data": data,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "hetero_trends.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
