"""
api/main.py
===========
FastAPI backend service for Intelligent Energy Consumption Prediction.

Features:
- Loads the trained XGBoost model and feature schema at startup.
- GET /health: Verifies API health and model availability.
- POST /predict: Accepts the 8 validated forecasting features and returns next-hour energy predictions.
- Strict feature ordering adherence against models/feature_names.json.
- Interactive documentation at /docs (Swagger) and /redoc (ReDoc).
"""

import os
import json
import joblib
from contextlib import asynccontextmanager
from typing import List

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    OptimizationRequest,
    OptimizationResponse,
    WhatIfRequest,
    WhatIfResponse
)
from src.optimization import optimize_prediction
from src.what_if import compute_what_if
from src.database import (
    insert_prediction,
    get_historical_energy_records,
    get_energy_summary,
    get_recent_predictions,
    get_recent_optimization_results
)

# Paths to persisted model artifacts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "best_energy_model.joblib")
FEATURE_NAMES_PATH = os.path.join(MODELS_DIR, "feature_names.json")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

# In-memory application state
ml_state = {
    "model": None,
    "feature_names": [],
    "model_name": "Unknown",
    "is_loaded": False
}


def load_artifacts():
    """
    Load the trained model and feature ordering from the models directory.
    Called once during API initialization.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. "
            "Please run 'python src/train_models.py' first to train and persist the model."
        )

    if not os.path.exists(FEATURE_NAMES_PATH):
        raise FileNotFoundError(
            f"Feature names file not found at {FEATURE_NAMES_PATH}."
        )

    # Load model with Joblib
    print(f"--> Loading model from: {MODEL_PATH}")
    ml_state["model"] = joblib.load(MODEL_PATH)

    # Load feature order
    print(f"--> Loading feature order from: {FEATURE_NAMES_PATH}")
    with open(FEATURE_NAMES_PATH, "r", encoding="utf-8") as f:
        ml_state["feature_names"] = json.load(f)

    # Load model name from metadata if available
    ml_state["model_name"] = "XGBoost"
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                ml_state["model_name"] = meta.get("best_model_name", "XGBoost")
        except Exception:
            pass

    ml_state["is_loaded"] = True
    print(f"--> [SUCCESS] Model '{ml_state['model_name']}' loaded successfully with {len(ml_state['feature_names'])} features.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle application startup and shutdown.
    Loads the trained model once before handling incoming requests.
    """
    load_artifacts()
    yield
    print("--> Shutting down Energy Prediction API service.")


# FastAPI Application Definition
app = FastAPI(
    title="Intelligent Energy Consumption Prediction API",
    description=(
        "Production-grade REST API for forecasting next-hour household energy consumption (kWh) "
        "using historical consumption dynamics and calendar context. Exposes the trained XGBoost model."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurable CORS origins for development and production security
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["Root"],
    summary="Root service info",
    description="Returns basic service information and navigation links to API documentation."
)
def root():
    return {
        "message": "Intelligent Energy Consumption Prediction API is running.",
        "documentation": "/docs",
        "health_check": "/health",
        "predict_endpoint": "/predict",
        "version": "1.0.0"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API and model health",
    description="Returns operational status and verifies that the machine learning model is loaded into memory."
)
def health_check():
    if not ml_state["is_loaded"] or ml_state["model"] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded or unavailable."
        )

    return HealthResponse(
        status="healthy",
        model_loaded=True,
        model_name=ml_state["model_name"],
        features_count=len(ml_state["feature_names"]),
        version="1.0.0"
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Predict energy consumption for given feature inputs",
    description=(
        "Feature-level prediction service. Accepts the 8 validated features (hour, day, day_of_week, "
        "month, weekend, lag_1h_kwh, lag_24h_kwh, rolling_mean_24h_kwh) and computes the model's predicted "
        "energy consumption in kWh for those given operational inputs. "
        "(Automated calculation of historical lag features will be integrated with database storage in a later phase)."
    )
)
def predict_energy(request: PredictionRequest):
    # 1. Verify model is loaded
    if not ml_state["is_loaded"] or ml_state["model"] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forecasting model is currently not loaded."
        )

    try:
        # 2. Extract payload dictionary
        data_dict = request.model_dump()

        # 3. Enforce strict feature ordering identical to training feature_names.json
        feature_order = ml_state["feature_names"]
        input_row = {col: data_dict[col] for col in feature_order}

        # 4. Create DataFrame to preserve column names expected by XGBoost
        df_input = pd.DataFrame([input_row])

        # 5. Perform model inference
        prediction_val = float(ml_state["model"].predict(df_input)[0])

        # Energy consumption cannot physically be negative; clip at 0.0
        predicted_kwh = max(0.0, round(prediction_val, 4))

        return PredictionResponse(
            predicted_energy_kwh=predicted_kwh,
            model_name=ml_state["model_name"],
            unit="kWh",
            status="success"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during model inference: {str(exc)}"
        )


