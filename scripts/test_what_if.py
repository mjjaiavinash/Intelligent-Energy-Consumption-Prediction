"""
scripts/test_what_if.py
=======================
Phase 6 - What-If Energy Consumption Simulation: Automated Test Suite

Tests (14 total):
  1.  Valid base/scenario prediction (lower scenario)
  2.  Lower-consumption scenario verification
  3.  Higher-consumption scenario verification
  4.  Equal/identical scenario (difference ~ 0)
  5.  Percentage change calculation accuracy
  6.  Zero base prediction safe handling
  7.  Invalid hour value (expect HTTP 422)
  8.  Invalid month value (expect HTTP 422)
  9.  Missing required feature (expect HTTP 422)
  10. Extra/unknown feature is ignored by Pydantic
  11. Base status classification (NORMAL / HIGH / PEAK)
  12. Scenario status classification
  13. Interpretation text generation (not empty, uses 'predicted')
  14. Full /what-if API endpoint round-trip test

Run with both FastAPI and MySQL running:
  python scripts/test_what_if.py

Requirements: requests library (pip install requests)
"""

import sys
import os
import json

try:
    import requests
except ImportError:
    print("[ERROR] requests library is required: pip install requests")
    sys.exit(1)

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

_test_client = None

def get_test_client():
    global _test_client
    if _test_client is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        from fastapi.testclient import TestClient
        from api.main import app, load_artifacts
        load_artifacts()
        _test_client = TestClient(app)
    return _test_client

PASS = "PASS"
FAIL = "FAIL"

results = []
total = 0
passed = 0


def record(name, ok, detail=""):
    global total, passed
    total += 1
    tag = PASS if ok else FAIL
    if ok:
        passed += 1
    results.append((tag, name, detail))
    mark = "OK" if ok else "XX"
    print(f"  [{tag}]  {mark}  {name}")
    if detail:
        print(f"          -> {detail}")


_use_live = None

def check_live_server():
    global _use_live
    if _use_live is None:
        try:
            r = requests.get(f"{API_BASE}/health", timeout=0.5)
            _use_live = (r.status_code == 200)
        except Exception:
            _use_live = False
    return _use_live

def post_what_if(payload):
    """Helper: POST /what-if. Tries live server; falls back to FastAPI TestClient."""
    if check_live_server():
        try:
            return requests.post(f"{API_BASE}/what-if", json=payload, timeout=5)
        except Exception:
            pass
    client = get_test_client()
    return client.post("/what-if", json=payload)


# ---------------------------------------------------------------------------
# BASE FEATURE SETS
# ---------------------------------------------------------------------------

VALID_BASE = {
    "hour": 18,
    "day": 26,
    "day_of_week": 4,
    "month": 11,
    "weekend": 0,
    "lag_1h_kwh": 1.6593,
    "lag_24h_kwh": 1.5735,
    "rolling_mean_24h_kwh": 1.7259
}

# Lower scenario: earlier hour, reduced lags
LOWER_SCENARIO = {
    "hour": 6,
    "day": 26,
    "day_of_week": 4,
    "month": 11,
    "weekend": 0,
    "lag_1h_kwh": 0.30,
    "lag_24h_kwh": 0.40,
    "rolling_mean_24h_kwh": 0.50
}

# Higher scenario: late-night high-lag conditions
HIGHER_SCENARIO = {
    "hour": 20,
    "day": 26,
    "day_of_week": 4,
    "month": 11,
    "weekend": 0,
    "lag_1h_kwh": 5.0,
    "lag_24h_kwh": 4.5,
    "rolling_mean_24h_kwh": 4.0
}


def separator(label):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print('=' * 60)


# ---------------------------------------------------------------------------
# TEST 1 - Valid base/scenario (lower scenario)
# ---------------------------------------------------------------------------
separator("Tests 1-6: Prediction & Math")

payload_lower = {
    "base_features": VALID_BASE,
    "scenario_features": LOWER_SCENARIO
}

resp1 = post_what_if(payload_lower)
ok1 = resp1.status_code == 200
if ok1:
    d1 = resp1.json()
    record("1. Valid base/scenario returns 200", True,
           f"base={d1['base_prediction_kwh']} kWh, scenario={d1['scenario_prediction_kwh']} kWh")
else:
    d1 = {}
    record("1. Valid base/scenario returns 200", False, f"HTTP {resp1.status_code}: {resp1.text[:120]}")

# ---------------------------------------------------------------------------
# TEST 2 - Lower-consumption scenario
# ---------------------------------------------------------------------------
ok2 = ok1 and (d1.get("scenario_prediction_kwh", 0) < d1.get("base_prediction_kwh", 0))
record("2. Lower scenario predicts less than base",
       ok2,
       f"diff={d1.get('difference_kwh', '?')} kWh" if ok1 else "skipped (test 1 failed)")

