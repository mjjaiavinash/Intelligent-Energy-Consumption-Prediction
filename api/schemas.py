"""
api/schemas.py
==============
Pydantic validation schemas for the Energy Consumption Prediction API.

Enforces strict type checks, valid numerical bounds, and field descriptions
for the 8 genuine next-hour forecasting features.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """
    Input schema containing the 8 features required for next-hour energy forecasting.
    Excluded concurrent same-hour variables are strictly omitted.
    """
    hour: int = Field(
        ...,
        ge=0,
        le=23,
        description="Hour of the day in 24-hour format (0-23)",
        examples=[18]
    )
    day: int = Field(
        ...,
        ge=1,
        le=31,
        description="Day of the month (1-31)",
        examples=[26]
    )
    day_of_week: int = Field(
        ...,
        ge=0,
        le=6,
        description="Day of the week (0 = Monday, 6 = Sunday)",
        examples=[4]
    )
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Month of the year (1-12)",
        examples=[11]
    )
    weekend: int = Field(
        ...,
        ge=0,
        le=1,
        description="Binary indicator: 1 if Saturday/Sunday, 0 if weekday",
        examples=[0]
    )
    lag_1h_kwh: float = Field(
        ...,
        ge=0.0,
        description="Energy consumption in the immediate preceding hour (kWh)",
        examples=[2.15]
    )
    lag_24h_kwh: float = Field(
        ...,
        ge=0.0,
        description="Energy consumption at the same hour on the previous day (kWh)",
        examples=[1.95]
    )
    rolling_mean_24h_kwh: float = Field(
        ...,
        ge=0.0,
        description="24-hour moving average energy consumption (kWh)",
        examples=[1.45]
    )

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
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
    }


class PredictionResponse(BaseModel):
    """
    Response schema returning the predicted energy consumption and model information.
    """
    predicted_energy_kwh: float = Field(
        ...,
        description="Predicted energy consumption for the given input feature values (in kWh)",
        examples=[2.385]
    )
    model_name: str = Field(
        ...,
        description="Machine learning model utilized for inference",
        examples=["XGBoost"]
    )
    unit: str = Field(
        default="kWh",
        description="Unit of measurement"
    )
    status: str = Field(
        default="success",
        description="Execution status of the prediction request"
    )

    model_config = {
        "protected_namespaces": ()
    }


class HealthResponse(BaseModel):
    """
    Response schema for the API health check endpoint.
    """
    status: str = Field(..., description="API operational status", examples=["healthy"])
    model_loaded: bool = Field(..., description="Confirmation that the trained ML model is loaded", examples=[True])
    model_name: str = Field(..., description="Name of the currently loaded model", examples=["XGBoost"])
    features_count: int = Field(..., description="Number of expected input features", examples=[8])
    version: str = Field(default="1.0.0", description="API version")

    model_config = {
        "protected_namespaces": ()
    }


class OptimizationRequest(BaseModel):
    """
    Input schema for the energy optimization endpoint.
    Supports either:
    1. Specifying an existing 'prediction_id' from the database, OR
    2. Providing direct 'predicted_consumption' and 'hour', OR
    3. Providing raw forecasting features in 'features' for end-to-end predict & optimize.
    """
    prediction_id: Optional[int] = Field(
        None,
        description="ID of an existing prediction record from the predictions table",
        examples=[1]
    )
    predicted_consumption: Optional[float] = Field(
        None,
        ge=0.0,
        description="Predicted energy consumption in kWh (if not referencing prediction_id)",
        examples=[2.85]
    )
    hour: Optional[int] = Field(
        None,
        ge=0,
        le=23,
        description="Hour of day (0-23) for baseline matching",
        examples=[18]
    )
    day_of_week: Optional[int] = Field(
        None,
        ge=0,
        le=6,
        description="Day of week (0=Monday, 6=Sunday)",
        examples=[4]
    )
    weekend: Optional[int] = Field(
        None,
        ge=0,
        le=1,
        description="Weekend flag (1 for weekend, 0 for weekday)",
        examples=[0]
    )
    features: Optional[PredictionRequest] = Field(
        None,
        description="Optional full 8-feature payload to run model inference and optimize in one step"
    )

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "predicted_consumption": 2.85,
                "hour": 18,
                "day_of_week": 4,
                "weekend": 0
            }
        }
    }


class OptimizationResponse(BaseModel):
    """
    Response schema returning data-driven baseline comparison, excess metrics,
    consumption classification tier, and tailored recommendations.
    """
    prediction_id: Optional[int] = Field(
        None,
        description="Linked ID from predictions table if available",
        examples=[123]
    )
    baseline_consumption: float = Field(
        ...,
        description="Data-driven historical baseline consumption from MySQL records (kWh)",
        examples=[1.1427]
    )
    predicted_consumption: float = Field(
        ...,
        description="Model's forecasted energy consumption (kWh)",
        examples=[2.85]
    )
    excess_consumption: float = Field(
        ...,
        description="Potential consumption above historical baseline: max(predicted - baseline, 0) (kWh)",
        examples=[1.7073]
    )
    potential_saving: float = Field(
        ...,
        description="Projected potential energy savings if consumption is moderated (kWh)",
        examples=[1.7073]
    )
    saving_percentage: float = Field(
        ...,
        description="Potential saving percentage: (excess / predicted) * 100 (%)",
        examples=[59.91]
    )
    status: str = Field(
        ...,
        description="Data-driven classification status: NORMAL, HIGH, or PEAK",
        examples=["PEAK"]
    )
    recommendation: str = Field(
        ...,
        description="Conservative, actionable optimization recommendation",
        examples=["High energy consumption peak detected. Consider shifting flexible loads to a lower-consumption period."]
    )
    unit: str = Field(
        default="kWh",
        description="Unit of energy measurement"
    )



    model_config = {
        "protected_namespaces": ()
    }


class WhatIfRequest(BaseModel):
    """
    Input schema for the What-If Energy Simulation endpoint (POST /what-if).

    Accepts two complete 8-feature sets:
    - base_features    : The reference/current scenario.
    - scenario_features: The modified/what-if scenario to compare against the base.

    Both feature sets are validated against the same bounds as PredictionRequest.
    Only the 8 genuine forecasting features are accepted; same-period concurrent
    measurements (reactive power, voltage, etc.) are excluded by design.
    """
    base_features: PredictionRequest = Field(
        ...,
        description="Reference (base) feature set for the current scenario prediction"
    )
    scenario_features: PredictionRequest = Field(
        ...,
        description="Modified (what-if) feature set to compare against the base scenario"
    )

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
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
        }
    }


class WhatIfResponse(BaseModel):
    """
    Response schema for the POST /what-if endpoint.

    Returns the dual-prediction comparison result including:
    - Raw predicted kWh for both base and scenario.
    - Arithmetic difference and percentage change.
    - Data-driven NORMAL / HIGH / PEAK classification for both.
    - Plain-English interpretation (conservative; uses 'predicted' not 'guaranteed').
    """
    base_prediction_kwh: float = Field(
        ...,
        description="XGBoost-predicted energy consumption for the base scenario (kWh)",
        examples=[2.385]
    )
    scenario_prediction_kwh: float = Field(
        ...,
        description="XGBoost-predicted energy consumption for the what-if scenario (kWh)",
        examples=[2.050]
    )
    difference_kwh: float = Field(
        ...,
        description="Difference: scenario_prediction - base_prediction (kWh). Negative = scenario uses less.",
        examples=[-0.335]
    )
    percentage_change: float = Field(
        ...,
        description="Percentage change: ((scenario - base) / base) * 100. Returns 0.0 when base = 0.",
        examples=[-14.05]
    )
    base_status: str = Field(
        ...,
        description="Data-driven consumption tier for base scenario: NORMAL, HIGH, or PEAK",
        examples=["HIGH"]
    )
    scenario_status: str = Field(
        ...,
        description="Data-driven consumption tier for scenario: NORMAL, HIGH, or PEAK",
        examples=["NORMAL"]
    )
    base_baseline_kwh: float = Field(
        ...,
        description="Historical MySQL baseline used for base scenario classification (kWh)",
        examples=[1.19]
    )
    scenario_baseline_kwh: float = Field(
        ...,
        description="Historical MySQL baseline used for scenario classification (kWh)",
        examples=[1.15]
    )
    interpretation: str = Field(
        ...,
        description="Conservative plain-English interpretation of the simulation result"
    )
    model_name: str = Field(
        default="XGBoost",
        description="Machine learning model used for both predictions"
    )
    unit: str = Field(
        default="kWh",
        description="Unit of energy measurement"
    )

    model_config = {
        "protected_namespaces": ()
    }