@app.post(
    "/optimize",
    response_model=OptimizationResponse,
    tags=["Optimization"],
    summary="Generate data-driven energy optimization and savings recommendations",
    description=(
        "Calculates a data-driven historical baseline from MySQL records for the target hour/day, "
        "compares it with predicted consumption, computes potential excess and savings, classifies the tier "
        "(NORMAL, HIGH, or PEAK), and saves the result to the optimization_results table."
    )
)
def optimize_energy(request: OptimizationRequest):
    # Case 1: Raw features provided -> predict, log prediction to DB, then optimize
    if request.features is not None:
        if not ml_state["is_loaded"] or ml_state["model"] is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Forecasting model is not loaded."
            )
        try:
            feat_dict = request.features.model_dump()
            feature_order = ml_state["feature_names"]
            input_row = {col: feat_dict[col] for col in feature_order}
            df_input = pd.DataFrame([input_row])
            predicted_val = float(ml_state["model"].predict(df_input)[0])
            predicted_val = max(0.0, round(predicted_val, 4))

            # Store prediction into MySQL predictions table
            prediction_id = insert_prediction(
                predicted_energy_kwh=predicted_val,
                model_name=ml_state["model_name"]
            )

            result = optimize_prediction(
                predicted_consumption=predicted_val,
                hour=feat_dict["hour"],
                day_of_week=feat_dict["day_of_week"],
                weekend=feat_dict["weekend"],
                prediction_id=prediction_id,
                save_to_db=True
            )
            return OptimizationResponse(**result)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Optimization failed: {str(e)}"
            )

    # Case 2: Existing prediction_id provided
    elif request.prediction_id is not None:
        try:
            result = optimize_prediction(
                prediction_id=request.prediction_id,
                predicted_consumption=request.predicted_consumption,
                hour=request.hour,
                day_of_week=request.day_of_week,
                weekend=request.weekend,
                save_to_db=True
            )
            return OptimizationResponse(**result)
        except ValueError as val_err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(val_err)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Optimization failed: {str(e)}"
            )

    # Case 3: Direct predicted_consumption and hour provided
    elif request.predicted_consumption is not None:
        if request.hour is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'hour' (0-23) is required when specifying 'predicted_consumption'."
            )
        try:
            # Optionally log prediction to predictions table
            pred_id = insert_prediction(
                predicted_energy_kwh=request.predicted_consumption,
                model_name=ml_state["model_name"]
            )

            result = optimize_prediction(
                predicted_consumption=request.predicted_consumption,
                hour=request.hour,
                day_of_week=request.day_of_week,
                weekend=request.weekend,
                prediction_id=pred_id,
                save_to_db=True
            )
            return OptimizationResponse(**result)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Optimization failed: {str(e)}"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Must provide either 'prediction_id', 'features', or 'predicted_consumption' with 'hour'."
        )


