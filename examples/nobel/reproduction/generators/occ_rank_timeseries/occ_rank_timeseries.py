#!/usr/bin/env python3
"""Shape the RC-derived occupation rank time series for the Svelte site.

Supplies the full occupation-rank explorer.

Upstream dependencies:
    package/data/occ_rank_timeseries.csv
    package/data/occ_shares_10group_table.csv
    package/data/occ_shares_25group_table.csv
    package/data/occ_shares_occ1950_table.csv

Output:
    generators/occ_rank_timeseries/output/occ_rank_timeseries.json

Run:
    python generators/occ_rank_timeseries/occ_rank_timeseries.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "package" / "data"
OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "occ_rank_timeseries.json"

LEVEL_CONFIG = {
    "occgroup_10": {
        "label": "10 broad groups",
        "table": "occ_shares_10group_table.csv",
        "table_id": "occ1950_1",
        "member_count": "occ_count",
    },
    "occgroup_25": {
        "label": "25-group classification (24 groups in scope)",
        "table": "occ_shares_25group_table.csv",
        "table_id": "occgroup_25_name",
        "member_count": "occ_count",
    },
    "occ1950": {
        "label": "All occupations",
        "table": "occ_shares_occ1950_table.csv",
        "table_id": "occ1950",
        "member_count": None,
    },
}

ROW_COLUMNS = [
    "year",
    "income_rank",
    "education_rank",
    "sample_count",
]


def normalize_id(s_id: pd.Series) -> pd.Series:
    """Return stable string ids without decimal suffixes on numeric codes."""

    # Format numeric identifiers as integers and preserve named identifiers.
    s_numeric_id = pd.to_numeric(s_id, errors="coerce")
    s_normalized_id = s_id.astype(str).str.strip()
    numeric_mask = s_numeric_id.notna()
    s_normalized_id.loc[numeric_mask] = (
        s_numeric_id.loc[numeric_mask].astype(int).astype(str)
    )
    return s_normalized_id


def clean_number(value: object, decimal_places: int = 3) -> float | int | None:
    """Return a finite JSON number or null with bounded decimal precision."""

    # Convert pandas missing values to standards-compliant JSON nulls.
    if pd.isna(value):
        return None

    # Preserve integer-valued fields as JSON integers.
    number = float(value)
    if number.is_integer():
        return int(number)
    return round(number, decimal_places)


def read_inputs() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Read and validate the four committed CSV inputs."""

    # Fail before output writes when any required input is absent.
    timeseries_path = DATA_DIR / "occ_rank_timeseries.csv"
    required_path_list = [timeseries_path]
    required_path_list.extend(
        DATA_DIR / str(config["table"])
        for config in LEVEL_CONFIG.values()
    )
    missing_path_list = [path for path in required_path_list if not path.exists()]
    if missing_path_list:
        missing_listing = "\n".join(f"  - {path}" for path in missing_path_list)
        raise FileNotFoundError(f"Required input files are missing:\n{missing_listing}")

    # Load the time series and one metadata table for each classification.
    df_timeseries = pd.read_csv(timeseries_path, dtype={"occ_id": str})
    table_dict = {
        level: pd.read_csv(DATA_DIR / str(config["table"]))
        for level, config in LEVEL_CONFIG.items()
    }
    expected_column_set = {
        "level",
        "occ_id",
        "occ_label",
        "sort_order",
        *ROW_COLUMNS,
    }
    missing_column_set = expected_column_set - set(df_timeseries.columns)
    if missing_column_set:
        raise ValueError(
            "occ_rank_timeseries.csv lacks columns: "
            f"{sorted(missing_column_set)}."
        )
    if df_timeseries.duplicated(["level", "occ_id", "year"]).any():
        raise ValueError("Time-series input contains duplicate option-year rows.")

    return df_timeseries, table_dict


