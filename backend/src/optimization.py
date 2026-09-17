"""
src/optimization.py
===================
Data-Driven Energy Optimization Engine for Intelligent Energy Consumption Prediction.

Key capabilities:
1. Calculates data-driven historical baselines using actual MySQL smart-meter readings
   (matching hour-of-day, day-of-week, and weekend patterns).
2. Quantifies potential excess consumption and potential savings (kWh and %).
3. Classifies consumption into explainable tiers: NORMAL, HIGH, or PEAK.
4. Generates conservative, actionable energy reduction/load-shifting recommendations.
5. Persists optimization results to the MySQL 'optimization_results' table.
"""

import os
import sys
from typing import Dict, Any, Optional, Tuple

# Ensure base directory is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.database import (
    get_connection,
    insert_optimization_result,
    get_prediction_by_id
)


def calculate_historical_baseline(
    hour: int,
    day_of_week: Optional[int] = None,
    weekend: Optional[int] = None,
    before_timestamp: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Calculate data-driven baseline consumption metrics from actual historical
    records stored in MySQL energy_consumption.

    Matching strategy:
    - Primary: Match same hour and day_of_week (e.g. Friday 6 PM).
    - Fallback: Match same hour and weekend indicator (e.g. Weekday 6 PM) if samples < 10.
    - Final Fallback: Match same hour across all days if samples < 10.

    Parameters:
    -----------
    hour : int (0-23)
    day_of_week : Optional[int] (0-6, 0=Monday)
    weekend : Optional[int] (0=Weekday, 1=Weekend)
    before_timestamp : Optional[str or datetime]

    Returns:
    --------
    Dict containing:
      - 'baseline_kwh': float (mean consumption)
      - 'std_dev': float (standard deviation)
      - 'sample_count': int (number of historical observations evaluated)
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"Invalid hour: {hour}. Hour must be between 0 and 23.")

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Primary query: match hour and day_of_week
        if day_of_week is not None:
            query = """
                SELECT 
                    ROUND(AVG(energy_consumption_kwh), 4) AS avg_kwh,
                    ROUND(STDDEV(energy_consumption_kwh), 4) AS std_kwh,
                    COUNT(*) AS cnt
                FROM energy_consumption
                WHERE hour = %s AND day_of_week = %s
            """
            params = [hour, day_of_week]
            if before_timestamp is not None:
                query += " AND timestamp < %s"
                params.append(before_timestamp)

            cursor.execute(query, params)
            row = cursor.fetchone()
            if row and row["cnt"] and row["cnt"] >= 10:
                return {
                    "baseline_kwh": float(row["avg_kwh"]),
                    "std_dev": float(row["std_kwh"]) if row["std_kwh"] is not None else 0.0,
                    "sample_count": int(row["cnt"])
                }

        # 2. Secondary query: match hour and weekend flag
        if weekend is not None or (day_of_week is not None and weekend is None):
            wknd_val = weekend if weekend is not None else (1 if day_of_week in (5, 6) else 0)
            query = """
                SELECT 
                    ROUND(AVG(energy_consumption_kwh), 4) AS avg_kwh,
                    ROUND(STDDEV(energy_consumption_kwh), 4) AS std_kwh,
                    COUNT(*) AS cnt
                FROM energy_consumption
                WHERE hour = %s AND weekend = %s
            """
            params = [hour, wknd_val]
            if before_timestamp is not None:
                query += " AND timestamp < %s"
                params.append(before_timestamp)

            cursor.execute(query, params)
            row = cursor.fetchone()
            if row and row["cnt"] and row["cnt"] >= 10:
                return {
                    "baseline_kwh": float(row["avg_kwh"]),
                    "std_dev": float(row["std_kwh"]) if row["std_kwh"] is not None else 0.0,
                    "sample_count": int(row["cnt"])
                }

        # 3. Fallback: match hour across all days
        query = """
            SELECT 
                ROUND(AVG(energy_consumption_kwh), 4) AS avg_kwh,
                ROUND(STDDEV(energy_consumption_kwh), 4) AS std_kwh,
                COUNT(*) AS cnt
            FROM energy_consumption
            WHERE hour = %s
        """
        params = [hour]
        if before_timestamp is not None:
            query += " AND timestamp < %s"
            params.append(before_timestamp)

        cursor.execute(query, params)
        row = cursor.fetchone()

        if row and row["cnt"] and row["cnt"] > 0:
            return {
                "baseline_kwh": float(row["avg_kwh"]),
                "std_dev": float(row["std_kwh"]) if row["std_kwh"] is not None else 0.0,
                "sample_count": int(row["cnt"])
            }
        else:
            # Fallback if table is completely empty
            return {
                "baseline_kwh": 1.0,
                "std_dev": 0.5,
                "sample_count": 0
            }

    finally:
        conn.close()


def calculate_excess_consumption(predicted_consumption: float, baseline_consumption: float) -> float:
    """
    Calculate potential excess consumption above the historical baseline:
    excess = max(predicted_consumption - baseline_consumption, 0)
    """
    excess = max(predicted_consumption - baseline_consumption, 0.0)
    return round(float(excess), 4)


def calculate_saving_percentage(predicted_consumption: float, excess_consumption: float) -> float:
    """
    Calculate the potential saving percentage:
    if predicted_consumption > 0 and excess_consumption > 0:
        saving_pct = (excess_consumption / predicted_consumption) * 100
    else:
        0.0
    """
    if predicted_consumption > 0.0 and excess_consumption > 0.0:
        pct = (excess_consumption / predicted_consumption) * 100.0
        return round(float(pct), 2)
    return 0.0


