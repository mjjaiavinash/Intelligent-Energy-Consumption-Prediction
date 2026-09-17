"""
src/train_models.py
===================
Training, evaluation, model selection, and visualization pipeline for
genuine next-hour energy consumption forecasting.

Feature Selection Rationale:
- Primary forecasting features (8 features):
  ['hour', 'day', 'day_of_week', 'month', 'weekend', 'lag_1h_kwh', 'lag_24h_kwh', 'rolling_mean_24h_kwh']
- Excluded same-period features:
  ['avg_reactive_power', 'avg_voltage', 'avg_global_intensity', 'sub_metering_1', 'sub_metering_2', 'sub_metering_3']
  These concurrent variables are measured during the predicted hour itself and are not
  known ahead of time in a realistic deployment. Using them would cause data leakage.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from evaluate import calculate_metrics, create_comparison_table, print_comparison_table, plot_model_comparison

# Paths
DATA_PATH = os.path.join("dataset", "processed", "energy_consumption_ml_dataset.csv")
MODELS_DIR = "models"
PLOTS_DIR = "plots"

# Target variable
TARGET_COL = "energy_consumption_kwh"

# Strictly 8 historical and calendar forecasting features
FEATURE_COLS = [
    "hour",
    "day",
    "day_of_week",
    "month",
    "weekend",
    "lag_1h_kwh",
    "lag_24h_kwh",
    "rolling_mean_24h_kwh"
]


def load_and_split_data(data_path: str = DATA_PATH, train_ratio: float = 0.8):
    """
    Load dataset and perform chronological train/test split (no shuffling).
    """
    print(f"--> Reading dataset from: {data_path}")
    df = pd.read_csv(data_path)

    # Verify timestamp ordering
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    total_samples = len(df)
    split_index = int(total_samples * train_ratio)

    X_train = X.iloc[:split_index].copy()
    y_train = y.iloc[:split_index].copy()
    X_test = X.iloc[split_index:].copy()
    y_test = y.iloc[split_index:].copy()

    train_dates = (df["timestamp"].iloc[0].strftime("%Y-%m-%d"), df["timestamp"].iloc[split_index - 1].strftime("%Y-%m-%d"))
    test_dates = (df["timestamp"].iloc[split_index].strftime("%Y-%m-%d"), df["timestamp"].iloc[-1].strftime("%Y-%m-%d"))

    print(f"--> Chronological Split Completed:")
    print(f"    Total samples : {total_samples:,}")
    print(f"    Train samples : {len(X_train):,} ({train_ratio*100:.0f}%) [{train_dates[0]} to {train_dates[1]}]")
    print(f"    Test samples  : {len(X_test):,} ({(1-train_ratio)*100:.0f}%) [{test_dates[0]} to {test_dates[1]}]")
    print(f"    Features ({len(FEATURE_COLS)}): {FEATURE_COLS}")
    print(f"    Target: {TARGET_COL}\n")

    return X_train, X_test, y_train, y_test, df.iloc[split_index:]["timestamp"]


def train_models(X_train, y_train):
    """
    Train Linear Regression, Random Forest, and XGBoost models.
    """
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=16,
            random_state=42,
            n_jobs=-1
        ),
        "XGBoost": XGBRegressor(
            n_estimators=100,
            learning_rate=0.08,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
    }

    trained_models = {}
    for name, model in models.items():
        print(f"--> Training {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model
        print(f"    {name} training completed.")

    return trained_models


def evaluate_models(trained_models, X_test, y_test):
    """
    Evaluate all models on the test set and collect metrics and predictions.
    """
    metrics_list = []
    predictions = {}

    for name, model in trained_models.items():
        preds = model.predict(X_test)
        predictions[name] = preds
        metrics = calculate_metrics(y_test, preds, model_name=name)
        metrics_list.append(metrics)

    df_comparison = create_comparison_table(metrics_list)
    return df_comparison, predictions


def plot_actual_vs_predicted(y_test, predictions, timestamps, best_model_name: str, output_path: str = "plots/actual_vs_predicted.png"):
    """
    Generate an Actual vs Predicted comparison plot on a 168-hour (1 week) representative
    test window so hourly cycles and predictions are distinct and readable.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Select a 168-hour window (7 days) for high-resolution visual comparison
    window = 168
    y_true_window = y_test.iloc[:window].values
    time_window = timestamps.iloc[:window]

    plt.figure(figsize=(15, 6))
    plt.plot(time_window, y_true_window, label="Actual Energy Consumption", color="#111111", linewidth=2.0, alpha=0.9)

    colors = {
        "Linear Regression": "#1f77b4",
        "Random Forest": "#2ca02c",
        "XGBoost": "#d62728"
    }

    for name, preds in predictions.items():
        pred_window = preds[:window]
        is_best = (name == best_model_name)
        lw = 2.0 if is_best else 1.2
        ls = "-" if is_best else "--"
        label_str = f"{name} (Best Model)" if is_best else name
        plt.plot(time_window, pred_window, label=label_str, color=colors.get(name, "#7f7f7f"),
                 linewidth=lw, linestyle=ls, alpha=0.85)

    plt.title(f"Actual vs Predicted Hourly Energy Consumption (7-Day Sample Window)\nBest Model: {best_model_name}",
              fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Date and Time", fontsize=12)
    plt.ylabel("Energy Consumption (kWh)", fontsize=12)
    plt.legend(loc="upper right", fontsize=11, framealpha=0.9)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"--> Saved Actual vs Predicted plot to: {output_path}")