# ---------------------------------------------------------------------------
# TEST 3 - Higher-consumption scenario
# ---------------------------------------------------------------------------
payload_higher = {"base_features": VALID_BASE, "scenario_features": HIGHER_SCENARIO}
resp3 = post_what_if(payload_higher)
ok3_http = resp3.status_code == 200
d3 = resp3.json() if ok3_http else {}
ok3 = ok3_http and d3.get("scenario_prediction_kwh", 0) > d3.get("base_prediction_kwh", 0)
record("3. Higher scenario predicts more than base",
       ok3,
       f"base={d3.get('base_prediction_kwh', '?')}, scenario={d3.get('scenario_prediction_kwh', '?')} kWh")

# ---------------------------------------------------------------------------
# TEST 4 - Equal / identical scenario (difference ~0)
# ---------------------------------------------------------------------------
payload_equal = {"base_features": VALID_BASE, "scenario_features": VALID_BASE}
resp4 = post_what_if(payload_equal)
ok4_http = resp4.status_code == 200
d4 = resp4.json() if ok4_http else {}
ok4 = ok4_http and abs(d4.get("difference_kwh", 1.0)) < 0.0001
record("4. Identical scenarios -> difference ~ 0",
       ok4,
       f"difference={d4.get('difference_kwh', '?')} kWh")

# ---------------------------------------------------------------------------
# TEST 5 - Percentage change calculation accuracy
# ---------------------------------------------------------------------------
if ok1:
    base_k = d1["base_prediction_kwh"]
    scen_k = d1["scenario_prediction_kwh"]
    reported_pct = d1.get("percentage_change", None)
    if base_k > 0 and reported_pct is not None:
        expected_pct = round(((scen_k - base_k) / base_k) * 100.0, 2)
        ok5 = abs(reported_pct - expected_pct) < 0.05
        record("5. Percentage change calculation is accurate",
               ok5,
               f"reported={reported_pct}%, expected={expected_pct}%")
    else:
        record("5. Percentage change calculation is accurate", False,
               "base_prediction_kwh=0 or percentage_change missing")
else:
    record("5. Percentage change calculation is accurate", False, "skipped (test 1 failed)")

# ---------------------------------------------------------------------------
# TEST 6 - Zero base prediction safe handling
#          Use a near-zero but valid lag to attempt approaching 0 output
# ---------------------------------------------------------------------------
near_zero_base = {
    "hour": 3,
    "day": 1,
    "day_of_week": 0,
    "month": 7,
    "weekend": 0,
    "lag_1h_kwh": 0.0,
    "lag_24h_kwh": 0.0,
    "rolling_mean_24h_kwh": 0.0
}
payload_zero = {"base_features": near_zero_base, "scenario_features": VALID_BASE}
resp6 = post_what_if(payload_zero)
ok6 = resp6.status_code == 200  # Must not crash regardless of base value
d6 = resp6.json() if ok6 else {}
pct6 = d6.get("percentage_change", None)
# If base happens to be 0, percentage_change should be 0.0 (safe)
ok6_safe = ok6 and pct6 is not None
record("6. Near-zero base does not crash API",
       ok6_safe,
       f"base={d6.get('base_prediction_kwh', '?')} kWh, pct_change={pct6}")

# ---------------------------------------------------------------------------
# Tests 7-10: Validation
# ---------------------------------------------------------------------------
separator("Tests 7-10: Input Validation")

# TEST 7 - Invalid hour
bad_hour = dict(VALID_BASE, hour=25)  # hour > 23
payload_bad_hour = {"base_features": bad_hour, "scenario_features": VALID_BASE}
resp7 = post_what_if(payload_bad_hour)
ok7 = resp7.status_code == 422
record("7. Invalid hour (25) -> HTTP 422",
       ok7,
       f"HTTP {resp7.status_code}")

# TEST 8 - Invalid month
bad_month = dict(VALID_BASE, month=13)  # month > 12
payload_bad_month = {"base_features": bad_month, "scenario_features": VALID_BASE}
resp8 = post_what_if(payload_bad_month)
ok8 = resp8.status_code == 422
record("8. Invalid month (13) -> HTTP 422",
       ok8,
       f"HTTP {resp8.status_code}")

# TEST 9 - Missing required feature
base_missing = {k: v for k, v in VALID_BASE.items() if k != "lag_1h_kwh"}
payload_missing = {"base_features": base_missing, "scenario_features": VALID_BASE}
resp9 = post_what_if(payload_missing)
ok9 = resp9.status_code == 422
record("9. Missing required feature (lag_1h_kwh) -> HTTP 422",
       ok9,
       f"HTTP {resp9.status_code}")

