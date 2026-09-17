"""
src/evaluate.py
===============
Evaluation utilities and metrics reporting for the energy forecasting models.

Calculates:
- Mean Absolute Error (MAE)
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)
- Coefficient of Determination (R²)

Generates:
- Formatted comparison table
- Model performance comparison bar charts
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_metrics(y_true, y_pred, model_name: str = "Model") -> dict:
    """
    Calculate MAE, MSE, RMSE, and R² for predictions on actual test data.
    Never hardcoded; derived entirely from inputs.
    """
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)

    return {
        "Model": model_name,
        "MAE": round(float(mae), 4),
        "MSE": round(float(mse), 4),
        "RMSE": round(float(rmse), 4),
        "R2": round(float(r2), 4)
    }


def create_comparison_table(metrics_list: list) -> pd.DataFrame:
    """
    Given a list of metric dictionaries, construct a formatted comparison DataFrame.
    """
    df_comparison = pd.DataFrame(metrics_list)
    return df_comparison


def print_comparison_table(df_comparison: pd.DataFrame) -> None:
    """
    Print a clean ASCII comparison table to the console.
    """
    print("\n" + "=" * 65)
    print("                MODEL PERFORMANCE COMPARISON")
    print("=" * 65)
    print(df_comparison.to_string(index=False))
    print("=" * 65 + "\n")


def plot_model_comparison(df_comparison: pd.DataFrame, output_path: str = "plots/model_performance_comparison.png") -> None:
    """
    Generate a clean visual comparison chart showing MAE, RMSE, and R2 across models.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    models = df_comparison["Model"].tolist()
    mae_vals = df_comparison["MAE"].tolist()
    rmse_vals = df_comparison["RMSE"].tolist()
    r2_vals = df_comparison["R2"].tolist()

    x = np.arange(len(models))
    width = 0.25

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Bar plots for error metrics (lower is better)
    bars1 = ax1.bar(x - width/2, mae_vals, width, label="MAE (kWh)", color="#2b5c8f", alpha=0.9)
    bars2 = ax1.bar(x + width/2, rmse_vals, width, label="RMSE (kWh)", color="#e05a47", alpha=0.9)

    ax1.set_xlabel("Regression Models", fontsize=12, fontweight="bold", labelpad=10)
    ax1.set_ylabel("Error in kWh (Lower is better)", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, fontsize=11)
    ax1.set_ylim(0, max(rmse_vals) * 1.35)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    # Annotate bars with exact values
    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(f"{h:.4f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")
    for bar in bars2:
        h = bar.get_height()
        ax1.annotate(f"{h:.4f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Line overlay for R² score (higher is better)
    ax2 = ax1.twinx()
    line = ax2.plot(x, r2_vals, color="#2ca02c", marker="o", linewidth=2.5, markersize=8, label="R² Score (Higher is better)")
    ax2.set_ylabel("R² Score", fontsize=12, color="#2ca02c", fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#2ca02c")
    ax2.set_ylim(min(min(r2_vals) * 0.8, 0.0), 1.05)

    for i, txt in enumerate(r2_vals):
        ax2.annotate(f"R²: {txt:.4f}", (x[i], txt), textcoords="offset points", xytext=(0, 10),
                     ha="center", fontsize=10, fontweight="bold", color="#1c6b1c")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.9)

    plt.title("Model Performance Comparison: MAE, RMSE, and R²", fontsize=14, fontweight="bold", pad=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"--> Saved model comparison plot to: {output_path}")