def build_option_metadata(
    df_level: pd.DataFrame,
    df_table: pd.DataFrame,
    level: str,
) -> pd.DataFrame:
    """Attach member and laureate counts to one level's options."""

    # Reduce the time series to its stable option metadata.
    option_columns = ["occ_id", "occ_label", "sort_order"]
    df_options = df_level[option_columns].drop_duplicates()
    if df_options["occ_id"].duplicated().any():
        raise ValueError(f"{level} has inconsistent metadata for an option id.")

    # Normalize the table key to the time series' string identifier contract.
    config = LEVEL_CONFIG[level]
    v_table_id = str(config["table_id"])
    df_table = df_table.copy()
    df_table["occ_id"] = normalize_id(df_table[v_table_id])
    if df_table["occ_id"].duplicated().any():
        raise ValueError(f"{level} metadata table contains duplicate option ids.")

    # Attach counts with a strict one-to-one relationship.
    metadata_columns = ["occ_id", "laureate_n"]
    v_member_count = config["member_count"]
    if v_member_count is not None:
        metadata_columns.append(str(v_member_count))
    df_options = df_options.merge(
        df_table[metadata_columns],
        on="occ_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if (df_options["_merge"] != "both").any():
        missing_id_list = df_options.loc[
            df_options["_merge"] != "both",
            "occ_id",
        ].tolist()
        raise ValueError(f"{level} options lack table metadata: {missing_id_list}.")
    df_options = df_options.drop(columns="_merge")

    # Detailed occupations always contain exactly one member.
    if v_member_count is None:
        df_options["member_count"] = 1
    else:
        df_options = df_options.rename(
            columns={str(v_member_count): "member_count"}
        )
    return df_options.sort_values("sort_order").reset_index(drop=True)


def build_level_payload(
    df_timeseries: pd.DataFrame,
    df_table: pd.DataFrame,
    level: str,
) -> dict:
    """Return options and rows for one occupation classification."""

    # Restrict to the requested level and attach its table metadata.
    df_level = df_timeseries.loc[df_timeseries["level"] == level].copy()
    if df_level.empty:
        raise ValueError(f"Time-series input contains no rows for {level}.")
    df_options = build_option_metadata(df_level, df_table, level)

    # Serialize option metadata in deterministic presentation order.
    option_list = []
    by_id_dict = {}
    for option in df_options.itertuples(index=False):
        occ_id = str(option.occ_id)
        option_list.append(
            {
                "id": occ_id,
                "label": str(option.occ_label),
                "sort_order": int(option.sort_order),
                "member_count": int(option.member_count),
                "laureate_n": int(option.laureate_n),
            }
        )

        # Emit one compact row for every configured decade.
        df_rows = df_level.loc[df_level["occ_id"] == occ_id].sort_values("year")
        row_list = []
        for row in df_rows[ROW_COLUMNS].itertuples(index=False):
            row_list.append(
                {
                    "year": int(row.year),
                    "income_rank": clean_number(row.income_rank),
                    "education_rank": clean_number(row.education_rank),
                    "sample_count": clean_number(row.sample_count),
                }
            )
        by_id_dict[occ_id] = {"rows": row_list}

    return {
        "label": str(LEVEL_CONFIG[level]["label"]),
        "options": option_list,
        "by_id": by_id_dict,
    }


def build_payload(
    df_timeseries: pd.DataFrame,
    table_dict: dict[str, pd.DataFrame],
) -> dict:
    """Return the complete occupation rank explorer JSON payload."""

    # Build each classification in the configured display order.
    levels_dict = {
        level: build_level_payload(df_timeseries, table_dict[level], level)
        for level in LEVEL_CONFIG
    }
    return {
        "meta": {
            "country": "USA",
            "year_min": 1850,
            "year_max": 1970,
            "rank_scale": [0, 100],
            "group_weight": "n_cohort_occ_raw",
        },
        "levels": levels_dict,
    }


def main() -> None:
    """Read synced inputs and write validated site-ready JSON."""

    # Build the complete payload before replacing any prior output.
    df_timeseries, table_dict = read_inputs()
    payload = build_payload(df_timeseries, table_dict)

    # Write standards-compliant JSON only after all shaping succeeds.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, ensure_ascii=False, indent=2, allow_nan=False)
        output_file.write("\n")

    option_n = sum(
        len(level_payload["options"])
        for level_payload in payload["levels"].values()
    )
    print(
        f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} "
        f"({option_n:,} options, {len(df_timeseries):,} rows)."
    )


if __name__ == "__main__":
    main()
