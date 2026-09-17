"""
src/what_if.py
==============
What-If Energy Consumption Simulation Engine for Phase 6.

Provides the core computation logic for running dual-scenario predictions
using the trained XGBoost model (8 forecasting features) and comparing
the results against historical baselines.

Key design principles:
- Reuses existing Phase 4 classification logic (calculate_historical_baseline,
  classify_consumption) — no second classification system.
- Does NOT write to the database (simulations are exploratory/ephemeral).
- Does NOT introduce features not supported by the trained model.
- All interpretation text is conservative and uses "predicted" not "guaranteed".
"""

import os
import sys
from typing import Dict, Any, Optional

import pandas as pd

# Ensure base directory is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.optimization import (
    calculate_historical_baseline,
    classify_consumption
)


# Ordered feature list exactly matching models/feature_names.json
FORECASTING_FEATURES = [
    "hour",
    "day",
    "day_of_week",
    "month",
    "weekend",
    "lag_1h_kwh",
    "lag_24h_kwh",
    "rolling_mean_24h_kwh",
]


def run_single_prediction(features: Dict[str, Any], model) -> float:
    """
    Run inference for a single feature dict using the provided model.

    Parameters
    ----------
    features : dict
        Mapping of feature name -> value, must contain all 8 forecasting features.
    model : sklearn-compatible model
        Trained XGBoost model loaded from joblib.

    Returns
    -------
    float
        Predicted energy consumption in kWh (clipped at 0.0).
    """
    input_row = {col: features[col] for col in FORECASTING_FEATURES}
    df = pd.DataFrame([input_row])
    raw = float(model.predict(df)[0])
    return max(0.0, round(raw, 4))


