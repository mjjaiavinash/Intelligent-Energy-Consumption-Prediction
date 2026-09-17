"""
scripts/test_optimization.py
============================
Automated test suite verifying the Phase 4 Data-Driven Energy Optimization Engine:
1. Historical baseline calculation (actual MySQL records).
2. Excess consumption calculation.
3. Saving percentage calculation.
4. Normal consumption classification.
5. High consumption classification.
6. Peak consumption classification.
7. Recommendation generation.
8. Database insertion into optimization_results.
9. API /optimize endpoint (using FastAPI TestClient).
10. Invalid input handling.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from api.main import app, ml_state
from src.database import get_connection, insert_prediction
from src.optimization import (
    calculate_historical_baseline,
    calculate_excess_consumption,
    calculate_saving_percentage,
    classify_consumption,
    generate_recommendation,
    optimize_prediction
)


def run_tests():
    print("=" * 65)
    print("      PHASE 4: ENERGY OPTIMIZATION ENGINE TEST SUITE")
    print("=" * 65 + "\n")

    passed_tests = 0
    total_tests = 10

    # -------------------------------------------------------------
    # Test 1: Historical Baseline Calculation (from MySQL records)
    # -------------------------------------------------------------
    print("--> Test 1: Historical Baseline Calculation (Actual MySQL Data)")
    baseline_info = calculate_historical_baseline(hour=18, day_of_week=4, weekend=0)
    print(f"    Baseline for Friday 6 PM (hour=18):")
    print(f"    - Baseline Consumption : {baseline_info['baseline_kwh']} kWh")
    print(f"    - Standard Deviation   : {baseline_info['std_dev']} kWh")
    print(f"    - Actual Historical Rows Evaluated : {baseline_info['sample_count']}")

    assert baseline_info["baseline_kwh"] > 0, "Baseline kWh should be positive."
    assert baseline_info["sample_count"] > 10, "Expected at least 10 historical records from MySQL."
    assert baseline_info["std_dev"] >= 0, "Standard deviation must be non-negative."
    print("    [PASS] Historical baseline derived from actual MySQL records.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 2: Excess Consumption Calculation
    # -------------------------------------------------------------
    print("--> Test 2: Excess Consumption Calculation")
    excess_high = calculate_excess_consumption(predicted_consumption=3.5, baseline_consumption=2.0)
    excess_low = calculate_excess_consumption(predicted_consumption=1.8, baseline_consumption=2.0)
    assert excess_high == 1.5, f"Expected 1.5, got {excess_high}"
    assert excess_low == 0.0, f"Expected 0.0, got {excess_low}"
    print(f"    Predicted 3.5 kWh vs Baseline 2.0 kWh -> Excess: {excess_high} kWh")
    print(f"    Predicted 1.8 kWh vs Baseline 2.0 kWh -> Excess: {excess_low} kWh")
    print("    [PASS] Excess consumption accurately calculated.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 3: Saving Percentage Calculation
    # -------------------------------------------------------------
    print("--> Test 3: Saving Percentage Calculation")
    saving_pct_pos = calculate_saving_percentage(predicted_consumption=3.5, excess_consumption=1.5)
    saving_pct_zero = calculate_saving_percentage(predicted_consumption=2.0, excess_consumption=0.0)
    assert saving_pct_pos == 42.86, f"Expected 42.86%, got {saving_pct_pos}%"
    assert saving_pct_zero == 0.0, f"Expected 0.0%, got {saving_pct_zero}%"
    print(f"    Predicted 3.5 kWh with 1.5 kWh excess -> Saving: {saving_pct_pos}%")
    print(f"    Predicted 2.0 kWh with 0.0 kWh excess -> Saving: {saving_pct_zero}%")
    print("    [PASS] Saving percentage logic verified.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 4: Normal Consumption Classification
    # -------------------------------------------------------------
    print("--> Test 4: Normal Consumption Classification")
    status_normal = classify_consumption(predicted_consumption=1.05, baseline_consumption=1.0, std_dev=0.2)
    assert status_normal == "NORMAL", f"Expected NORMAL, got {status_normal}"
    print(f"    Predicted 1.05 kWh vs Baseline 1.0 kWh (std=0.2) -> Classification: {status_normal}")
    print("    [PASS] Normal tier correctly classified.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 5: High Consumption Classification
    # -------------------------------------------------------------
    print("--> Test 5: High Consumption Classification")
    status_high = classify_consumption(predicted_consumption=1.25, baseline_consumption=1.0, std_dev=0.2)
    assert status_high == "HIGH", f"Expected HIGH, got {status_high}"
    print(f"    Predicted 1.25 kWh vs Baseline 1.0 kWh (std=0.2) -> Classification: {status_high}")
    print("    [PASS] High tier correctly classified.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 6: Peak Consumption Classification
    # -------------------------------------------------------------
    print("--> Test 6: Peak Consumption Classification")
    status_peak = classify_consumption(predicted_consumption=1.60, baseline_consumption=1.0, std_dev=0.2)
    assert status_peak == "PEAK", f"Expected PEAK, got {status_peak}"
    print(f"    Predicted 1.60 kWh vs Baseline 1.0 kWh (std=0.2) -> Classification: {status_peak}")
    print("    [PASS] Peak tier correctly classified.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 7: Recommendation Generation
    # -------------------------------------------------------------
    print("--> Test 7: Recommendation Generation")
    rec_normal = generate_recommendation("NORMAL", excess_consumption=0.0, saving_percentage=0.0)
    rec_high = generate_recommendation("HIGH", excess_consumption=0.35, saving_percentage=22.5)
    rec_peak = generate_recommendation("PEAK", excess_consumption=1.20, saving_percentage=45.0)

    assert "normal" in rec_normal.lower()
    assert "flexible energy usage" in rec_high.lower()
    assert "shifting flexible loads" in rec_peak.lower()
    print(f"    [NORMAL Recommendation]: {rec_normal}")
    print(f"    [HIGH Recommendation]  : {rec_high}")
    print(f"    [PEAK Recommendation]  : {rec_peak}")
    print("    [PASS] Understandable and conservative recommendations generated.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 8: Database Insertion into optimization_results
    # -------------------------------------------------------------
    print("--> Test 8: Database Insertion into optimization_results")
    # Log a dummy prediction record first to test foreign key relationship
    dummy_pred_id = insert_prediction(
        predicted_energy_kwh=2.85,
        model_name="XGBoost_Opt_Test"
    )
    opt_dict = optimize_prediction(
        predicted_consumption=2.85,
        hour=18,
        day_of_week=4,
        weekend=0,
        prediction_id=dummy_pred_id,
        save_to_db=True
    )
    assert opt_dict["id"] is not None and opt_dict["id"] > 0, "Failed to persist optimization result."
    print(f"    Saved optimization record ID: {opt_dict['id']} (Linked to prediction_id: {dummy_pred_id})")

    # Verify query back from database
    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM optimization_results WHERE id = %s;", (opt_dict["id"],))
        db_row = cursor.fetchone()
        assert db_row is not None, "Could not retrieve persisted optimization record from MySQL."
        assert float(db_row["predicted_consumption"]) == 2.85
        assert float(db_row["baseline_consumption"]) == opt_dict["baseline_consumption"]
        print(f"    Verified from MySQL: ID={db_row['id']}, Pred={db_row['predicted_consumption']}, Base={db_row['baseline_consumption']}")
    finally:
        conn.close()

    print("    [PASS] Database insertion and foreign key persistence verified.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 9: API /optimize Endpoint
    # -------------------------------------------------------------
    print("--> Test 9: API POST /optimize Endpoint")
    with TestClient(app) as client:
        # A. Test direct prediction & optimization
        payload_direct = {
            "predicted_consumption": 2.85,
            "hour": 18,
            "day_of_week": 4,
            "weekend": 0
        }
        resp = client.post("/optimize", json=payload_direct)
        print(f"    Direct Payload Status: {resp.status_code}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"    Response JSON:\n    {data}")
        assert "baseline_consumption" in data
        assert "excess_consumption" in data
        assert "status" in data
        assert data["status"] in ["NORMAL", "HIGH", "PEAK"]

        # B. Test end-to-end features payload
        payload_features = {
            "features": {
                "hour": 18,
                "day": 26,
                "day_of_week": 4,
                "month": 11,
                "weekend": 0,
                "lag_1h_kwh": 2.15,
                "lag_24h_kwh": 1.95,
                "rolling_mean_24h_kwh": 1.45
            }
        }
        resp_feat = client.post("/optimize", json=payload_features)
        print(f"    Features Payload Status: {resp_feat.status_code}")
        assert resp_feat.status_code == 200, f"Expected 200, got {resp_feat.status_code}: {resp_feat.text}"
        data_feat = resp_feat.json()
        assert data_feat["prediction_id"] is not None
        print(f"    End-to-End Optimize Response: Pred ID={data_feat['prediction_id']}, Status={data_feat['status']}, Saving={data_feat['saving_percentage']}%")

    print("    [PASS] API /optimize endpoint successfully tested for direct and end-to-end requests.\n")
    passed_tests += 1

    # -------------------------------------------------------------
    # Test 10: Invalid Input Handling
    # -------------------------------------------------------------
    print("--> Test 10: Invalid Input Handling")
    with TestClient(app) as client:
        # Missing hour when providing predicted_consumption
        bad_payload = {"predicted_consumption": 2.5}
        resp_bad = client.post("/optimize", json=bad_payload)
        assert resp_bad.status_code == 422, f"Expected 422, got {resp_bad.status_code}"
        print("    [Sub-test A] Correctly rejected predicted_consumption without hour (HTTP 422).")

        # Empty payload
        resp_empty = client.post("/optimize", json={})
        assert resp_empty.status_code == 422, f"Expected 422, got {resp_empty.status_code}"
        print("    [Sub-test B] Correctly rejected empty payload (HTTP 422).")

        # Invalid hour out of bounds (hour=25)
        bad_hour = {"predicted_consumption": 2.5, "hour": 25}
        resp_hour = client.post("/optimize", json=bad_hour)
        assert resp_hour.status_code == 422, f"Expected 422 for hour=25, got {resp_hour.status_code}"
        print("    [Sub-test C] Correctly rejected out-of-bounds hour (HTTP 422).")

    # Function-level exception check
    try:
        calculate_historical_baseline(hour=99)
        assert False, "Should have raised ValueError for hour=99"
    except ValueError:
        print("    [Sub-test D] calculate_historical_baseline correctly raised ValueError for hour=99.")

    print("    [PASS] All invalid inputs safely handled and rejected.\n")
    passed_tests += 1

    print("=" * 65)
    print(f"  ALL {passed_tests}/{total_tests} PHASE 4 TESTS PASSED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as err:
        print(f"\n[TEST FAILED]: {str(err)}", file=sys.stderr)
        sys.exit(1)
