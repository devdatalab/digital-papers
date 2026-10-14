#!/usr/bin/env python3
"""Regional and country-bloc analyses for the regional appendix tables/figures.

Supplementary panels: A7. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Replicates five Stata dofiles covering regional heterogeneity:
      - a/table_region_spec.do      → region_spec: rank ~ prize_year by 5-region × USA vs. RoW
      - a/table_bloc_spec.do        → bloc_spec: rank ~ prize_year by bloc (West/East/South)
      - a/table_region_top_pctl.do  → region_top_pctl: top-pct indicator ~ i.bloc
      - a/table_bloc_interaction.do → bloc_interaction: rank ~ bloc × prize_year/post1950/gender
      - a/graph_regions.do          → binscatter_bloc: rank vs prize_year by bloc

Region construction (table_region_spec.do sequential logic):
    1 = West excl. USA  (bloc==0, country_name != "USA", scandinavia==0)
    2 = East            (bloc==1)
    3 = Global South    (bloc==2)
    4 = Scandinavia     (scandinavia==1, overrides any prior assignment)
    5 = USA             (country_name == "USA", overrides any prior assignment)

bloc_nr construction (table_bloc_interaction.do):
    1 = West (bloc==0), 2 = East (bloc==1), 3 = Global South (bloc==2)

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/regional_analysis/output/regional_analysis.json

Run:
    python code/regional_analysis/regional_analysis.py
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

RANK_VARS_2 = ["med_inctot_rank", "educ_rank"]
RANK_VARS_3 = ["med_inctot_rank", "educ_rank", "global_med_inctot_rank"]
RANK_BASES_2 = ["med_inctot", "educ"]
N_BINS = 20

REGION_LABELS = {1: "West (excl. USA)", 2: "East", 3: "Global South", 4: "Scandinavia", 5: "USA"}
BLOC_LABELS = {0: "West", 1: "East", 2: "Global South"}
BLOC_CODES = {"west": 0, "east": 1, "south": 2}


def coerce_bloc(df: pd.DataFrame) -> None:
    """Normalize legacy numeric bloc codes and current string labels in-place."""
    raw = df["bloc"]
    numeric = pd.to_numeric(raw, errors="coerce")
    label_codes = raw.astype("string").str.strip().str.lower().map(BLOC_CODES)
    coded = numeric.where(numeric.notna(), label_codes)
    unknown = raw.notna() & coded.isna()
    if unknown.any():
        values = sorted(raw[unknown].astype(str).unique())
        raise ValueError(f"Unknown bloc labels: {values}")
    df["bloc"] = coded.astype(float)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "nobelists_analysis.csv")
    df["prize_year_rescaled"] = df["prize_year"] - 1901
    coerce_bloc(df)

    # 5-region variable — sequential assignment matching table_region_spec.do
    region = pd.Series(np.nan, index=df.index)
    region[(df["bloc"] == 0) & (df["country_name"] != "USA")] = 1
    region[df["bloc"] == 1] = 2
    region[df["bloc"] == 2] = 3
    region[df["scandinavia"] == 1] = 4   # overrides
    region[df["country_name"] == "USA"] = 5  # overrides
    df["region"] = region

    # bloc_nr for interaction tables (West=1, East=2, South=3)
    df["bloc_nr"] = np.where(df["bloc"] == 0, 1, np.where(df["bloc"] == 1, 2, 3))

    return df


def reg_result(model) -> dict:
    result = {}
    for k in model.params.index:
        result[k] = {"coef": round(float(model.params[k]), 6), "se": round(float(model.bse[k]), 6)}
    result["n"] = int(model.nobs)
    result["r2"] = round(float(model.rsquared), 6)
    return result


# ── 1. Rank trend by 5-region + USA vs. RoW ────────────────────────────────────

def region_spec(df: pd.DataFrame) -> dict:
    """reg rank prize_year_rescaled if region == r, HC1  (for r in 1..5).
    Also: reg rank usa, HC1."""
    results: dict = {"by_region": {}, "usa_vs_row": {}}

    for rank in RANK_VARS_2:
        results["by_region"][rank] = {}
        for r, label in REGION_LABELS.items():
            sub = df[df["region"] == r][["prize_year_rescaled", rank]].dropna()
            if len(sub) < 5:
                results["by_region"][rank][str(r)] = {"skipped": True, "n": len(sub), "label": label}
                print(f"  region_spec {rank} r={r} ({label}): SKIPPED n={len(sub)}")
                continue
            model = smf.ols(f"Q('{rank}') ~ prize_year_rescaled", data=sub).fit(cov_type="HC1")
            results["by_region"][rank][str(r)] = {"label": label, **reg_result(model)}
            print(f"  region_spec {rank} r={r} ({label}): coef={model.params['prize_year_rescaled']:.4f} "
                  f"n={int(model.nobs)}")

        # USA vs. rest of world
        sub_usa = df[["usa", rank]].dropna()
        sub_usa = sub_usa[sub_usa["usa"].notna()]
        model_usa = smf.ols(f"Q('{rank}') ~ usa", data=sub_usa).fit(cov_type="HC1")
        results["usa_vs_row"][rank] = reg_result(model_usa)
        print(f"  region_spec {rank} USA coef={model_usa.params['usa']:.4f} n={int(model_usa.nobs)}")

    return results


# ── 2. Rank trend by bloc ───────────────────────────────────────────────────────

def bloc_spec(df: pd.DataFrame) -> dict:
    """reg rank prize_year_rescaled if bloc == j, HC1  (j in 0, 1, 2)."""
    results: dict = {}
    for rank in RANK_VARS_3:
        results[rank] = {}
        for j, label in BLOC_LABELS.items():
            sub = df[df["bloc"] == j][["prize_year_rescaled", rank]].dropna()
            model = smf.ols(f"Q('{rank}') ~ prize_year_rescaled", data=sub).fit(cov_type="HC1")
            results[rank][str(j)] = {"label": label, **reg_result(model)}
            print(f"  bloc_spec {rank} bloc={j} ({label}): coef={model.params['prize_year_rescaled']:.4f} "
                  f"n={int(model.nobs)}")
    return results


# ── 3. Top-pct indicators by bloc ──────────────────────────────────────────────

def region_top_pctl(df: pd.DataFrame) -> dict:
    """reg top_{cutoff}_{base} i.bloc, HC1.
    In Python: C(bloc_nr) with reference = 1 (West), or use bloc directly."""
    cutoffs = ["decile", "5pct"]
    results: dict = {}
    for cutoff in cutoffs:
        results[cutoff] = {}
        for base in RANK_BASES_2:
            dep = f"top_{cutoff}_{base}"
            sub = df[[dep, "bloc_nr"]].dropna()
            # Stata uses i.bloc with bloc==0 as base; bloc_nr==1 is West (base)
            model = smf.ols(f"Q('{dep}') ~ C(bloc_nr)", data=sub).fit(cov_type="HC1")
            r = reg_result(model)
            results[cutoff][base] = r
            west = r.get("Intercept", r.get("(Intercept)", {}))
            east_key = "C(bloc_nr)[T.2]"
            south_key = "C(bloc_nr)[T.3]"
            print(f"  region_top_pctl {cutoff} {base}: "
                  f"West={r.get('Intercept', {}).get('coef', 'n/a'):.3f} "
                  f"East={r.get(east_key, {}).get('coef', float('nan')):.3f} "
                  f"South={r.get(south_key, {}).get('coef', float('nan')):.3f} "
                  f"n={r.get('n', '?')}")
    return results


# ── 4. Bloc interaction tables ─────────────────────────────────────────────────

def bloc_interaction(df: pd.DataFrame) -> dict:
    """Three interaction models from table_bloc_interaction.do."""
    results: dict = {"trend_interaction": {}, "post1950_interaction": {}, "gender_by_bloc": {}}

    for rank in RANK_VARS_2:

        # (a) rank ~ C(bloc_nr) * prize_year_rescaled
        sub = df[[rank, "bloc_nr", "prize_year_rescaled"]].dropna()
        m = smf.ols(f"Q('{rank}') ~ C(bloc_nr) * prize_year_rescaled", data=sub).fit(cov_type="HC1")
        results["trend_interaction"][rank] = reg_result(m)
        print(f"  bloc_interaction trend {rank}: n={int(m.nobs)}")

        # (b) rank ~ C(bloc_nr) * post1950
        sub2 = df[[rank, "bloc_nr", "post1950"]].dropna()
        m2 = smf.ols(f"Q('{rank}') ~ C(bloc_nr) * post1950", data=sub2).fit(cov_type="HC1")
        results["post1950_interaction"][rank] = reg_result(m2)
        print(f"  bloc_interaction post1950 {rank}: n={int(m2.nobs)}")

        # (c) for each bloc: rank ~ post1950 + pre1950_female + post1950_female
        results["gender_by_bloc"][rank] = {}
        for b, label in [(1, "west"), (2, "east"), (3, "south")]:
            sub3 = df[df["bloc_nr"] == b][[rank, "post1950", "pre1950_female", "post1950_female"]].dropna()
            if len(sub3) < 10:
                results["gender_by_bloc"][rank][label] = {"skipped": True, "n": len(sub3)}
                print(f"  gender_by_bloc {rank} {label}: SKIPPED n={len(sub3)}")
                continue
            m3 = smf.ols(
                f"Q('{rank}') ~ post1950 + pre1950_female + post1950_female", data=sub3
            ).fit(cov_type="HC1")
            results["gender_by_bloc"][rank][label] = reg_result(m3)
            print(f"  gender_by_bloc {rank} {label}: n={int(m3.nobs)}")

    return results


# ── 5. Binscatter by bloc ──────────────────────────────────────────────────────

def binscatter_bloc(df: pd.DataFrame) -> dict:
    """Binscatter of rank vs prize_year, separately for each bloc."""
    results: dict = {}
    for rank in RANK_VARS_2:
        results[rank] = {}
        for j, label in BLOC_LABELS.items():
            sub = df[df["bloc"] == j][[rank, "prize_year"]].dropna()
            if len(sub) < N_BINS:
                results[rank][label] = []
                continue
            x_bin = pd.qcut(sub["prize_year"], q=N_BINS, labels=False, duplicates="drop")
            bins = (
                pd.DataFrame({"y": sub[rank].values, "x": sub["prize_year"].values, "bin": x_bin.values})
                .groupby("bin")[["x", "y"]]
                .mean()
                .reset_index(drop=True)
            )
            results[rank][label] = [
                {"x": round(float(r.x), 2), "y": round(float(r.y), 4)} for _, r in bins.iterrows()
            ]
            print(f"  binscatter_bloc {rank} {label}: {len(results[rank][label])} bins")
    return results


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = load_data()
    print(f"N total = {len(df)}")
    print(f"Region distribution:\n{df['region'].value_counts().sort_index()}\n")

    print("[1/5] Region-stratified trend regressions")
    r_spec = region_spec(df)

    print("\n[2/5] Bloc-stratified trend regressions")
    b_spec = bloc_spec(df)

    print("\n[3/5] Top-percentile indicators ~ bloc")
    r_top = region_top_pctl(df)

    print("\n[4/5] Bloc interaction models")
    b_inter = bloc_interaction(df)

    print("\n[5/5] Binscatter rank vs prize_year by bloc")
    bs_bloc = binscatter_bloc(df)

    payload = {
        "meta": {
            "script": "regional_analysis",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": int(len(df)),
            "source_dofiles": [
                "a/table_region_spec.do",
                "a/table_bloc_spec.do",
                "a/table_region_top_pctl.do",
                "a/table_bloc_interaction.do",
                "a/graph_regions.do",
            ],
            "region_labels": REGION_LABELS,
            "bloc_labels": BLOC_LABELS,
        },
        "data": {
            "region_spec": r_spec,
            "bloc_spec": b_spec,
            "region_top_pctl": r_top,
            "bloc_interaction": b_inter,
            "binscatter_bloc": bs_bloc,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "regional_analysis.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