def compute_status(
    predicted_kwh: float,
    hour: int,
    day_of_week: Optional[int] = None,
    weekend: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute NORMAL / HIGH / PEAK classification for a given prediction
    by querying the MySQL historical baseline for the matching time context.

    Reuses calculate_historical_baseline() and classify_consumption() from
    src/optimization.py to maintain a single classification system.

    Returns
    -------
    dict with keys: status, baseline_kwh, std_dev, sample_count
    """
    baseline_info = calculate_historical_baseline(
        hour=hour,
        day_of_week=day_of_week,
        weekend=weekend,
    )
    baseline_kwh = baseline_info["baseline_kwh"]
    std_dev = baseline_info["std_dev"]
    sample_count = baseline_info["sample_count"]

    status = classify_consumption(predicted_kwh, baseline_kwh, std_dev)

    return {
        "status": status,
        "baseline_kwh": round(baseline_kwh, 4),
        "std_dev": round(std_dev, 4),
        "sample_count": sample_count,
    }


def generate_interpretation(
    base_kwh: float,
    scenario_kwh: float,
    difference_kwh: float,
    percentage_change: float,
    base_status: str,
    scenario_status: str,
) -> str:
    """
    Generate a plain-English, conservative interpretation of the what-if
    comparison result.

    Uses "predicted" throughout — never "guaranteed" or "actual savings".

    Parameters
    ----------
    base_kwh : float
    scenario_kwh : float
    difference_kwh : float   (scenario - base)
    percentage_change : float
    base_status : str        (NORMAL / HIGH / PEAK)
    scenario_status : str    (NORMAL / HIGH / PEAK)

    Returns
    -------
    str  Plain-English interpretation.
    """
    abs_diff = abs(difference_kwh)
    abs_pct = abs(percentage_change)

    # Direction
    if abs_diff < 0.001:
        direction_text = (
            "The scenario produces approximately the same predicted energy consumption "
            f"as the base scenario ({base_kwh:.3f} kWh)."
        )
    elif difference_kwh < 0:
        direction_text = (
            f"The scenario predicts lower energy consumption by {abs_diff:.3f} kWh "
            f"({abs_pct:.2f}%) compared to the base scenario "
            f"({base_kwh:.3f} kWh → {scenario_kwh:.3f} kWh)."
        )
    else:
        direction_text = (
            f"The scenario predicts higher energy consumption by {abs_diff:.3f} kWh "
            f"({abs_pct:.2f}%) compared to the base scenario "
            f"({base_kwh:.3f} kWh → {scenario_kwh:.3f} kWh)."
        )

    # Status change insight
    status_insight = ""
    if base_status != scenario_status:
        status_insight = (
            f" The predicted consumption category changes from "
            f"{base_status} (base) to {scenario_status} (scenario)."
        )
        # Highlight improvement specifically
        tier_order = {"NORMAL": 0, "HIGH": 1, "PEAK": 2}
        if tier_order.get(scenario_status, 0) < tier_order.get(base_status, 0):
            status_insight += (
                f" This is a predicted improvement in the consumption tier."
            )
        else:
            status_insight += (
                f" This represents a predicted worsening of the consumption tier."
            )
    else:
        status_insight = f" Both scenarios remain in the {base_status} tier."

    # Disclaimer
    disclaimer = (
        " Note: These are model-predicted values — not guaranteed real-world outcomes."
    )

    return direction_text + status_insight + disclaimer


def compute_what_if(
    base_features: Dict[str, Any],
    scenario_features: Dict[str, Any],
    model,
    model_name: str = "XGBoost",
) -> Dict[str, Any]:
    """
    Core What-If computation function.

    1. Runs model inference on the base feature set.
    2. Runs model inference on the scenario feature set.
    3. Calculates difference and percentage change.
    4. Classifies both predictions against the historical MySQL baseline.
    5. Generates a dynamic interpretation.

    Parameters
    ----------
    base_features : dict
        8 forecasting features for the reference/base scenario.
    scenario_features : dict
        8 forecasting features for the what-if scenario (may differ from base).
    model : sklearn-compatible model
        Trained XGBoost model.
    model_name : str
        Display name of the model (e.g., "XGBoost").

    Returns
    -------
    dict containing complete what-if simulation results.
    """
    # 1. Predict base and scenario
    base_kwh = run_single_prediction(base_features, model)
    scenario_kwh = run_single_prediction(scenario_features, model)

    # 2. Calculate difference
    difference_kwh = round(scenario_kwh - base_kwh, 4)

    # 3. Calculate percentage change (safe division)
    if base_kwh > 0.0:
        percentage_change = round(
            ((scenario_kwh - base_kwh) / base_kwh) * 100.0, 2
        )
    else:
        percentage_change = 0.0

    # 4. Classify both predictions via existing Phase 4 logic
    base_status_info = compute_status(
        predicted_kwh=base_kwh,
        hour=base_features["hour"],
        day_of_week=base_features.get("day_of_week"),
        weekend=base_features.get("weekend"),
    )
    scenario_status_info = compute_status(
        predicted_kwh=scenario_kwh,
        hour=scenario_features["hour"],
        day_of_week=scenario_features.get("day_of_week"),
        weekend=scenario_features.get("weekend"),
    )

    base_status = base_status_info["status"]
    scenario_status = scenario_status_info["status"]

    # 5. Generate interpretation
    interpretation = generate_interpretation(
        base_kwh=base_kwh,
        scenario_kwh=scenario_kwh,
        difference_kwh=difference_kwh,
        percentage_change=percentage_change,
        base_status=base_status,
        scenario_status=scenario_status,
    )

    return {
        "base_prediction_kwh": base_kwh,
        "scenario_prediction_kwh": scenario_kwh,
        "difference_kwh": difference_kwh,
        "percentage_change": percentage_change,
        "base_status": base_status,
        "scenario_status": scenario_status,
        "base_baseline_kwh": base_status_info["baseline_kwh"],
        "scenario_baseline_kwh": scenario_status_info["baseline_kwh"],
        "interpretation": interpretation,
        "model_name": model_name,
        "unit": "kWh",
    }
