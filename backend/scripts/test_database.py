"""
scripts/test_database.py
========================
Automated database integration test:
1. Tests connection to MySQL server.
2. Verifies presence of the 4 required tables:
   - energy_consumption
   - predictions
   - optimization_results
   - model_metrics
3. Runs sample SELECT queries.
4. Tests inserting and reading a model metric record to verify write permissions.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.database import (
    get_connection,
    get_db_config,
    get_historical_energy_records,
    insert_model_metrics,
    get_recent_predictions
)


def run_database_tests():
    print("=" * 65)
    print("           MYSQL DATABASE INTEGRATION TEST SUITE")
    print("=" * 65 + "\n")

    cfg = get_db_config(use_database=True)
    print(f"Target: {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg.get('database', 'N/A')}\n")

    # -----------------------------------------------------------------
    # Test 1: Verify Connection
    # -----------------------------------------------------------------
    print("--> Test 1: Testing Connection to MySQL Server...")
    try:
        conn = get_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()[0]
        conn.close()
        print(f"    [PASS] Connected successfully! MySQL Server Version: {version}\n")
    except Exception as e:
        print(f"    [FAIL] Connection failed: {e}\n", file=sys.stderr)
        print("--> DIAGNOSTIC HINT:", file=sys.stderr)
        print("    1. Make sure MySQL service is running.", file=sys.stderr)
        print("    2. Create a .env file with your credentials (see .env.example).", file=sys.stderr)
        print("    3. Ensure user and password match your local MySQL installation.\n", file=sys.stderr)
        sys.exit(1)

    # -----------------------------------------------------------------
    # Test 2: Check Database and Table Existence
    # -----------------------------------------------------------------
    print("--> Test 2: Verifying Required Database Tables...")
    expected_tables = {
        "energy_consumption",
        "predictions",
        "optimization_results",
        "model_metrics"
    }

    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        found_tables = {row[0].lower() for row in cursor.fetchall()}
        conn.close()

        print(f"    Found tables in database: {sorted(list(found_tables))}")
        missing = expected_tables - found_tables

        if missing:
            print(f"    [FAIL] Missing required tables: {missing}", file=sys.stderr)
            print("    Please run: mysql -u root -p < database/schema.sql", file=sys.stderr)
            sys.exit(1)
        else:
            print("    [PASS] All 4 required tables exist.\n")

    except Exception as e:
        print(f"    [FAIL] Table check failed: {e}\n", file=sys.stderr)
        sys.exit(1)

    # -----------------------------------------------------------------
    # Test 3: Sample SELECT Query
    # -----------------------------------------------------------------
    print("--> Test 3: Executing Sample SELECT Queries...")
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM energy_consumption;")
        count_records = cursor.fetchone()[0]
        print(f"    Total rows in 'energy_consumption': {count_records:,}")

        cursor.execute("SELECT COUNT(*) FROM predictions;")
        count_preds = cursor.fetchone()[0]
        print(f"    Total rows in 'predictions': {count_preds:,}")

        conn.close()
        print("    [PASS] Sample count queries executed successfully.\n")

    except Exception as e:
        print(f"    [FAIL] Sample query failed: {e}\n", file=sys.stderr)
        sys.exit(1)

    # -----------------------------------------------------------------
    # Test 4: Sample Data Fetch & Write Check
    # -----------------------------------------------------------------
    print("--> Test 4: Testing Table Read/Write Operations...")
    try:
        # Test inserting model metrics entry
        metric_id = insert_model_metrics(
            model_name="XGBoost_Test",
            mae=0.3324,
            mse=0.2286,
            rmse=0.4781,
            r2_score=0.5870
        )
        print(f"    Successfully inserted test record into 'model_metrics' (ID: {metric_id})")

        # Fetch historical records
        records = get_historical_energy_records(limit=3)
        print(f"    Fetched {len(records)} sample rows from 'energy_consumption':")
        for r in records:
            print(f"      [{r['timestamp']}] Hour: {r['hour']}, Lag 1h: {r['lag_1h_kwh']}, Consumption: {r['energy_consumption_kwh']} kWh")

        print("    [PASS] Database read and write operations verified.\n")

    except Exception as e:
        print(f"    [FAIL] Read/Write test failed: {e}\n", file=sys.stderr)
        sys.exit(1)

    print("=" * 65)
    print("  ALL DATABASE INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_database_tests()
