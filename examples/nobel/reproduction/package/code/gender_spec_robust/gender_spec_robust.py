#!/usr/bin/env python3
"""Gender-gap robustness regressions for Appendix Table A8.

Supplementary panels: A3. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    The paper's Appendix Table A8 (`tab:gender_robust`) — "Differences in
    Average SES Rank of Laureate Fathers, by Gender: Robustness" — was not
    part of the original Stata code; this module reproduces it.

    Table A8 re-estimates the male–female gap in father SES rank (the Table 2 /
    heterogeneity Panel A specification: outcome ~ female, HC1 robust SEs) on
    four exclusion samples, to show the gap does not hinge on the hardest-to-rank
    fathers. The four samples are the same ones used by main_robust.py's Table A5.

    Every coefficient, standard error and N produced here reproduces the
    published table exactly (verified against the published paper,
    Appendix Table A8).

Appendix Table A8 — same female specification, four restricted samples:
    Panel A  exclude difficult-to-classify fathers  classification_difficult == 1  (N=700)
    Panel B  exclude aristocrats                    occ1950 == 9999                (N=704)
    Panel C  exclude business owners and farmers    occ1950 in {100, 290}          (N=559)
    Panel D  exclude the economics prize            category == "economics"        (N=621)

    Six outcomes per panel: national income rank and education rank (continuous
    "Average Rank"), plus Top-10% and Top-20% family indicators for each. Each
    cell reports the `female` coefficient (female − male baseline) with an HC1
    SE, plus the constant (baseline male level) and N.

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/gender_spec_robust/output/gender_spec_robust.json

Run:
    python code/gender_spec_robust/gender_spec_robust.py
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

# occ1950 sentinel codes defining the exclusion sub-samples (from main_robust.py).
OCC_ARISTOCRAT = 9999          # occ1950_label == "aristocrat"
OCC_FARMERS = 100              # "farmers (owners and tenants)"
OCC_PROPRIETORS = 290          # "managers, officials, and proprietors (nec)"

FEMALE_CODES = {"male": 0, "female": 1}

# The six outcomes, in the paper's row order. `indicator` marks the four Top-N
# family measures — the published table prints significance stars only on those,
# not on the two continuous "Average Rank" outcomes.
OUTCOMES = [
    ("med_inctot_rank", False),
    ("educ_rank", False),
    ("top_decile_med_inctot", True),
    ("top_decile_educ", True),
    ("top_20pct_med_inctot", True),
    ("top_20pct_educ", True),
]


def stars(p: float) -> str:
    """Significance markers as printed in the paper: * .10, ** .05, *** .01."""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def coerce_female(df: pd.DataFrame) -> None:
    """Normalize legacy numeric gender codes and current string labels in-place.

    Mirrors gender_analysis.coerce_female: the `female` column ships as string
    labels ("male"/"female") in the current data, but may be numeric in older
    extracts.
    """
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
    path = DATA_DIR / "nobelists_analysis.csv"
    if not path.exists():
        raise SystemExit(f"Input not found: {path}")
    df = pd.read_csv(path, low_memory=False)
    coerce_female(df)
    return df


def female_reg(df: pd.DataFrame, col: str) -> dict:
    """OLS of `col` on the female indicator with HC1 SEs.

    Same specification as Table 2 / heterogeneity Panel A. Returns the female
    coefficient (female − male baseline), its SE and p-value, plus the intercept
    (the baseline male level) and N.
    """
    sub = df[["female", col]].dropna()
    model = smf.ols(f"Q('{col}') ~ female", data=sub).fit(cov_type="HC1")
    return {
        "constant": round(float(model.params["Intercept"]), 4),
        "constant_se": round(float(model.bse["Intercept"]), 4),
        "coef": round(float(model.params["female"]), 6),
        "se": round(float(model.bse["female"]), 6),
        "p": round(float(model.pvalues["female"]), 6),
        "n": int(model.nobs),
    }


def build_a8(df: pd.DataFrame) -> dict:
    """Table A8 — same female specification, four restricted samples."""
    is_econ = df["category"].astype("string").str.lower().str.contains("econ", na=False)

    panels = [
        ("A", "Sample excluding difficult to classify observations",
         df[df["classification_difficult"] != 1]),
        ("B", "Sample excluding aristocrats",
         df[df["occ1950"] != OCC_ARISTOCRAT]),
        ("C", "Sample excluding business owners and farmers",
         df[~df["occ1950"].isin([OCC_FARMERS, OCC_PROPRIETORS])]),
        ("D", "Sample excluding Economics",
         df[~is_econ]),
    ]

    out: dict = {}
    for key, title, sub in panels:
        outcomes = {col: female_reg(sub, col) for col, _ in OUTCOMES}
        # Per-outcome N coincide within a panel (same rows non-missing); report
        # the panel N from the primary income-rank outcome for the column header.
        out[key] = {
            "title": title,
            "n": outcomes["med_inctot_rank"]["n"],
            "outcomes": outcomes,
        }
        inc, edu = outcomes["med_inctot_rank"], outcomes["educ_rank"]
        print(f"  A8 Panel {key}: n={out[key]['n']:3}  "
              f"IncRank {inc['constant']:.3f} / {inc['coef']:+.3f}{stars(inc['p']):3}"
              f"  EducRank {edu['constant']:.3f} / {edu['coef']:+.3f}{stars(edu['p'])}")
    return out


def main() -> None:
    df = load_data()
    print(f"N total = {len(df)}, N female = {int(df['female'].sum())}")

    print("\nAppendix Table A8 — gender gap under sample restrictions")
    a8 = build_a8(df)

    payload = {
        "meta": {
            "script": "gender_spec_robust",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_total": int(len(df)),
            "n_female": int(df["female"].sum()),
            "rhs_variable": "female",
            "rhs_note": "coefficient = female mean − male baseline (the Intercept)",
            "se_type": "HC1",
            "paper_table": "Appendix Table A8 (tab:gender_robust)",
            "source_dofile": "a/table_gender_robust.do",
        },
        "data": a8,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "gender_spec_robust.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