@app.get(
    "/energy/summary",
    tags=["Dashboard"],
    summary="Retrieve aggregate energy KPIs",
    description="Computes and returns key metrics from MySQL (average, peak, latest consumption, and potential savings)."
)
def get_dashboard_summary():
    try:
        summary = get_energy_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve energy summary: {str(e)}"
        )


@app.get(
    "/energy/history",
    tags=["Dashboard"],
    summary="Retrieve historical energy consumption records",
    description="Retrieves smart-meter records from MySQL energy_consumption with customizable limit and sorting."
)
def get_energy_history(limit: int = 100, order: str = "desc", for_chart: bool = False):
    try:
        limit_val = min(max(limit, 1), 500)
        order_clause = "timestamp ASC" if (order.lower() == "asc" or for_chart) else "timestamp DESC"
        records = get_historical_energy_records(limit=limit_val, order_by=order_clause)
        for r in records:
            if hasattr(r["timestamp"], "strftime"):
                r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            # Convert Decimal types to float for clean JSON serialization
            for k, v in r.items():
                if hasattr(v, "__float__") and not isinstance(v, (int, float, bool)):
                    r[k] = float(v)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve energy history: {str(e)}"
        )


@app.get(
    "/predictions",
    tags=["Dashboard"],
    summary="Retrieve recent predictions",
    description="Returns recent prediction events stored in MySQL predictions table."
)
def get_predictions_history(limit: int = 20):
    try:
        limit_val = min(max(limit, 1), 100)
        records = get_recent_predictions(limit=limit_val)
        for r in records:
            for field in ["prediction_time", "target_time", "created_at"]:
                if r.get(field) and hasattr(r[field], "strftime"):
                    r[field] = r[field].strftime("%Y-%m-%d %H:%M:%S")
            for k, v in r.items():
                if hasattr(v, "__float__") and not isinstance(v, (int, float, bool)):
                    r[k] = float(v)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve predictions: {str(e)}"
        )


@app.get(
    "/optimization-results",
    tags=["Dashboard"],
    summary="Retrieve recent optimization recommendations",
    description="Returns recent optimization results stored in MySQL optimization_results table."
)
def get_optimizations_history(limit: int = 20):
    try:
        limit_val = min(max(limit, 1), 100)
        records = get_recent_optimization_results(limit=limit_val)
        for r in records:
            if r.get("created_at") and hasattr(r["created_at"], "strftime"):
                r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            for k, v in r.items():
                if hasattr(v, "__float__") and not isinstance(v, (int, float, bool)):
                    r[k] = float(v)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve optimization results: {str(e)}"
        )


@app.post(
    "/what-if",
    response_model=WhatIfResponse,
    tags=["What-If Simulation"],
    summary="Run a what-if energy consumption simulation",
    description=(
        "Accepts two complete 8-feature sets (base_features and scenario_features), "
        "runs the trained XGBoost model on each, and returns a side-by-side comparison "
        "including: predicted kWh for both scenarios, arithmetic difference, percentage change, "
        "data-driven NORMAL/HIGH/PEAK classification for both (reusing Phase 4 MySQL baseline logic), "
        "and a plain-English interpretation. "
        "This endpoint is purely exploratory — no results are written to the database. "
        "Only the 8 supported forecasting features may be used; concurrent same-period measurements "
        "(reactive power, voltage, etc.) are intentionally excluded."
    )
)
def run_what_if_simulation(request: WhatIfRequest):
    """POST /what-if — dual-scenario prediction comparison."""
    # Verify model is loaded
    if not ml_state["is_loaded"] or ml_state["model"] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forecasting model is not loaded. Cannot run what-if simulation."
        )

    try:
        base_dict = request.base_features.model_dump()
        scenario_dict = request.scenario_features.model_dump()

        result = compute_what_if(
            base_features=base_dict,
            scenario_features=scenario_dict,
            model=ml_state["model"],
            model_name=ml_state["model_name"],
        )

        return WhatIfResponse(**result)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"What-if simulation failed: {str(exc)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