# TEST 10 - Extra/unknown feature is handled gracefully (Pydantic ignores extra fields)
base_extra = dict(VALID_BASE, unknown_feature=99.9)
payload_extra = {"base_features": base_extra, "scenario_features": VALID_BASE}
resp10 = post_what_if(payload_extra)
ok10 = resp10.status_code in (200, 422)  # Both acceptable behaviors
record("10. Extra/unknown feature is handled gracefully",
       ok10,
       f"HTTP {resp10.status_code} (200=ignored, 422=rejected by schema)")

# ---------------------------------------------------------------------------
# Tests 11-13: Classification & Interpretation
# ---------------------------------------------------------------------------
separator("Tests 11-13: Classification & Interpretation")

# Fetch results from test 1 (valid lower scenario)
if ok1:
    base_status = d1.get("base_status", "")
    scenario_status = d1.get("scenario_status", "")
    interpretation = d1.get("interpretation", "")

    # TEST 11 - Base status classification
    ok11 = base_status in ("NORMAL", "HIGH", "PEAK")
    record("11. Base status is a valid tier (NORMAL/HIGH/PEAK)",
           ok11,
           f"base_status='{base_status}'")

    # TEST 12 - Scenario status classification
    ok12 = scenario_status in ("NORMAL", "HIGH", "PEAK")
    record("12. Scenario status is a valid tier",
           ok12,
           f"scenario_status='{scenario_status}'")

    # TEST 13 - Interpretation is non-empty and uses "predicted"
    ok13 = (
        isinstance(interpretation, str)
        and len(interpretation) > 20
        and "predicted" in interpretation.lower()
    )
    record("13. Interpretation is non-empty and uses 'predicted'",
           ok13,
           f"length={len(interpretation)}, snippet='{interpretation[:80]}...'")
else:
    record("11. Base status is a valid tier", False, "skipped (test 1 failed)")
    record("12. Scenario status is a valid tier", False, "skipped (test 1 failed)")
    record("13. Interpretation non-empty and uses 'predicted'", False, "skipped (test 1 failed)")

# ---------------------------------------------------------------------------
# Test 14 - Full API round-trip with user-spec example
# ---------------------------------------------------------------------------
separator("Test 14: Full API Round-Trip")

payload_spec = {
    "base_features": {
        "hour": 18,
        "day": 26,
        "day_of_week": 4,
        "month": 11,
        "weekend": 0,
        "lag_1h_kwh": 1.6593,
        "lag_24h_kwh": 1.5735,
        "rolling_mean_24h_kwh": 1.7259
    },
    "scenario_features": {
        "hour": 19,
        "day": 26,
        "day_of_week": 4,
        "month": 11,
        "weekend": 0,
        "lag_1h_kwh": 1.4000,
        "lag_24h_kwh": 1.5000,
        "rolling_mean_24h_kwh": 1.6000
    }
}

resp14 = post_what_if(payload_spec)
ok14_http = resp14.status_code == 200
if ok14_http:
    d14 = resp14.json()
    required_fields = [
        "base_prediction_kwh", "scenario_prediction_kwh",
        "difference_kwh", "percentage_change",
        "base_status", "scenario_status",
        "base_baseline_kwh", "scenario_baseline_kwh",
        "interpretation", "model_name", "unit"
    ]
    missing_fields = [f for f in required_fields if f not in d14]
    ok14 = len(missing_fields) == 0
    detail14 = (
        f"base={d14['base_prediction_kwh']} kWh, "
        f"scenario={d14['scenario_prediction_kwh']} kWh, "
        f"diff={d14['difference_kwh']} kWh, "
        f"pct={d14['percentage_change']}%, "
        f"base_status={d14['base_status']}, "
        f"scenario_status={d14['scenario_status']}"
    )
    if missing_fields:
        detail14 += f" | MISSING FIELDS: {missing_fields}"
else:
    ok14 = False
    d14 = {}
    detail14 = f"HTTP {resp14.status_code}: {resp14.text[:200]}"

record("14. Full /what-if round-trip with spec example payload",
       ok14,
       detail14)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
separator("PHASE 6 WHAT-IF TEST SUMMARY")
for tag, name, detail in results:
    mark = "OK" if tag == PASS else "XX"
    print(f"  [{tag}]  {mark}  {name}")

print(f"\n{'=' * 60}")
print(f"  TOTAL: {passed}/{total} tests passed")

if ok14 and ok1:
    print("\n  Full /what-if API response (Test 14):")
    print(json.dumps(d14, indent=4))

print('=' * 60)

if passed < total:
    sys.exit(1)
