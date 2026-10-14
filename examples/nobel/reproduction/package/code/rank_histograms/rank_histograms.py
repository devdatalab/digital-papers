#!/usr/bin/env python3
"""Histogram data for Figure 1: father rank distributions.

Why this file exists:
    Replicates a/graph_ranks_histogram.do. Produces the binned percentage data
    for three father-rank histograms (national income rank, national education
    rank, global income rank) for the full sample and separately by gender.
    Reproduces the paper's Figure 1.

Upstream dependencies:
    data/nobelists_analysis.csv

Output:
    code/rank_histograms/output/rank_histograms.json

Run:
    python code/rank_histograms/rank_histograms.py
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

RANKS = [
    ("med_inctot_rank", "Father's national income rank"),
    ("educ_rank", "Father's national education rank"),
    ("global_med_inctot_rank", "Father's global income rank"),
]
BIN_WIDTH = 5
BIN_EDGES = list(range(0, 101, BIN_WIDTH))  # [0, 5, 10, ..., 100]
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


def histogram_pcts(series: pd.Series) -> list[dict]:
    """Return percent in each 5-percentile bin (midpoint x, pct y).

    Replicates Stata:
        replace rank = 99 if rank == 100
        egen bin = cut(rank), at(0(5)100)
        histogram bin, discrete width(5) percent
    """
    s = series.dropna().clip(upper=99)
    total = len(s)
    result = []
    for left in BIN_EDGES[:-1]:
        right = left + BIN_WIDTH
        count = int(((s >= left) & (s < right)).sum())
        pct = round(100.0 * count / total, 4) if total > 0 else 0.0
        result.append({"x": left + BIN_WIDTH / 2, "pct": pct})
    return result


def rank_histograms(df: pd.DataFrame, col: str) -> dict:
    return {
        "full": histogram_pcts(df[col]),
        "male": histogram_pcts(df.loc[df["female"] == 0, col]),
        "female": histogram_pcts(df.loc[df["female"] == 1, col]),
    }


def main() -> None:
    dta = DATA_DIR / "nobelists_analysis.csv"
    if not dta.exists():
        raise SystemExit(f"Input not found: {dta}")

    df = pd.read_csv(dta)
    # Stata stored empty strings as "" (not missing); read_csv turns empty CSV
    # fields into NaN. Restore "" on string columns so downstream string filters
    # and grouping reproduce the original .dta behaviour.
    _str_cols = df.select_dtypes(include=["object", "string"]).columns
    df[_str_cols] = df[_str_cols].fillna("")
    coerce_female(df)
    # Stata: keep if !missing(father_occupation)
    df = df[df["father_occupation"].notna()].copy()
    n = len(df)
    print(f"N = {n}")

    data = {}
    for col, label in RANKS:
        if col not in df.columns:
            raise SystemExit(f"Column '{col}' not found in dataset.")
        data[col] = {"label": label, **rank_histograms(df, col)}

    payload = {
        "meta": {
            "script": "rank_histograms",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n": n,
            "source_dofile": "a/graph_ranks_histogram.do",
        },
        "data": data,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "rank_histograms.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {out.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
