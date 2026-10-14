#!/usr/bin/env python3
"""Group means and equality tests for Table 2: heterogeneity specification.

Why this file exists:
    Replicates a/table_heterogeneity_spec.do. For each rank variable, computes
    the full-sample mean and group means by gender, Cold War bloc, 5-way region,
    and prize category. Runs F-tests (Wald tests) for equality across groups
    using HC1 robust SEs. Reproduces the paper's Table 2.

Constructed variables (matching Stata):
    top_20pct_<rank>  — 1 if rank ∈ [80, 100], else 0 (missing if rank missing)
    region            — 1=USA, 2=Western Europe, 3=Eastern Europe,
                        4=Global South, 5=All others
    male              — 1 - female

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/heterogeneity_spec/output/heterogeneity_spec.json

Run:
    python code/heterogeneity_spec/heterogeneity_spec.py
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

# Rank variables — the three base ranks plus top-decile and top-20% indicators
BASE_RANKS = ["med_inctot_rank", "educ_rank", "global_med_inctot_rank"]
TOP_DECILE_VARS = ["top_decile_med_inctot", "top_decile_educ", "top_decile_global_med_inctot"]

REGION_LABELS = {1: "USA", 2: "Western Europe", 3: "Eastern Europe", 4: "Global South", 5: "All others"}
BLOC_LABELS = {0: "Western/NATO", 1: "Soviet/Eastern", 2: "Non-aligned"}
PRIZE_CAT_LABELS = {1: "Chemistry", 2: "Economics", 3: "Medicine", 4: "Physics"}
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


def add_constructed_vars(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    coerce_coded_column(df, "female", FEMALE_CODES)
    coerce_coded_column(df, "bloc", BLOC_CODES)
    coerce_coded_column(df, "prize_category", PRIZE_CATEGORY_CODES)

    # top_20pct indicators: inrange(rank, 80, 100) if !mi(rank)
    for base in ["med_inctot", "educ", "global_med_inctot"]:
        col = f"{base}_rank"
        new = f"top_20pct_{base}"
        if col in df.columns:
            df[new] = np.where(df[col].notna(), (df[col] >= 80).astype(float), np.nan)

    # 5-way region variable (sequential assignment matching Stata logic)
    region = pd.Series(np.nan, index=df.index)
    region[df["country_name"] == "USA"] = 1
    mask = region.isna()
    region[mask & ((df["europe"] == 1) | df["country_name"].isin(["Finland"]))] = 2
    eastern_europe = ["Czechoslovakia", "Poland", "Hungary", "Romania", "Lithuania"]

    # Eastern Europe takes precedence over the broad European assignment.
    region[(df["bloc"] == 1) | df["country_name"].isin(eastern_europe)] = 3
    mask = region.isna()
    region[mask & ((df["bloc"] == 2) | df["country_name"].isin(["China"]))] = 4
    region[region.isna()] = 5
    df["region"] = region.astype(int)

    df["male"] = (1 - df["female"]).astype(float)

    return df


def group_means(df: pd.DataFrame, col: str, group_col: str) -> list[dict]:
    """Group means with HC1 SEs (= sample SE of the mean within each group)."""
    results = []
    for g, sub in df.groupby(group_col, observed=True):
        vals = sub[col].dropna()
        n = len(vals)
        if n == 0:
            continue
        mean = float(vals.mean())
        se = float(vals.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan
        results.append({"group": int(g) if not isinstance(g, str) else g, "mean": round(mean, 4), "se": round(se, 4), "n": n})
    return results


def wald_p(df: pd.DataFrame, col: str, group_col: str) -> float:
    """F-test p-value for equality of group means (HC1 robust, no constant)."""
    sub = df[[col, group_col]].dropna()
    try:
        model = smf.ols(f"Q('{col}') ~ C({group_col}) - 1", data=sub).fit(cov_type="HC1")
        cats = sorted(sub[group_col].unique())
        if len(cats) < 2:
            return np.nan
        hypotheses = " = ".join([f"C({group_col})[{c}]" for c in cats])
        ftest = model.f_test(hypotheses)
        return float(ftest.pvalue)
    except Exception:
        return np.nan


def full_mean(df: pd.DataFrame, col: str) -> dict:
    """Full-sample mean with HC1 SE (intercept-only OLS)."""
    vals = df[col].dropna()
    n = len(vals)
    if n == 0:
        return {"mean": np.nan, "se": np.nan, "n": 0}
    mean = float(vals.mean())
    se = float(vals.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan
    return {"mean": round(mean, 4), "se": round(se, 4), "n": n}


def spec_for_rank(df: pd.DataFrame, col: str) -> dict:
    result = {"full_sample": full_mean(df, col)}

    # Gender
    gender_data = group_means(df, col, "male")
    result["gender"] = {str(int(r["group"])): r for r in gender_data}  # 0=female, 1=male
    result["gender"]["p_equal"] = round(wald_p(df, col, "male"), 4)

    # Bloc
    bloc_data = group_means(df, col, "bloc")
    result["bloc"] = {str(int(r["group"])): r for r in bloc_data}
    result["bloc"]["p_equal"] = round(wald_p(df, col, "bloc"), 4)

    # 5-way region
    region_data = group_means(df, col, "region")
    result["region"] = {str(r["group"]): r for r in region_data}
    result["region"]["p_equal"] = round(wald_p(df, col, "region"), 4)

    # Prize category
    cat_data = group_means(df, col, "prize_category")
    result["prize_category"] = {str(int(r["group"])): r for r in cat_data}
    result["prize_category"]["p_equal"] = round(wald_p(df, col, "prize_category"), 4)

    return result


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = pd.read_csv(dta)
    df = add_constructed_vars(df)
    print(f"N = {len(df)}")

    # All variables in the Stata ylist
    top_20_vars = [f"top_20pct_{b}" for b in ["med_inctot", "educ", "global_med_inctot"]]
    yvars = BASE_RANKS + TOP_DECILE_VARS + top_20_vars

    data = {}
    for col in yvars:
        if col not in df.columns:
            print(f"  Skipping '{col}' — not in dataset.")
            continue
        data[col] = spec_for_rank(df, col)
        print(f"  {col}: full mean={data[col]['full_sample']['mean']:.2f}")

    payload = {
        "meta": {
            "script": "heterogeneity_spec",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": len(df),
            "se_type": "HC1",
            "source_dofile": "a/table_heterogeneity_spec.do",
            "labels": {
                "region": REGION_LABELS,
                "bloc": BLOC_LABELS,
                "prize_category": PRIZE_CAT_LABELS,
                "male": {0: "Female", 1: "Male"},
            },
        },
        "data": data,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "heterogeneity_spec.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
