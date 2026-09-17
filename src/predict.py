"""
src/predict.py
==============
Inference module for genuine next-hour energy consumption forecasting.

Key capabilities:
1. Loads the saved best model (models/best_energy_model.joblib).
2. Loads the exact feature schema (models/feature_names.json).
3. Validates and enforces exact feature ordering.
4. Predicts future energy consumption (in kWh) for single inputs or batch DataFrames.
5. Includes a demonstration script comparing sample predictions with actual values.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Union, Dict, List

MODELS_DIR = "models"
MODEL_FILE = os.path.join(MODELS_DIR, "best_energy_model.joblib")
FEATURES_FILE = os.path.join(MODELS_DIR, "feature_names.json")
METADATA_FILE = os.path.join(MODELS_DIR, "model_metadata.json")


class EnergyPredictor:
    """
    Production-ready predictor enforcing exact feature alignment for energy forecasting.
    """
    def __init__(self, model_path: str = MODEL_FILE, features_path: str = FEATURES_FILE):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at '{model_path}'. Please train models first using 'python src/train_models.py'.")
        if not os.path.exists(features_path):
            raise FileNotFoundError(f"Feature names file not found at '{features_path}'.")

        # Load model using joblib
        self.model = joblib.load(model_path)
        
        # Load required features
        with open(features_path, "r", encoding="utf-8") as f:
            self.feature_names: List[str] = json.load(f)

        # Optional metadata
        self.metadata = {}
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def predict(self, input_data: Union[Dict, List[Dict], pd.DataFrame]) -> np.ndarray:
        """
        Make energy consumption forecasts (kWh) for the next hour.
        
        Parameters:
        -----------
        input_data : dict, list of dicts, or pandas DataFrame
            Contains the 8 required features:
            ['hour', 'day', 'day_of_week', 'month', 'weekend', 'lag_1h_kwh', 'lag_24h_kwh', 'rolling_mean_24h_kwh']
            
        Returns:
        --------
        np.ndarray : Predicted energy consumption in kWh
        """
        # Convert input to DataFrame if necessary
        if isinstance(input_data, dict):
            df_input = pd.DataFrame([input_data])
        elif isinstance(input_data, list):
            df_input = pd.DataFrame(input_data)
        elif isinstance(input_data, pd.DataFrame):
            df_input = input_data.copy()
        else:
            raise TypeError("Input data must be a dictionary, list of dictionaries, or pandas DataFrame.")

        # Check for missing features
        missing = [col for col in self.feature_names if col not in df_input.columns]
        if missing:
            raise ValueError(f"Input is missing required features: {missing}. Required features: {self.feature_names}")

        # Ensure exact column ordering as used during training
        X = df_input[self.feature_names].astype(float)

        # Predict
        predictions = self.model.predict(X)
        return predictions


def run_demo():
    """
    Demonstrate prediction on sample rows from the processed dataset.
    """
    print("=" * 65)
    print("      NEXT-HOUR ENERGY CONSUMPTION PREDICTION DEMO")
    print("=" * 65)

    predictor = EnergyPredictor()
    best_model_name = predictor.metadata.get("best_model_name", "Trained Model")
    print(f"Loaded Model: {best_model_name}")
    print(f"Required Features ({len(predictor.feature_names)}): {predictor.feature_names}\n")

    # Load 5 sample rows from the end of the test set
    data_path = os.path.join("dataset", "processed", "energy_consumption_ml_dataset.csv")
    if not os.path.exists(data_path):
        print("Processed dataset not found for demo.")
        return

    df = pd.read_csv(data_path)
    sample_df = df.tail(5).copy()

    predictions = predictor.predict(sample_df)
    sample_df["predicted_kwh"] = np.round(predictions, 4)
    sample_df["actual_kwh"] = np.round(sample_df["energy_consumption_kwh"], 4)
    sample_df["error_kwh"] = np.round(np.abs(sample_df["actual_kwh"] - sample_df["predicted_kwh"]), 4)

    display_cols = ["timestamp"] + predictor.feature_names[:4] + ["lag_1h_kwh", "actual_kwh", "predicted_kwh", "error_kwh"]
    print("Sample Forecast Results:")
    print(sample_df[display_cols].to_string(index=False))

    # Single dictionary prediction example
    print("\n" + "-" * 65)
    print("Single Input Dictionary Test:")
    single_input = {
        "hour": 18,
        "day": 26,
        "day_of_week": 4,  # Friday
        "month": 11,       # November
        "weekend": 0,
        "lag_1h_kwh": 2.15,
        "lag_24h_kwh": 1.95,
        "rolling_mean_24h_kwh": 1.45
    }
    single_pred = predictor.predict(single_input)[0]
    print("Input parameters:", single_input)
    print(f"--> Forecasted Energy Consumption: {single_pred:.4f} kWh")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_demo()
