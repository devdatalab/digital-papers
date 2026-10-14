#!/usr/bin/env python3
"""Permutation test for parent-child scientific field match (Figure 3 / Table 3).

Supplementary panels: A18. Appendix figure/table labels below
refer to the PDF numbering.

Why this file exists:
    Replicates a/same_parent_field_rand_test.do. For each match-quality tier
    (prof_match, nonprof_match, weak_match, and "good" = prof+nonprof combined)
    and each sample (econ/non-econ), runs a Monte Carlo permutation test that
    asks: given the observed parent-field distribution, how often would a random
    assignment of Nobel prizes produce as many field matches as we observe?

    The permutation distribution is compared to the observed match count to
    produce a p-value, expected count, and excess rate. These feed Table 3
    (tab:parent_child_field_match) and Figure 3 (fig:perm_main, which is the
    good-match × non-econ panel).

Algorithm:
    For each simulated trial (B=10,000), independently draw child fields from
    the empirical prize-field distribution and parent fields from the empirical
    parent-field distribution within the sub-sample. Count the share that match.
    P-value = fraction of simulated shares exceeding the observed share.

Note on random seed:
    Stata and NumPy use different PRNGs, so the exact simulation draws differ.
    With B=10,000 the Monte Carlo SEs are <0.005; conclusions are the same.
    Original Stata seed: 20260515.

Variable derivation:
    nobelists_analysis.csv supplies parent_field and parent_field_match_type,
    including the PDF paper's laureate-specific biographical overrides.

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/parent_field_match/output/parent_field_perm_test.json

Run:
    python code/parent_field_match/parent_field_perm_test.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"

B = 10_000
SEED = 20260515

# Hardcoded prize-field shares used as the null distribution of child fields.
# These are the global fractions from the analysis dataset — see Stata comments:
#   "Override expected prize shares since we think they're endogenous."
# Non-econ sample shares (no economics prize):
PRIZE_PROBS_NONECON = {"chemistry": 0.2990, "physics": 0.3408, "medicine": 0.3602, "economics": 0.0}
# Econ sample shares (prize year >= 1969, all four fields):
PRIZE_PROBS_ECON = {"chemistry": 0.2434, "physics": 0.2763, "medicine": 0.2785, "economics": 0.2018}

FIELDS = ["chemistry", "physics", "medicine", "economics"]


def load_data() -> pd.DataFrame:
    """Load parent fields and match types, preserving biographical overrides."""
    df = pd.read_csv(DATA_DIR / "nobelists_analysis.csv")

    # The analysis fields include the occupation crosswalk plus manual overrides.
    # Preserve those final classifications, including explicit "none" values.
    df = df.rename(columns={"parent_field_match_type": "match_type"}).copy()
    df["parent_field"] = df["parent_field"].fillna("none").str.strip().str.lower()
    df["match_type"] = df["match_type"].fillna("none").str.strip()

    # Derive category_key from the `category` string column
    df["category_key"] = df["category"].fillna("").str.strip().str.lower()

    return df


def build_sample_mask(df: pd.DataFrame, sample: str) -> pd.Series:
    sci_fields_4 = set(FIELDS)
    sci_fields_3 = {"chemistry", "physics", "medicine"}
    if sample == "econ_sample":
        return (df["prize_year"] >= 1969) & df["parent_field"].isin(sci_fields_4)
    else:  # nonecon_sample
        return (df["category_key"] != "economics") & df["parent_field"].isin(sci_fields_3)


def build_match_mask(df: pd.DataFrame, match_type: str) -> pd.Series:
    if match_type == "good":
        return df["match_type"].isin({"prof_match", "nonprof_match"})
    return df["match_type"] == match_type


def perm_test(
    df: pd.DataFrame,
    match_type: str,
    sample: str,
    rng: np.random.Generator,
) -> dict:
    """Run the permutation test for one (match_type, sample) combination."""
    sub = df[build_sample_mask(df, sample) & build_match_mask(df, match_type)].copy()

    if len(sub) == 0:
        return {"n": 0, "skipped": True}

    n = len(sub)
    is_econ = sample == "econ_sample"
    prize_probs_dict = PRIZE_PROBS_ECON if is_econ else PRIZE_PROBS_NONECON

    # Parent field counts (empirical distribution of parents in this sub-sample)
    parent_counts = {f: int((sub["parent_field"] == f).sum()) for f in FIELDS}
    parent_total = sum(parent_counts.values())
    parent_probs = np.array([parent_counts[f] / parent_total for f in FIELDS])

    # Prize field probabilities (null hypothesis)
    prize_probs = np.array([prize_probs_dict[f] for f in FIELDS])

    # Observed matches (same_cat: parent_field == category_key)
    n_observed = int((sub["parent_field"] == sub["category_key"]).sum())
    observed_share = n_observed / n

    # Monte Carlo simulation
    child_draws = rng.choice(len(FIELDS), size=(B, n), p=prize_probs)
    parent_draws = rng.choice(len(FIELDS), size=(B, n), p=parent_probs)
    sim_shares = (child_draws == parent_draws).mean(axis=1)

    p_value = float((sim_shares > observed_share).mean())
    expected_count = float(sim_shares.mean() * n)
    expected_share = float(sim_shares.mean())
    excess_rate = 100.0 * (n_observed / expected_count - 1) if expected_count > 0 else np.nan

    # Histogram of simulated shares (for Figure 3 plot)
    bin_width = 0.04
    bin_edges = np.arange(0, 0.64 + bin_width, bin_width)
    counts, _ = np.histogram(sim_shares, bins=bin_edges)
    sim_histogram = [
        {"bin_center": round(float(left + bin_width / 2), 4), "fraction": round(float(c / B), 6)}
        for left, c in zip(bin_edges[:-1], counts)
    ]

    return {
        "n": n,
        "parent_counts": parent_counts,
        "n_observed": n_observed,
        "observed_share": round(observed_share, 4),
        "observed_pct": round(100 * observed_share, 1),
        "expected_count": round(expected_count, 2),
        "expected_pct": round(100 * expected_share, 1),
        "excess_rate": round(excess_rate, 1),
        "p_value": round(p_value, 4),
        "p_value_display": "<0.01" if p_value < 0.01 else f"{p_value:.2f}",
        "sim_histogram": sim_histogram,
        "sim_mean": round(float(sim_shares.mean()), 4),
        "sim_std": round(float(sim_shares.std()), 4),
    }


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = load_data()
    print(f"N total = {len(df)}")

    rng = np.random.default_rng(SEED)
    data = {}

    match_types = ["prof_match", "nonprof_match", "weak_match", "good"]
    samples = ["econ_sample", "nonecon_sample"]

    for mtype in match_types:
        for sample in samples:
            key = f"{mtype}_{sample}"
            result = perm_test(df, mtype, sample, rng)
            data[key] = result
            if result.get("skipped"):
                print(f"  {key}: SKIPPED (n=0)")
            else:
                print(
                    f"  {key}: n={result['n']}, observed={result['n_observed']} "
                    f"({result['observed_pct']:.0f}%), expected={result['expected_count']:.1f} "
                    f"({result['expected_pct']:.0f}%), excess={result['excess_rate']:.0f}%, "
                    f"p={result['p_value_display']}"
                )

    payload = {
        "meta": {
            "script": "parent_field_perm_test",
            "generated": datetime.now(timezone.utc).isoformat(),
            "B": B,
            "seed_numpy": SEED,
            "seed_stata_original": 20260515,
            "note": "Random draws differ from Stata; p-values agree within Monte Carlo SE (<0.005)",
            "prize_probs_nonecon": PRIZE_PROBS_NONECON,
            "prize_probs_econ": PRIZE_PROBS_ECON,
            "source_dofile": "a/same_parent_field_rand_test.do",
        },
        "data": data,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "parent_field_perm_test.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
