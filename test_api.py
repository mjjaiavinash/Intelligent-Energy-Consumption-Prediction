"""
test_api.py
===========
Automated test suite verifying the FastAPI endpoints for Energy Consumption Prediction:
1. Verifies model loading on startup.
2. Tests GET /health endpoint.
3. Tests POST /predict with valid forecasting feature payload.
4. Tests POST /predict with invalid and missing inputs (ensuring validation errors).
"""

import sys
from fastapi.testclient import TestClient
from api.main import app, ml_state


def run_tests():
    print("=" * 65)
    print("         RUNNING FASTAPI PREDICTION BACKEND TESTS")
    print("=" * 65 + "\n")

    passed_tests = 0
    total_tests = 9

    # TestClient invokes lifespan handlers (startup and shutdown)
    with TestClient(app) as client:

        # -------------------------------------------------------------
        # Test 1: Verify Model Loading
        # -------------------------------------------------------------
        print("--> Test 1: Verify Model Loading at Startup")
        assert ml_state["is_loaded"] is True, "Model is not marked as loaded in ml_state."
        assert ml_state["model"] is not None, "Model object is None."
        assert len(ml_state["feature_names"]) == 8, f"Expected 8 features, got {len(ml_state['feature_names'])}."
        print(f"    [PASS] Model '{ml_state['model_name']}' loaded with features: {ml_state['feature_names']}\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 2: GET /health Endpoint
        # -------------------------------------------------------------
        print("--> Test 2: GET /health Endpoint")
        health_resp = client.get("/health")
        print(f"    Status Code: {health_resp.status_code}")
        print(f"    Response JSON: {health_resp.json()}")
        assert health_resp.status_code == 200, f"Expected 200, got {health_resp.status_code}"
        health_data = health_resp.json()
        assert health_data["status"] == "healthy"
        assert health_data["model_loaded"] is True
        assert health_data["model_name"] == "XGBoost"
        assert health_data["features_count"] == 8
        print("    [PASS] Health endpoint returned healthy status with model confirmation.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 3: POST /predict with Valid Input
        # -------------------------------------------------------------
        print("--> Test 3: POST /predict with Valid Payload")
        valid_payload = {
            "hour": 18,
            "day": 26,
            "day_of_week": 4,   # Friday
            "month": 11,        # November
            "weekend": 0,
            "lag_1h_kwh": 2.15,
            "lag_24h_kwh": 1.95,
            "rolling_mean_24h_kwh": 1.45
        }
        predict_resp = client.post("/predict", json=valid_payload)
        print(f"    Status Code: {predict_resp.status_code}")
        print(f"    Response JSON: {predict_resp.json()}")
        assert predict_resp.status_code == 200, f"Expected 200, got {predict_resp.status_code}"
        pred_data = predict_resp.json()
        assert "predicted_energy_kwh" in pred_data
        assert pred_data["model_name"] == "XGBoost"
        assert pred_data["predicted_energy_kwh"] > 0
        assert pred_data["unit"] == "kWh"
        print(f"    [PASS] Forecast successfully generated: {pred_data['predicted_energy_kwh']} kWh\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 4: POST /predict with Out-of-Range Inputs (Validation)
        # -------------------------------------------------------------
        print("--> Test 4: POST /predict with Invalid Out-of-Range Field (hour=25, month=15)")
        invalid_payload = {
            "hour": 25,          # Invalid: hour must be 0-23
            "day": 26,
            "day_of_week": 4,
            "month": 15,         # Invalid: month must be 1-12
            "weekend": 0,
            "lag_1h_kwh": 2.15,
            "lag_24h_kwh": 1.95,
            "rolling_mean_24h_kwh": 1.45
        }
        invalid_resp = client.post("/predict", json=invalid_payload)
        print(f"    Status Code: {invalid_resp.status_code} (Expected 422 Unprocessable Entity)")
        assert invalid_resp.status_code == 422, f"Expected 422 for invalid values, got {invalid_resp.status_code}"
        print("    [PASS] Pydantic correctly rejected out-of-range input fields.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 5: POST /predict with Missing Required Input Field
        # -------------------------------------------------------------
        print("--> Test 5: POST /predict with Missing Required Field ('lag_1h_kwh')")
        missing_payload = {
            "hour": 18,
            "day": 26,
            "day_of_week": 4,
            "month": 11,
            "weekend": 0,
            # lag_1h_kwh intentionally omitted
            "lag_24h_kwh": 1.95,
            "rolling_mean_24h_kwh": 1.45
        }
        missing_resp = client.post("/predict", json=missing_payload)
        print(f"    Status Code: {missing_resp.status_code} (Expected 422 Unprocessable Entity)")
        assert missing_resp.status_code == 422, f"Expected 422 for missing field, got {missing_resp.status_code}"
        print("    [PASS] Pydantic correctly rejected incomplete input payload.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 6: GET /energy/summary
        # -------------------------------------------------------------
        print("--> Test 6: GET /energy/summary Endpoint")
        sum_resp = client.get("/energy/summary")
        assert sum_resp.status_code == 200, f"Expected 200, got {sum_resp.status_code}"
        sum_data = sum_resp.json()
        assert "average_consumption" in sum_data
        assert "total_records" in sum_data
        assert sum_data["total_records"] > 0
        print(f"    [PASS] Summary retrieved: {sum_data['total_records']:,} records, Avg: {sum_data['average_consumption']} kWh\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 7: GET /energy/history
        # -------------------------------------------------------------
        print("--> Test 7: GET /energy/history Endpoint")
        hist_resp = client.get("/energy/history?limit=10&order=desc")
        assert hist_resp.status_code == 200, f"Expected 200, got {hist_resp.status_code}"
        hist_data = hist_resp.json()
        assert len(hist_data) == 10
        assert "energy_consumption_kwh" in hist_data[0]
        print(f"    [PASS] History retrieved {len(hist_data)} rows. Latest: {hist_data[0]['timestamp']} -> {hist_data[0]['energy_consumption_kwh']} kWh\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 8: GET /predictions
        # -------------------------------------------------------------
        print("--> Test 8: GET /predictions Endpoint")
        preds_resp = client.get("/predictions?limit=5")
        assert preds_resp.status_code == 200, f"Expected 200, got {preds_resp.status_code}"
        preds_data = preds_resp.json()
        print(f"    [PASS] Predictions retrieved: {len(preds_data)} records\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # Test 9: GET /optimization-results
        # -------------------------------------------------------------
        print("--> Test 9: GET /optimization-results Endpoint")
        opts_resp = client.get("/optimization-results?limit=5")
        assert opts_resp.status_code == 200, f"Expected 200, got {opts_resp.status_code}"
        opts_data = opts_resp.json()
        print(f"    [PASS] Optimization results retrieved: {len(opts_data)} records\n")
        passed_tests += 1

    print("=" * 65)
    print(f"  ALL {passed_tests}/{total_tests} TESTS PASSED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n[TEST FAILED]: {str(e)}", file=sys.stderr)
        sys.exit(1)
