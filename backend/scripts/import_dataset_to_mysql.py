"""
scripts/import_dataset_to_mysql.py
==================================
Batch importer script transferring processed ML energy records into MySQL.

Key features:
1. Reads 'dataset/processed/energy_consumption_ml_dataset.csv' without modifying it.
2. Extracts the relevant columns for the 'energy_consumption' table.
3. Batches inserts (1,000 rows per batch) for optimal throughput and memory safety.
4. Uses ON DUPLICATE KEY UPDATE to safely handle duplicate timestamps.
5. Tracks and displays progress, successful inserts, and errors.
"""

import os
import sys
import time
import pandas as pd
from dotenv import load_dotenv

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.database import get_connection, insert_energy_records, init_db

DATA_PATH = os.path.join(BASE_DIR, "dataset", "processed", "energy_consumption_ml_dataset.csv")
BATCH_SIZE = 1000


def import_csv_to_mysql(csv_path: str = DATA_PATH, batch_size: int = BATCH_SIZE):
    """
    Read the processed CSV and batch-insert records into MySQL energy_consumption table.
    """
    print("=" * 65)
    print("      DATASET IMPORT TO MYSQL (energy_consumption)")
    print("=" * 65 + "\n")

    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV dataset file not found at: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Verify MySQL connection and ensure tables exist
    print("--> Checking MySQL connection and verifying database schema...")
    try:
        init_db(os.path.join(BASE_DIR, "database", "schema.sql"))
    except Exception as e:
        print(f"[ERROR] Failed to connect to MySQL or initialize database: {e}", file=sys.stderr)
        print("Please check your .env file or environment variables.", file=sys.stderr)
        sys.exit(1)

    # 2. Read processed CSV without altering it
    print(f"--> Reading processed dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    total_rows = len(df)
    print(f"    Total rows found in CSV: {total_rows:,}")

    # 3. Format records for database insertion
    # Ensure column compatibility
    required_cols = [
        "timestamp", "hour", "day", "day_of_week", "month", "weekend",
        "lag_1h_kwh", "lag_24h_kwh", "rolling_mean_24h_kwh", "energy_consumption_kwh"
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"[ERROR] CSV is missing expected columns: {missing_cols}", file=sys.stderr)
        sys.exit(1)

    df_subset = df[required_cols].copy()
    # Format timestamp to ISO string
    df_subset["timestamp"] = pd.to_datetime(df_subset["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    # Cast integers and floats cleanly
    df_subset["weekend"] = df_subset["weekend"].astype(int)

    records = df_subset.to_dict(orient="records")

    # 4. Batch insertion
    print(f"--> Starting batch insertion into MySQL ({batch_size} rows per batch)...")
    start_time = time.time()
    successful = 0
    failed = 0

    query = """
        INSERT INTO energy_consumption (
            timestamp, hour, day, day_of_week, month, weekend,
            lag_1h_kwh, lag_24h_kwh, rolling_mean_24h_kwh, energy_consumption_kwh
        ) VALUES (
            %(timestamp)s, %(hour)s, %(day)s, %(day_of_week)s, %(month)s, %(weekend)s,
            %(lag_1h_kwh)s, %(lag_24h_kwh)s, %(rolling_mean_24h_kwh)s, %(energy_consumption_kwh)s
        )
        ON DUPLICATE KEY UPDATE
            hour = VALUES(hour),
            day = VALUES(day),
            day_of_week = VALUES(day_of_week),
            month = VALUES(month),
            weekend = VALUES(weekend),
            lag_1h_kwh = VALUES(lag_1h_kwh),
            lag_24h_kwh = VALUES(lag_24h_kwh),
            rolling_mean_24h_kwh = VALUES(rolling_mean_24h_kwh),
            energy_consumption_kwh = VALUES(energy_consumption_kwh);
    """

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor()
        for idx in range(0, total_rows, batch_size):
            batch = records[idx:idx + batch_size]
            try:
                cursor.executemany(query, batch)
                conn.commit()
                successful += len(batch)
            except Exception as batch_err:
                print(f"\n    [WARN] Error at batch {idx}-{idx+len(batch)}: {batch_err}")
                conn.rollback()
                failed += len(batch)

            # Progress display
            progress = (successful + failed) / total_rows * 100
            bar_len = 30
            filled_len = int(bar_len * (successful + failed) // total_rows)
            bar = "=" * filled_len + "-" * (bar_len - filled_len)
            print(f"\r    [{bar}] {progress:5.1f}% | Processed: {successful + failed:,}/{total_rows:,} rows", end="", flush=True)

        print()  # Newline after progress bar
    finally:
        conn.close()

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print("                 IMPORT SUMMARY REPORT")
    print("=" * 65)
    print(f"Total Rows Processed : {total_rows:,}")
    print(f"Successful Records   : {successful:,}")
    print(f"Failed Records       : {failed:,}")
    print(f"Time Taken           : {elapsed:.2f} seconds")
    print(f"Average Speed        : {successful / max(elapsed, 0.001):.1f} rows/sec")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    import_csv_to_mysql()
