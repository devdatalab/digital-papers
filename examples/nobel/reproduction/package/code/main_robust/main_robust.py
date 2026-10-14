#!/usr/bin/env python3
"""Robustness regressions for Appendix Tables A5 and A6.

Supplementary panels: A2, A14. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    The paper's two main-specification robustness tables were not part of the
    original Stata code; this module reproduces them. Both tables re-run the Table 1 specification —
    OLS of a father SES rank on a linear time trend, HC1 robust SEs — under
    alternate samples (A5) and alternate rank codings (A6).

    Every coefficient, standard error and N produced here reproduces the
    published table exactly (verified against the published paper,
    pp. 36-37).

Appendix Table A5 — alternate samples (dependent vars unchanged):
    Panel A  exclude difficult-to-classify fathers  classification_difficult == 1  (13 dropped, N=700)
    Panel B  exclude aristocrats                    occ1950 == 9999               ( 9 dropped, N=704)
    Panel C  exclude business owners and farmers    occ1950 in {100, 290}         (154 dropped, N=559)
    Panel D  exclude the economics prize            category == "economics"       (92 dropped, N=621)

    Note on the paper's notes: the A5 note says "8 laureates whose fathers were
    aristocrats" and "134 children of business owners and farmers". The data
    yield 9 and 154, which is what reproduces the table's own published N of 704
    and 559. The prose counts are stale; the numbers here match the table.

Appendix Table A6 — alternate codings (full sample, N=713):
    Panel A  heterogeneous business-owner coding    inc_rank_alt / educ_rank_alt_biz
    Panel B  education recoded from biographies                  educ_rank_alt_ed
    Panel C  both of the above                                   educ_rank_alt_both

    A6 Panels B and C have no income column in the published table (the recoding
    only touches education), so only the education column is emitted.

Not here on purpose:
    Appendix Table A7 (`tab:pregdp`) needs no new module — main_spec.py already
    regresses both global_med_inctot_rank and global_med_inctot_pregdp_rank, so
    main_spec.json holds A7's two columns already.

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/main_robust/output/main_robust.json

Run:
    python code/main_robust/main_robust.py
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

# occ1950 sentinel codes used to define the A5 sub-samples.
OCC_ARISTOCRAT = 9999          # occ1950_label == "aristocrat"
OCC_FARMERS = 100              # "farmers (owners and tenants)"
OCC_PROPRIETORS = 290          # "managers, officials, and proprietors (nec)"

INCOME_LABEL = "National Income Rank"
EDUC_LABEL = "National Education Rank"


def stars(p: float) -> str:
    """Significance markers as printed in the paper: * .10, ** .05, *** .01."""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def trend_reg(df: pd.DataFrame, col: str) -> dict:
    """OLS of `col` on the 1901-rescaled prize year with HC1 SEs.

    Mirrors main_spec.run_spec so A5/A6 stay comparable with Table 1, but also
    returns p-values (the appendix tables print significance stars) and the
    intercept as a named "constant" (the tables label it "Constant (Year = 1901)").
    """
    sub = df[["prize_year_rescaled", col]].dropna()
    model = smf.ols(f"Q('{col}') ~ prize_year_rescaled", data=sub).fit(cov_type="HC1")
    return {
        "column": col,
        "constant": round(float(model.params["Intercept"]), 4),
        "constant_se": round(float(model.bse["Intercept"]), 4),
        "constant_stars": stars(float(model.pvalues["Intercept"])),
        "coef": round(float(model.params["prize_year_rescaled"]), 6),
        "se": round(float(model.bse["prize_year_rescaled"]), 6),
        "stars": stars(float(model.pvalues["prize_year_rescaled"])),
        "n": int(model.nobs),
        "r2": round(float(model.rsquared), 4),
    }


def load_data() -> pd.DataFrame:
    path = DATA_DIR / "nobelists_analysis.csv"
    if not path.exists():
        raise SystemExit(f"Input not found: {path}")
    df = pd.read_csv(path, low_memory=False)
    # Same RHS as Table 1: years since the first prize (1901).
    df["prize_year_rescaled"] = df["prize_year"] - 1901
    return df


def build_a5(df: pd.DataFrame) -> dict:
    """Table A5 — same dependent variables, four restricted samples."""
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
        out[key] = {
            "title": title,
            "income": trend_reg(sub, "med_inctot_rank"),
            "education": trend_reg(sub, "educ_rank"),
        }
        inc, edu = out[key]["income"], out[key]["education"]
        print(f"  A5 Panel {key}: N={inc['n']:3}  inc {inc['constant']:.3f} / {inc['coef']:+.3f}{inc['stars']:3}"
              f"  educ {edu['constant']:.3f} / {edu['coef']:+.3f}{edu['stars']}")
    return out


def build_a6(df: pd.DataFrame) -> dict:
    """Table A6 — full sample, alternate rank codings.

    Panels B and C recode education only, so they carry no income column; the
    published table leaves those cells blank.
    """
    panels = [
        ("A", "Heterogeneous coding of business owners", "inc_rank_alt", "educ_rank_alt_biz"),
        ("B", "Recoding education according to biographies", None, "educ_rank_alt_ed"),
        ("C", "Recoding education and heterogeneous business owners", None, "educ_rank_alt_both"),
    ]

    out: dict = {}
    for key, title, inc_col, edu_col in panels:
        entry: dict = {"title": title, "education": trend_reg(df, edu_col)}
        if inc_col is not None:
            entry["income"] = trend_reg(df, inc_col)
        out[key] = entry
        edu = entry["education"]
        inc_txt = (f"inc {entry['income']['constant']:.3f} / {entry['income']['coef']:+.3f}"
                   f"{entry['income']['stars']:3}" if inc_col else "inc      —        ")
        print(f"  A6 Panel {key}: N={edu['n']:3}  {inc_txt}  educ {edu['constant']:.3f} / "
              f"{edu['coef']:+.3f}{edu['stars']}")
    return out


def main() -> None:
    df = load_data()
    print(f"N = {len(df)} (base analysis sample: {int(df['med_inctot_rank'].notna().sum())})")

    print("\n[1/2] Appendix Table A5 — robustness to sample restrictions")
    a5 = build_a5(df)

    print("\n[2/2] Appendix Table A6 — robustness to alternate codings")
    a6 = build_a6(df)

    payload = {
        "meta": {
            "script": "main_robust",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": int(len(df)),
            "rhs_variable": "prize_year_rescaled",
            "rhs_note": "prize_year - 1901; coefficient = change in rank per year since 1901",
            "se_type": "HC1",
            "column_labels": {"income": INCOME_LABEL, "education": EDUC_LABEL},
            "source_dofile": "a/table_main_spec_robust.do, a/table_main_spec_robust_2.do",
            "paper_tables": {"a5": "Appendix Table A5", "a6": "Appendix Table A6"},
        },
        "data": {"a5": a5, "a6": a6},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "main_robust.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nWrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