def classify_consumption(
    predicted_consumption: float,
    baseline_consumption: float,
    std_dev: Optional[float] = None
) -> str:
    """
    Data-driven, explainable classification of predicted energy consumption:
    - NORMAL : Predicted consumption is within normal variation of historical baseline.
    - HIGH   : Predicted consumption is moderately elevated above baseline.
    - PEAK   : Predicted consumption is significantly elevated above baseline.

    Uses standard deviation bounds when available; falls back to percentage ratios:
    - Normal: predicted <= baseline + 0.5*std (or <= 1.15*baseline)
    - High:   baseline + 0.5*std < predicted <= baseline + 1.5*std (or 1.15 to 1.35*baseline)
    - Peak:   predicted > baseline + 1.5*std (or > 1.35*baseline)
    """
    if baseline_consumption <= 0:
        return "NORMAL"

    if std_dev is not None and std_dev > 0.05:
        normal_limit = baseline_consumption + (0.5 * std_dev)
        high_limit = baseline_consumption + (1.5 * std_dev)
    else:
        normal_limit = baseline_consumption * 1.15
        high_limit = baseline_consumption * 1.35

    if predicted_consumption <= normal_limit:
        return "NORMAL"
    elif predicted_consumption <= high_limit:
        return "HIGH"
    else:
        return "PEAK"


def generate_recommendation(
    status: str,
    excess_consumption: float,
    saving_percentage: float
) -> str:
    """
    Generate transparent, conservative recommendations based on consumption tier.
    Does not invent appliance-level data because the dataset does not contain appliance schedules.
    """
    status_upper = status.upper()

    if status_upper == "NORMAL":
        return "Energy consumption is within the normal historical range for this time period."

    elif status_upper == "HIGH":
        return (
            f"Moderately elevated energy consumption detected ({excess_consumption:.2f} kWh above historical baseline). "
            f"Consider reducing or shifting flexible energy usage during this period (potential saving: {saving_percentage:.1f}%)."
        )

    elif status_upper == "PEAK":
        return (
            f"High energy consumption peak detected ({excess_consumption:.2f} kWh above historical baseline). "
            f"Consider shifting flexible loads to a lower-consumption period (potential saving: {saving_percentage:.1f}%)."
        )

    else:
        return "Energy consumption evaluated. Monitor usage trends."


def optimize_prediction(
    predicted_consumption: Optional[float] = None,
    hour: Optional[int] = None,
    day_of_week: Optional[int] = None,
    weekend: Optional[int] = None,
    prediction_id: Optional[int] = None,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    High-level orchestrator:
    1. Resolves prediction details (either from prediction_id or directly provided).
    2. Calculates historical baseline from MySQL energy_consumption.
    3. Computes excess consumption and potential saving percentage.
    4. Classifies consumption into NORMAL / HIGH / PEAK.
    5. Generates a tailored recommendation.
    6. Persists result into MySQL optimization_results table (if save_to_db is True).

    Returns:
    --------
    Dict containing complete optimization results.
    """
    target_pred = predicted_consumption
    target_hour = hour
    target_dow = day_of_week
    target_weekend = weekend

    # If prediction_id is provided, retrieve details from predictions table
    if prediction_id is not None:
        pred_record = get_prediction_by_id(prediction_id)
        if pred_record is None:
            raise ValueError(f"Prediction record with ID {prediction_id} not found in database.")

        if target_pred is None:
            target_pred = float(pred_record["predicted_energy_kwh"])

        # Infer hour and day_of_week from prediction_time or target_time if not explicitly passed
        ref_time = pred_record.get("target_time") or pred_record.get("prediction_time")
        if ref_time is not None:
            if target_hour is None:
                target_hour = ref_time.hour
            if target_dow is None:
                target_dow = ref_time.weekday()
            if target_weekend is None:
                target_weekend = 1 if target_dow in (5, 6) else 0

    # Ensure we have both predicted consumption and hour
    if target_pred is None:
        raise ValueError("predicted_consumption must be provided or resolved via prediction_id.")
    if target_hour is None:
        raise ValueError("hour must be provided or resolved from prediction record timestamps.")

    if target_weekend is None and target_dow is not None:
        target_weekend = 1 if target_dow in (5, 6) else 0

    # 1. Calculate baseline using actual historical records from MySQL
    baseline_info = calculate_historical_baseline(
        hour=target_hour,
        day_of_week=target_dow,
        weekend=target_weekend
    )
    baseline_val = baseline_info["baseline_kwh"]
    std_dev_val = baseline_info["std_dev"]
    samples_val = baseline_info["sample_count"]

    # 2. Calculate excess consumption
    excess_val = calculate_excess_consumption(target_pred, baseline_val)

    # 3. Calculate saving percentage
    saving_pct = calculate_saving_percentage(target_pred, excess_val)

    # 4. Classify status
    status_tier = classify_consumption(target_pred, baseline_val, std_dev_val)

    # 5. Generate recommendation
    rec_text = generate_recommendation(status_tier, excess_val, saving_pct)

    # 6. Save to database if requested
    opt_record_id = None
    if save_to_db:
        try:
            opt_record_id = insert_optimization_result(
                prediction_id=prediction_id,
                baseline_consumption=baseline_val,
                predicted_consumption=target_pred,
                potential_saving=excess_val,
                saving_percentage=saving_pct,
                recommendation=rec_text
            )
        except Exception as db_err:
            print(f"[WARN] Failed to insert optimization record into database: {db_err}")

    return {
        "id": opt_record_id,
        "prediction_id": prediction_id,
        "baseline_consumption": round(baseline_val, 4),
        "predicted_consumption": round(target_pred, 4),
        "excess_consumption": round(excess_val, 4),
        "potential_saving": round(excess_val, 4),
        "saving_percentage": round(saving_pct, 2),
        "status": status_tier,
        "recommendation": rec_text,
        "sample_count": samples_val,
        "unit": "kWh"
    }