def plot_feature_importance(model, feature_names, model_name: str, output_path: str):
    """
    Plot and save feature importances for tree-based models (Random Forest, XGBoost).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    importances = model.feature_importances_

    # Sort descending
    indices = np.argsort(importances)
    sorted_features = [feature_names[i] for i in indices]
    sorted_importances = importances[indices]

    plt.figure(figsize=(9, 5.5))
    bar_color = "#2ca02c" if "Forest" in model_name else "#d62728"
    bars = plt.barh(range(len(sorted_features)), sorted_importances, color=bar_color, alpha=0.85, edgecolor="#333333")
    plt.yticks(range(len(sorted_features)), sorted_features, fontsize=11)
    plt.xlabel("Relative Importance Score", fontsize=12, fontweight="bold")
    plt.title(f"Feature Importance - {model_name} (Forecasting Features)", fontsize=13, fontweight="bold", pad=12)
    plt.grid(axis="x", linestyle="--", alpha=0.5)

    # Annotate importance values
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 0.005, bar.get_y() + bar.get_height()/2, f"{w:.4f}",
                 va="center", ha="left", fontsize=9, fontweight="bold")

    plt.xlim(0, max(sorted_importances) * 1.18)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"--> Saved {model_name} feature importance plot to: {output_path}")


def save_artifacts(best_model, best_model_name: str, df_comparison: pd.DataFrame, feature_names: list):
    """
    Save best model with joblib, and feature names + metadata to JSON files.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    # 1. Save model with joblib
    model_path = os.path.join(MODELS_DIR, "best_energy_model.joblib")
    joblib.dump(best_model, model_path)
    print(f"--> Saved best model ({best_model_name}) to: {model_path}")

    # 2. Save feature names / ordering
    feature_path = os.path.join(MODELS_DIR, "feature_names.json")
    with open(feature_path, "w", encoding="utf-8") as f:
        json.dump(feature_names, f, indent=4)
    print(f"--> Saved feature names ordering to: {feature_path}")

    # 3. Save comprehensive metadata
    best_metrics = df_comparison[df_comparison["Model"] == best_model_name].iloc[0].to_dict()
    metadata = {
        "project": "Intelligent Energy Consumption Prediction and Optimization",
        "phase": 1,
        "task": "Next-hour energy consumption forecasting",
        "best_model_name": best_model_name,
        "target_variable": TARGET_COL,
        "features": feature_names,
        "excluded_features": [
            "avg_reactive_power",
            "avg_voltage",
            "avg_global_intensity",
            "sub_metering_1",
            "sub_metering_2",
            "sub_metering_3"
        ],
        "rationale_for_exclusion": "Concurrent measurements from the forecast hour are excluded to prevent data leakage in genuine next-hour forecasting.",
        "test_metrics": best_metrics,
        "all_model_metrics": df_comparison.to_dict(orient="records")
    }

    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"--> Saved model metadata to: {metadata_path}")


def main():
    print("=" * 65)
    print("  PHASE 1: MACHINE LEARNING MODEL TRAINING & COMPARISON")
    print("=" * 65 + "\n")

    # 1. Load and chronologically split data
    X_train, X_test, y_train, y_test, test_timestamps = load_and_split_data()

    # 2. Train all 3 models
    trained_models = train_models(X_train, y_train)

    # 3. Evaluate models on test data
    df_comparison, predictions = evaluate_models(trained_models, X_test, y_test)

    # 4. Display comparison table
    print_comparison_table(df_comparison)

    # 5. Select best model based primarily on RMSE (with lowest MAE and highest R2)
    df_sorted = df_comparison.sort_values(by=["RMSE", "MAE"], ascending=[True, True])
    best_model_name = df_sorted.iloc[0]["Model"]
    best_model = trained_models[best_model_name]
    best_rmse = df_sorted.iloc[0]["RMSE"]
    best_mae = df_sorted.iloc[0]["MAE"]
    best_r2 = df_sorted.iloc[0]["R2"]

    print(f"[BEST MODEL SELECTED]: {best_model_name}")
    print(f"Criteria: Lowest RMSE ({best_rmse:.4f} kWh), Lowest MAE ({best_mae:.4f} kWh), Highest R² ({best_r2:.4f})\n")

    # 6. Generate plots
    plot_actual_vs_predicted(y_test, predictions, test_timestamps, best_model_name)
    plot_model_comparison(df_comparison)
    plot_feature_importance(trained_models["Random Forest"], FEATURE_COLS, "Random Forest", "plots/feature_importance_random_forest.png")
    plot_feature_importance(trained_models["XGBoost"], FEATURE_COLS, "XGBoost", "plots/feature_importance_xgboost.png")

    # 7. Save model and metadata
    save_artifacts(best_model, best_model_name, df_comparison, FEATURE_COLS)

    print("\n[SUCCESS] Phase 1 model training and persistence completed successfully!\n")


if __name__ == "__main__":
    main()
