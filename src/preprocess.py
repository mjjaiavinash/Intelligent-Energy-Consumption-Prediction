"""
src/preprocess.py
=================
Reproducible data preprocessing pipeline for the Intelligent Energy Consumption
Prediction and Optimization project.

Transforms raw minute-level household electricity consumption data into
hourly aggregated ML features.

Workflow:
1. Load raw data from 'dataset/raw/household_power_consumption.txt'.
2. Parse and combine Date and Time columns into datetime index.
3. Handle missing ('?') and invalid measurements appropriately.
4. Resample/aggregate minute-level power measurements into hourly intervals.
5. Engineer temporal calendar features:
   - hour (0-23)
   - day (1-31)
   - day_of_week (0-6, Mon=0, Sun=6)
   - month (1-12)
   - weekend (0 or 1)
6. Engineer temporal lag and rolling features:
   - lag_1h_kwh (consumption 1 hour prior)
   - lag_24h_kwh (consumption 24 hours prior)
   - rolling_mean_24h_kwh (mean consumption over preceding 24 hours)
7. Assign target variable: energy_consumption_kwh.
8. Validate and compare against existing processed dataset.
9. Report differences without silently overwriting the verified dataset.
"""

import os
import sys
import time
import argparse
import pandas as pd
import numpy as np

# Default paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(BASE_DIR, "dataset", "raw", "household_power_consumption.txt")
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "dataset", "processed", "energy_consumption_ml_dataset.csv")

EXPECTED_COLUMNS = [
    "timestamp",
    "hour",
    "day",
    "day_of_week",
    "month",
    "weekend",
    "lag_1h_kwh",
    "lag_24h_kwh",
    "rolling_mean_24h_kwh",
    "avg_reactive_power",
    "avg_voltage",
    "avg_global_intensity",
    "sub_metering_1",
    "sub_metering_2",
    "sub_metering_3",
    "energy_consumption_kwh"
]


