#!/usr/bin/env python3
"""Extended-results grid: SES measure x outcome x subgroup binscatters + histograms.

Why this file exists:
    Powers the site's `/extended-results` Extras page, which reimagines the
    standalone `nobel-agents/main_results` dashboard as a native part of this
    digital edition. It precomputes, for every combination of

        SES measure (3)  x  subgroup (overall + 4 fields + 2 genders + 5 regions)

    a father-rank histogram and three prize-year binscatters with linear trends:
        - average_rank : mean rank by 5-year prize-year window
        - top_10       : share with rank >= 90 (recoded to 0/100 before binning)
        - top_20       : share with rank >= 80 (recoded to 0/100 before binning)

    Region subgroups are skipped under the global-income measure (region is the
    main factor driving global-rank differences), matching the reference UI rule.

    This ports the *data half* of nobel-agents/main_results/code/make_main_results.py
    verbatim (region_label, measure_sample, histogram_data, panel_values,
    time_binscatter_data, robust_ols, robust_linear_regression,
    grouped_panel_regressions, two_sided_t_pvalue) so the site's numbers match the
    reference dashboard: same HC1 robust SEs, same 5-year windows, same pooled
    interacted subgroup slopes (Table A12 structure), same out-of-sample fit
    endpoints. All SVG/HTML rendering from the reference is dropped.

    Data note: the reference reads `nobelists_analysis.dta` (714 nonmissing rank
    rows). This project's `package/data/nobelists_analysis.csv` is the source
    of truth here and carries 713 nonmissing rank rows -- a one-row content drift
    (one Western Europe laureate) the project explicitly accepts. All other
    subgroup counts match the reference build log exactly.

    Encoding note: in the `.dta` `bloc` was numeric (1 = Eastern bloc, 2 = Global
    South); in the CSV it is a string ('east' / 'south' / 'west'). region_label
    maps 'east' -> Eastern Europe and 'south' -> Global South accordingly.

Upstream dependencies:
    package/data/nobelists_analysis.csv
    (ports logic from nobel-agents/main_results/code/make_main_results.py)

Output:
    generators/extended_results/output/extended_results.json
    (manually copied to src/lib/data/extended_results.json for the app)

Run:
    python generators/extended_results/extended_results.py
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "package" / "data"
OUT_DIR = Path(__file__).resolve().parent / "output"
SOURCE_CSV = DATA_DIR / "nobelists_analysis.csv"

YEAR_MIN = 1901
YEAR_MAX = 2023
HIST_BIN_WIDTH = 5
TIME_BIN_WIDTH = 5
FIT_LABEL_START_YEAR = YEAR_MIN

# --- The permutation grid (mirrors make_main_results.py constants) -----------

MEASURES = [
    {"id": "national_income", "column": "med_inctot_rank", "label": "National income rank", "short": "National income"},
    {"id": "education", "column": "educ_rank", "label": "Education rank", "short": "Education"},
    {"id": "global_income", "column": "global_med_inctot_rank", "label": "Global income rank", "short": "Global income"},
]

FIELD_GROUPS = [
    {"id": "physics", "label": "Physics", "filter_column": "category", "filter_values": ["Physics"]},
    {"id": "chemistry", "label": "Chemistry", "filter_column": "category", "filter_values": ["Chemistry"]},
    {"id": "physiology", "label": "Physiology", "filter_column": "category", "filter_values": ["Medicine"]},
    {"id": "economics", "label": "Economics", "filter_column": "category", "filter_values": ["Economics"]},
]

GENDER_GROUPS = [
    {"id": "male", "label": "Men", "filter_column": "gender", "filter_values": ["male"]},
    {"id": "female", "label": "Women", "filter_column": "gender", "filter_values": ["female"]},
]

REGION_GROUPS = [
    {"id": "usa", "label": "USA", "filter_column": "region_label", "filter_values": ["USA"]},
    {"id": "western_europe", "label": "Western Europe", "filter_column": "region_label", "filter_values": ["Western Europe"]},
    {"id": "eastern_europe", "label": "Eastern Europe", "filter_column": "region_label", "filter_values": ["Eastern Europe"]},
    {"id": "global_south", "label": "Global South", "filter_column": "region_label", "filter_values": ["Global South"]},
    {"id": "all_others", "label": "All others", "filter_column": "region_label", "filter_values": ["All others"]},
]

# Region breakdowns are uninformative for global ranks (region drives global-rank
# differences), so region subgroups are omitted under the global-income measure.
REGION_MEASURES = [m for m in MEASURES if m["id"] != "global_income"]

PANEL_SPECS = [
    {"id": "average_rank", "binary_threshold": None},
    {"id": "top_10", "binary_threshold": 90.0},
    {"id": "top_20", "binary_threshold": 80.0},
]

EASTERN_EUROPE = {"Czechoslovakia", "Poland", "Hungary", "Romania", "Lithuania"}


# --- Ported statistics (verbatim from make_main_results.py) -------------------

def is_true(value: object) -> bool:
    if pd.isna(value):
        return False
    return bool(int(value))


def region_label(row: pd.Series) -> str:
    """5-way birth-region grouping. Ports make_main_results.region_label; the only
    change is `bloc` being a CSV string ('east'/'south') rather than a numeric
    .dta code (1/2)."""
    country = str(row.get("country_name", "") or "")
    europe = is_true(row.get("europe"))
    bloc = str(row.get("bloc") or "")
    region = None

    if country == "USA":
        region = "USA"
    if europe or (country == "Finland" and region is None):
        region = "Western Europe"
    if bloc == "east" or (country in EASTERN_EUROPE and region is None):
        region = "Eastern Europe"
    if bloc == "south" or (country == "China" and region is None):
        region = "Global South"
    if region is None:
        region = "All others"
    return region


def measure_sample(
    data: pd.DataFrame,
    measure: dict[str, str],
    group: dict[str, object] | None = None,
) -> pd.DataFrame:
    subset = data[["name", "category", "prize_year", measure["column"]]].copy()
    if group is not None:
        mask = data[str(group["filter_column"])].isin(group["filter_values"])
        subset = subset.loc[mask].copy()

    subset = subset.rename(columns={measure["column"]: "rank_value"})
    subset["rank_value"] = pd.to_numeric(subset["rank_value"], errors="coerce")
    subset = subset.loc[subset["prize_year"].notna() & subset["rank_value"].notna()].copy()
    subset["prize_year"] = subset["prize_year"].astype(int)
    return subset


def robust_ols(y_values: np.ndarray, design: np.ndarray) -> dict[str, object]:
    n_obs = len(y_values)
    rank = int(np.linalg.matrix_rank(design))
    xtx_inverse = np.linalg.pinv(design.T @ design)
    coefficients = xtx_inverse @ (design.T @ y_values)
    residuals = y_values - design @ coefficients
    meat = (design * residuals[:, None]).T @ (design * residuals[:, None])
    scale = n_obs / (n_obs - rank) if n_obs > rank else 1.0
    covariance = scale * xtx_inverse @ meat @ xtx_inverse
    return {
        "n_obs": n_obs,
        "rank": rank,
        "df_resid": max(n_obs - rank, 1),
        "coefficients": coefficients,
        "covariance": covariance,
    }


def two_sided_t_pvalue(coef: float, se: float, df_resid: int) -> float:
    if not np.isfinite(coef) or not np.isfinite(se):
        return float("nan")
    if se == 0:
        return 0.0 if not math.isclose(coef, 0.0) else 1.0
    return float(2 * stats.t.sf(abs(coef / se), df_resid))


def robust_linear_regression(x_values: np.ndarray, y_values: np.ndarray) -> dict[str, float]:
    n_obs = len(x_values)
    if n_obs < 3 or np.unique(x_values).size < 2:
        return {"n_obs": float(n_obs), "intercept": float("nan"), "coef": float("nan"),
                "se": float("nan"), "p_value": float("nan")}

    design = np.column_stack([np.ones(n_obs), x_values])
    fit = robust_ols(y_values, design)
    coefficients = fit["coefficients"]
    covariance = fit["covariance"]
    slope = float(coefficients[1])
    slope_se = math.sqrt(max(float(covariance[1, 1]), 0.0))
    return {
        "n_obs": float(n_obs),
        "intercept": float(coefficients[0]),
        "coef": slope,
        "se": slope_se,
        "p_value": two_sided_t_pvalue(slope, slope_se, int(fit["df_resid"])),
    }


def histogram_data(sample: pd.DataFrame) -> pd.DataFrame:
    values = sample["rank_value"].to_numpy(dtype=float)
    capped = np.where(values >= 100.0, 99.0, values)
    bin_left = np.floor(capped / HIST_BIN_WIDTH) * HIST_BIN_WIDTH
    histogram = (
        pd.DataFrame({"bin_left": bin_left})
        .groupby("bin_left", as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    all_bins = pd.DataFrame({"bin_left": np.arange(0, 100, HIST_BIN_WIDTH, dtype=float)})
    histogram = all_bins.merge(histogram, on="bin_left", how="left").fillna({"count": 0})
    histogram["bin_right"] = histogram["bin_left"] + HIST_BIN_WIDTH
    histogram["center"] = histogram["bin_left"] + HIST_BIN_WIDTH / 2
    histogram["share_percent"] = 100 * histogram["count"] / len(sample) if len(sample) else 0.0
    return histogram


def panel_values(sample: pd.DataFrame, panel: dict[str, object]) -> np.ndarray:
    if panel["binary_threshold"] is None:
        return sample["rank_value"].to_numpy(dtype=float)
    threshold = float(panel["binary_threshold"])
    return (sample["rank_value"].to_numpy(dtype=float) >= threshold).astype(float) * 100


def time_binscatter_data(sample: pd.DataFrame, panel: dict[str, object]) -> tuple[pd.DataFrame, dict[str, float]]:
    panel_sample = sample[["name", "prize_year", "rank_value"]].copy()
    panel_sample["y_value"] = panel_values(sample, panel)
    panel_sample["bin_start"] = YEAR_MIN + ((panel_sample["prize_year"] - YEAR_MIN) // TIME_BIN_WIDTH) * TIME_BIN_WIDTH
    panel_sample["bin_end"] = np.minimum(panel_sample["bin_start"] + TIME_BIN_WIDTH - 1, YEAR_MAX)
    panel_sample["x_value"] = (panel_sample["bin_start"] + panel_sample["bin_end"]) / 2

    points = (
        panel_sample.groupby(["bin_start", "bin_end", "x_value"], as_index=False)
        .agg(y_value=("y_value", "mean"), n_obs=("name", "count"))
        .sort_values("bin_start")
    )
    regression = robust_linear_regression(
        panel_sample["prize_year"].to_numpy(dtype=float),
        panel_sample["y_value"].to_numpy(dtype=float),
    )
    return points, regression


def grouped_panel_regressions(
    data: pd.DataFrame,
    measure: dict[str, str],
    groups: list[dict[str, object]],
) -> dict[str, dict[str, dict[str, float]]]:
    """Pooled interacted OLS (one model per panel, all groups at once) so subgroup
    slope SEs match Table A12 / the reference dashboard. Verbatim port."""
    group_samples = []
    group_ids = [str(group["id"]) for group in groups]
    for group in groups:
        sample = measure_sample(data, measure, group)
        sample["group_id"] = str(group["id"])
        group_samples.append(sample[["prize_year", "rank_value", "group_id"]])

    if not group_samples:
        return {}

    sample = pd.concat(group_samples, ignore_index=True)
    results: dict[str, dict[str, dict[str, float]]] = {group_id: {} for group_id in group_ids}

    for panel in PANEL_SPECS:
        panel_sample = sample.copy()
        panel_sample["y_value"] = panel_values(panel_sample, panel)
        year = panel_sample["prize_year"].to_numpy(dtype=float)
        group_values = panel_sample["group_id"].to_numpy()
        columns = [np.ones(len(panel_sample))]
        dummy_positions: dict[str, int] = {}

        for group_id in group_ids[1:]:
            dummy_positions[group_id] = len(columns)
            columns.append((group_values == group_id).astype(float))

        slope_positions: dict[str, int] = {}
        for group_id in group_ids:
            slope_positions[group_id] = len(columns)
            columns.append(np.where(group_values == group_id, year, 0.0))

        fit = robust_ols(panel_sample["y_value"].to_numpy(dtype=float), np.column_stack(columns))
        coefficients = fit["coefficients"]
        covariance = fit["covariance"]
        df_resid = int(fit["df_resid"])

        for group_id in group_ids:
            slope_position = slope_positions[group_id]
            intercept = float(coefficients[0])
            if group_id in dummy_positions:
                intercept += float(coefficients[dummy_positions[group_id]])
            coef = float(coefficients[slope_position])
            se = math.sqrt(max(float(covariance[slope_position, slope_position]), 0.0))
            results[group_id][str(panel["id"])] = {
                "n_obs": float((group_values == group_id).sum()),
                "intercept": intercept,
                "coef": coef,
                "se": se,
                "p_value": two_sided_t_pvalue(coef, se, df_resid),
            }

    return results


# --- Emit the app JSON shape --------------------------------------------------

def fit_block(regression: dict[str, float]) -> dict[str, object]:
    """Serialise a regression result into the JSON fit block, with predicted
    endpoints at 1901 and 2023 (out-of-sample values allowed, as in the reference)."""
    intercept = regression["intercept"]
    coef = regression["coef"]
    finite = np.isfinite(intercept) and np.isfinite(coef)
    pred_start = intercept + coef * FIT_LABEL_START_YEAR if finite else float("nan")
    pred_end = intercept + coef * YEAR_MAX if finite else float("nan")

    def num(value: float, digits: int) -> float | None:
        return round(float(value), digits) if np.isfinite(value) else None

    return {
        "intercept": num(intercept, 5),
        "coef": num(coef, 6),
        "se": num(regression["se"], 6),
        "p": num(regression["p_value"], 6),
        "predStart": {"x": FIT_LABEL_START_YEAR, "y": num(pred_start, 3)},
        "predEnd": {"x": YEAR_MAX, "y": num(pred_end, 3)},
    }


def histogram_block(histogram: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {
            "x": float(row.center),
            "binStart": float(row.bin_left),
            "binEnd": float(row.bin_right),
            "share": round(float(row.share_percent), 4),
            "n": int(row.count),
        }
        for row in histogram.itertuples()
    ]


def points_block(points: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {
            "x": float(row.x_value),
            "binStart": int(row.bin_start),
            "binEnd": int(row.bin_end),
            "y": round(float(row.y_value), 4),
            "n": int(row.n_obs),
        }
        for row in points.itertuples()
    ]


def build_cell(
    data: pd.DataFrame,
    measure: dict[str, str],
    group: dict[str, object] | None,
    panel_regressions: dict[str, dict[str, float]] | None,
) -> dict[str, object]:
    """One cell = histogram + three trend panels for a (measure, subgroup)."""
    sample = measure_sample(data, measure, group)
    cell: dict[str, object] = {
        "n": int(len(sample)),
        "histogram": histogram_block(histogram_data(sample)),
        "panels": {},
    }
    for panel in PANEL_SPECS:
        points, regression = time_binscatter_data(sample, panel)
        # Subgroup cells override the per-sample fit with the pooled interacted
        # slope (matches the reference dashboard); the points are still the
        # per-group binscatter means.
        if panel_regressions is not None and str(panel["id"]) in panel_regressions:
            regression = panel_regressions[str(panel["id"])]
        cell["panels"][str(panel["id"])] = {
            "points": points_block(points),
            "fit": fit_block(regression),
        }
    return cell


def main() -> None:
    if not SOURCE_CSV.exists():
        raise SystemExit(f"Input not found: {SOURCE_CSV}")

    data = pd.read_csv(SOURCE_CSV)
    data["category"] = data["category"].fillna("").astype(str)
    data["gender"] = data["gender"].fillna("").astype(str)
    data["prize_year"] = pd.to_numeric(data["prize_year"], errors="coerce")
    data["region_label"] = data.apply(region_label, axis=1)
    n_total = len(data)
    print(f"N total = {n_total}")

    # Flat subgroup catalogue for the UI (dim + id + label).
    subgroups: list[dict[str, str]] = [{"dim": "overall", "id": "overall", "label": "Overall"}]
    for g in FIELD_GROUPS:
        subgroups.append({"dim": "field", "id": str(g["id"]), "label": str(g["label"])})
    for g in GENDER_GROUPS:
        subgroups.append({"dim": "gender", "id": str(g["id"]), "label": str(g["label"])})
    for g in REGION_GROUPS:
        subgroups.append({"dim": "region", "id": str(g["id"]), "label": str(g["label"])})

    cells: dict[str, dict[str, object]] = {}
    for measure in MEASURES:
        measure_cells: dict[str, object] = {}

        # Overall (per-sample HC1 fit).
        measure_cells["overall"] = build_cell(data, measure, None, None)

        # Field (pooled interacted slopes).
        field_regs = grouped_panel_regressions(data, measure, FIELD_GROUPS)
        for g in FIELD_GROUPS:
            measure_cells[str(g["id"])] = build_cell(data, measure, g, field_regs.get(str(g["id"])))

        # Gender (pooled interacted slopes).
        gender_regs = grouped_panel_regressions(data, measure, GENDER_GROUPS)
        for g in GENDER_GROUPS:
            measure_cells[str(g["id"])] = build_cell(data, measure, g, gender_regs.get(str(g["id"])))

        # Region (pooled interacted slopes) -- skipped for global income.
        if measure in REGION_MEASURES:
            region_regs = grouped_panel_regressions(data, measure, REGION_GROUPS)
            for g in REGION_GROUPS:
                measure_cells[str(g["id"])] = build_cell(data, measure, g, region_regs.get(str(g["id"])))

        cells[str(measure["id"])] = measure_cells
        print(f"  {measure['label']}: overall n={measure_cells['overall']['n']}, "
              f"subgroups={len(measure_cells)}")

    payload = {
        "meta": {
            "script": "extended_results",
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_total": n_total,
            "source": "package/data/nobelists_analysis.csv",
            "source_reference": "nobel-agents/main_results/code/make_main_results.py",
            "bin_width_years": TIME_BIN_WIDTH,
            "hist_bin_width": HIST_BIN_WIDTH,
            "year_min": YEAR_MIN,
            "year_max": YEAR_MAX,
            "note": (
                "Top-10/20 panels recode rank to 0/100 (>=90, >=80) before binning. "
                "Subgroup fits use the pooled interacted regression (Table A12 structure); "
                "overall fits are per-sample HC1 OLS. Region cells omitted under global_income. "
                "One-row content drift vs the reference .dta (713 vs 714 nonmissing rank rows)."
            ),
        },
        "measures": [{"id": m["id"], "label": m["label"], "column": m["column"], "short": m["short"]} for m in MEASURES],
        "subgroups": subgroups,
        "cells": cells,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "extended_results.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
