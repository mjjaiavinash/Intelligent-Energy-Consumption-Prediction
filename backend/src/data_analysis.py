"""
src/data_analysis.py
====================
Exploratory Data Analysis and Validation for Intelligent Energy Consumption Prediction.

Key operations performed:
1. Loads processed dataset (read-only).
2. Validates data dimensions, types, missing values, duplicates, and infinite values.
3. Computes summary statistics.
4. Parses timestamps as datetime for temporal ordering.
5. Generates an 'Energy Consumption over Time' visualization plot.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Define paths
DATA_PATH = os.path.join("dataset", "processed", "energy_consumption_ml_dataset.csv")
PLOTS_DIR = "plots"


def load_dataset(file_path: str = DATA_PATH) -> pd.DataFrame:
    """
    Load the processed energy consumption dataset into a Pandas DataFrame.
    Does not modify or overwrite the file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")
    
    print(f"--> Loading dataset from: {file_path}")
    df = pd.read_csv(file_path)
    return df


def validate_dataset(df: pd.DataFrame) -> None:
    """
    Perform dataset validation and display:
    - Shape
    - Column names
    - Data types
    - Missing values
    - Duplicate rows
    - Infinite values
    - Descriptive statistics
    """
    print("\n" + "=" * 60)
    print("           DATASET VALIDATION REPORT")
    print("=" * 60)

    # 1. Dataset Shape
    print(f"\n1. Shape: {df.shape[0]:,} rows, {df.shape[1]} columns")

    # 2. Column Names
    print("\n2. Column Names:")
    for idx, col in enumerate(df.columns, start=1):
        print(f"   {idx:2d}. {col}")

    # 3. Data Types
    print("\n3. Data Types:")
    print(df.dtypes.to_string())

    # 4. Missing Values
    print("\n4. Missing (Null/NaN) Values:")
    null_counts = df.isnull().sum()
    print(null_counts.to_string())
    total_nulls = null_counts.sum()
    print(f"   Total missing values: {total_nulls}")

    # 5. Duplicate Rows
    duplicates = df.duplicated().sum()
    print(f"\n5. Duplicate Rows: {duplicates}")

    # 6. Infinite Values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_counts = np.isinf(df[numeric_cols]).sum().sum()
    print(f"\n6. Infinite Values: {inf_counts}")

    # 7. Basic Statistics
    print("\n7. Descriptive Statistics for Numeric Features:")
    print(df.describe().T[['count', 'mean', 'std', 'min', '50%', 'max']].to_string())

    print("=" * 60)


def plot_energy_over_time(df: pd.DataFrame, output_dir: str = PLOTS_DIR) -> None:
    """
    Plot energy consumption over time using parsed datetime timestamps.
    Saves the figure to plots/energy_consumption_over_time.png.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "energy_consumption_over_time.png")

    print("\n--> Generating 'Energy Consumption over Time' plot...")

    # Ensure timestamp is parsed as datetime
    df_plot = df.copy()
    df_plot["timestamp"] = pd.to_datetime(df_plot["timestamp"])
    df_plot = df_plot.sort_values("timestamp")

    # Resample to daily average for clean, legible visualization across years
    daily_resampled = df_plot.set_index("timestamp")["energy_consumption_kwh"].resample("D").mean()

    plt.figure(figsize=(14, 6))
    plt.plot(daily_resampled.index, daily_resampled.values, color="#1f77b4", linewidth=1.2, alpha=0.9, label="Daily Mean Consumption")
    
    # 30-day moving average for trend line
    rolling_30d = daily_resampled.rolling(window=30, min_periods=1).mean()
    plt.plot(rolling_30d.index, rolling_30d.values, color="#ff7f0e", linewidth=2.0, label="30-Day Moving Average Trend")

    plt.title("Household Energy Consumption Over Time (2006 - 2010)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Energy Consumption (kWh)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right", fontsize=11)
    plt.tight_layout()

    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"--> Saved plot to: {output_path}")


def main():
    """Main execution function for data analysis."""
    df = load_dataset()
    validate_dataset(df)
    plot_energy_over_time(df)
    print("\n[SUCCESS] Data analysis and validation completed successfully.\n")


if __name__ == "__main__":
    main()