def load_raw_data(file_path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Load raw UCI Household Power Consumption dataset.
    Handles semicolon delimiter and '?' missing values.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw dataset file not found at: {file_path}")

    print(f"--> [1/7] Reading raw dataset from: {file_path}")
    t0 = time.time()
    df_raw = pd.read_csv(
        file_path,
        sep=";",
        na_values=["?"],
        low_memory=False
    )
    print(f"    Loaded {len(df_raw):,} raw records in {time.time() - t0:.2f}s")
    return df_raw


def parse_and_clean_raw(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Parse datetime and convert electrical measurement columns to numeric.
    """
    print("--> [2/7] Parsing datetime and coercing numeric measurements...")
    t0 = time.time()

    # Combine Date (DD/MM/YYYY) and Time (HH:MM:SS)
    df_raw["datetime"] = pd.to_datetime(
        df_raw["Date"] + " " + df_raw["Time"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    numeric_cols = [
        "Global_active_power",
        "Global_reactive_power",
        "Voltage",
        "Global_intensity",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3"
    ]

    for col in numeric_cols:
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

    # Drop any records with unparseable datetime
    df_clean = df_raw.dropna(subset=["datetime"]).copy()
    print(f"    Cleaned in {time.time() - t0:.2f}s")
    return df_clean


def aggregate_hourly(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Resample minute measurements to hourly means.
    Global_active_power is in kW; hourly mean represents energy in kWh.
    """
    print("--> [3/7] Aggregating minute records to hourly averages...")
    t0 = time.time()

    numeric_cols = [
        "Global_active_power",
        "Global_reactive_power",
        "Voltage",
        "Global_intensity",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3"
    ]

    hourly = df_clean.set_index("datetime")[numeric_cols].resample("1h").mean()
    # Drop hours where primary power measurement is completely missing
    hourly = hourly.dropna(subset=["Global_active_power"]).copy()
    print(f"    Produced {len(hourly):,} hourly intervals in {time.time() - t0:.2f}s")
    return hourly


def engineer_features(hourly: pd.DataFrame) -> pd.DataFrame:
    """
    Generate calendar features, historical lag features, and rolling statistics.
    Ensures strict temporal order to prevent data leakage.
    """
    print("--> [4/7] Engineering calendar, lag, and rolling features...")
    t0 = time.time()

    # Sort index chronologically
    hourly = hourly.sort_index()

    # Target variable (hourly active energy consumption in kWh)
    hourly["energy_consumption_kwh"] = hourly["Global_active_power"]

    # 1. Calendar Features
    hourly["timestamp"] = hourly.index.strftime("%Y-%m-%d %H:%M:%S")
    hourly["hour"] = hourly.index.hour
    hourly["day"] = hourly.index.day
    hourly["day_of_week"] = hourly.index.dayofweek
    hourly["month"] = hourly.index.month
    hourly["weekend"] = (hourly["day_of_week"] >= 5).astype(int)

    # 2. Historical Lag & Rolling Features (computed strictly from past hours)
    # lag_1h: consumption 1 hour prior
    hourly["lag_1h_kwh"] = hourly["energy_consumption_kwh"].shift(1)
    # lag_24h: consumption exactly 24 hours prior (same hour previous day)
    hourly["lag_24h_kwh"] = hourly["energy_consumption_kwh"].shift(24)
    # rolling_mean_24h: rolling average of past 24 hours (excluding target hour)
    hourly["rolling_mean_24h_kwh"] = hourly["energy_consumption_kwh"].shift(1).rolling(24).mean()

    # 3. Concurrent electrical measurements (retained for database analysis, excluded during ML forecast)
    hourly["avg_reactive_power"] = hourly["Global_reactive_power"]
    hourly["avg_voltage"] = hourly["Voltage"]
    hourly["avg_global_intensity"] = hourly["Global_intensity"]
    hourly["sub_metering_1"] = hourly["Sub_metering_1"]
    hourly["sub_metering_2"] = hourly["Sub_metering_2"]
    hourly["sub_metering_3"] = hourly["Sub_metering_3"]

    # Select ordered columns and drop initial warm-up NaNs from lag creation
    df_features = hourly[EXPECTED_COLUMNS].dropna().reset_index(drop=True)
    print(f"    Feature engineering complete in {time.time() - t0:.2f}s. Clean rows: {len(df_features):,}")
    return df_features


def compare_with_existing(
    new_df: pd.DataFrame,
    existing_path: str = PROCESSED_DATA_PATH
) -> dict:
    """
    Compare newly generated dataset against existing verified dataset.
    Reports row count, column alignment, timestamp overlap, and numeric differences.
    """
    print(f"\n--> [5/7] Comparing generated dataset with: {existing_path}")

    if not os.path.exists(existing_path):
        print("    [NOTICE] Existing processed file does not exist yet. No comparison required.")
        return {"status": "new_file"}

    existing_df = pd.read_csv(existing_path)

    new_rows, new_cols = new_df.shape
    ex_rows, ex_cols = existing_df.shape

    col_match = list(new_df.columns) == list(existing_df.columns)
    row_diff = new_rows - ex_rows

    print(f"    Existing dataset shape : ({ex_rows:,}, {ex_cols})")
    print(f"    Generated dataset shape: ({new_rows:,}, {new_cols})")
    print(f"    Columns match exactly  : {col_match}")
    print(f"    Row count difference   : {row_diff:+d} rows")

    # Check timestamp overlap
    ex_timestamps = set(existing_df["timestamp"])
    new_timestamps = set(new_df["timestamp"])
    overlap = len(ex_timestamps.intersection(new_timestamps))
    overlap_pct = (overlap / ex_rows) * 100

    print(f"    Timestamp overlap      : {overlap:,} / {ex_rows:,} ({overlap_pct:.2f}%)")

    # Numeric comparison on overlapping timestamps
    merged = pd.merge(
        existing_df[["timestamp", "energy_consumption_kwh"]],
        new_df[["timestamp", "energy_consumption_kwh"]],
        on="timestamp",
        suffixes=("_existing", "_new")
    )
    max_kwh_diff = np.abs(merged["energy_consumption_kwh_existing"] - merged["energy_consumption_kwh_new"]).max()
    print(f"    Max target absolute diff: {max_kwh_diff:.8f} kWh")

    return {
        "status": "compared",
        "col_match": col_match,
        "row_diff": row_diff,
        "overlap_pct": overlap_pct,
        "max_kwh_diff": max_kwh_diff,
        "existing_rows": ex_rows,
        "new_rows": new_rows
    }


def validate_dataset(df: pd.DataFrame) -> bool:
    """
    Validate dataset for missing values, column integrity, and sensible numerical ranges.
    """
    print("\n--> [6/7] Validating dataset integrity...")
    is_valid = True

    # Check nulls
    nulls = df.isnull().sum()
    if nulls.sum() > 0:
        print(f"    [WARNING] Found missing values:\n{nulls[nulls > 0]}")
        is_valid = False
    else:
        print("    [PASS] Zero missing values detected.")

    # Check columns
    if list(df.columns) != EXPECTED_COLUMNS:
        print("    [WARNING] Columns do not match expected ordering.")
        is_valid = False
    else:
        print(f"    [PASS] All {len(EXPECTED_COLUMNS)} columns present and correctly ordered.")

    # Check ranges
    if (df["hour"] < 0).any() or (df["hour"] > 23).any():
        print("    [WARNING] Hour outside 0-23 range.")
        is_valid = False
    if (df["energy_consumption_kwh"] < 0).any():
        print("    [WARNING] Negative energy consumption detected.")
        is_valid = False

    print(f"    [PASS] Energy consumption range: [{df['energy_consumption_kwh'].min():.3f}, {df['energy_consumption_kwh'].max():.3f}] kWh")
    return is_valid


def main():
    parser = argparse.ArgumentParser(
        description="Reproducible preprocessing pipeline for UCI Household Power Consumption dataset."
    )
    parser.add_argument(
        "--raw-path",
        default=RAW_DATA_PATH,
        help="Path to raw household_power_consumption.txt"
    )
    parser.add_argument(
        "--output-path",
        default=PROCESSED_DATA_PATH,
        help="Path to output processed CSV"
    )
    parser.add_argument(
        "--force-overwrite",
        action="store_true",
        help="Force overwrite existing processed dataset if set."
    )
    args = parser.parse_args()

    print("=" * 70)
    print("   INTELLIGENT ENERGY CONSUMPTION PREDICTION — PREPROCESSING PIPELINE")
    print("=" * 70)

    try:
        # 1. Load raw data
        df_raw = load_raw_data(args.raw_path)

        # 2. Parse and clean
        df_clean = parse_and_clean_raw(df_raw)

        # 3. Aggregate hourly
        hourly = aggregate_hourly(df_clean)

        # 4. Feature engineering
        df_processed = engineer_features(hourly)

        # 5. Compare with existing dataset
        comp = compare_with_existing(df_processed, args.output_path)

        # 6. Validate
        is_valid = validate_dataset(df_processed)

        # 7. Safe output handling
        print("\n--> [7/7] Output handling...")
        if not os.path.exists(args.output_path):
            df_processed.to_csv(args.output_path, index=False)
            print(f"    [SUCCESS] Saved processed dataset to: {args.output_path}")
        elif args.force_overwrite:
            df_processed.to_csv(args.output_path, index=False)
            print(f"    [SUCCESS] Overwrote processed dataset (--force-overwrite specified): {args.output_path}")
        else:
            print(f"    [SAFEGUARD] Existing processed file at '{args.output_path}' was preserved.")
            print("    The existing verified file remains unchanged to prevent unintended model divergence.")
            print("    To overwrite explicitly, re-run with '--force-overwrite'.")

        print("\n" + "=" * 70)
        print("          PREPROCESSING PIPELINE EXECUTION COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Preprocessing failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
