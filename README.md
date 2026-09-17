# Intelligent Energy Consumption Prediction and Optimization

A comprehensive Machine Learning and API system for **next-hour household energy consumption forecasting** (`energy_consumption_kwh`) using historical consumption dynamics and temporal calendar features.

---

## Project Overview

- **Phase 1: ML Regression Pipeline**: Data validation, chronological splitting, multi-model benchmarking (Linear Regression, Random Forest, XGBoost), feature importance analysis, and model persistence.
- **Phase 2: Prediction API**: High-performance FastAPI backend exposing the trained XGBoost model for next-hour predictions with Pydantic validation, strict feature alignment, and automated testing.

---

## Genuine Next-Hour Forecasting Architecture

To avoid data leakage and ensure realistic production deployment:
- **Included 8 Forecasting Features**:
  - `hour`, `day`, `day_of_week`, `month`, `weekend` (Calendar context)
  - `lag_1h_kwh` (Energy consumption in immediate preceding hour)
  - `lag_24h_kwh` (Energy consumption at same hour on previous day)
  - `rolling_mean_24h_kwh` (Moving average consumption over past 24 hours)

- **Excluded Same-Period Variables**:
  - `avg_reactive_power`, `avg_voltage`, `avg_global_intensity`, `sub_metering_1`, `sub_metering_2`, `sub_metering_3`
  - *Rationale*: Concurrent measurements are recorded during the predicted hour itself. Using them as forecast features would introduce artificial data leakage.

---

## Project Directory Structure

```
Intelligent-Energy-Consumption-Prediction/
│
├── api/
│   ├── __init__.py
│   ├── schemas.py                              # Pydantic input/output schemas with bounds
│   └── main.py                                 # FastAPI application with /health & /predict
│
├── dataset/
│   ├── processed/
│   │   └── energy_consumption_ml_dataset.csv   # 34,127 hourly records (read-only)
│   └── raw/
│       └── household_power_consumption.txt     # Raw dataset
│
├── models/
│   ├── best_energy_model.joblib                # Persisted XGBoost model
│   ├── feature_names.json                      # Strict 8-feature schema & ordering
│   └── model_metadata.json                     # Training & test evaluation metrics
│
├── plots/
│   ├── actual_vs_predicted.png                 # 7-day test window comparison
│   ├── model_performance_comparison.png        # Bar chart comparing MAE, RMSE, R²
│   ├── energy_consumption_over_time.png        # Historical energy trend (2006-2010)
│   ├── feature_importance_random_forest.png    # Random Forest feature importance
│   └── feature_importance_xgboost.png          # XGBoost feature importance
│
├── src/
│   ├── __init__.py
│   ├── data_analysis.py                        # Dataset validation and EDA
│   ├── evaluate.py                             # Metrics calculation and comparison table
│   ├── train_models.py                         # Chronological split, model training & evaluation
│   └── predict.py                              # Inference script with feature alignment
│
├── test_api.py                                 # Automated FastAPI test suite (5/5 tests)
├── requirements.txt                            # Python dependencies
└── README.md                                   # Documentation & execution instructions
```

---

## Installation & Setup

1. Clone or open the repository.
2. Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Running Phase 1 (ML Pipeline)

```bash
# 1. Validate dataset & generate historical energy consumption plot
python src/data_analysis.py

# 2. Train models, evaluate on chronological test split, and persist best model
python src/train_models.py

# 3. Test standalone inference module
python src/predict.py
```

### Model Benchmark Results:

| Model | MAE (kWh) | MSE | RMSE (kWh) | R² Score |
| :--- | :---: | :---: | :---: | :---: |
| Linear Regression | 0.3807 | 0.2825 | 0.5315 | 0.4896 |
| Random Forest | 0.3379 | 0.2387 | 0.4886 | 0.5687 |
| **XGBoost (Selected Best)** | **0.3324** | **0.2286** | **0.4781** | **0.5870** |

---

## Running Phase 2 (FastAPI Backend)

### 1. Start the API Server
Run with Uvicorn:
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
Or directly using Python:
```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

The service will start on `http://127.0.0.1:8000`.

### 2. Interactive Documentation
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints

### 1. Health Check
- **Endpoint**: `GET /health`
- **Description**: Verifies that the API service is running and confirms the model is loaded in memory.
- **Sample Request**:
```bash
curl -X GET "http://127.0.0.1:8000/health"
```
- **Sample Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "XGBoost",
  "features_count": 8,
  "version": "1.0.0"
}
```

---

### 2. Feature-Level Energy Prediction Service
- **Endpoint**: `POST /predict`
- **Description**: Feature-level prediction service that accepts the 8 operational features (including historical lags and rolling averages) and returns the model's predicted energy consumption in kWh for those given conditions. *(Note: This service accepts input features directly; automated retrieval of historical lag values will be handled by the database/MySQL layer in a subsequent phase).*
- **Sample Request**:
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
           "hour": 18,
           "day": 26,
           "day_of_week": 4,
           "month": 11,
           "weekend": 0,
           "lag_1h_kwh": 2.15,
           "lag_24h_kwh": 1.95,
           "rolling_mean_24h_kwh": 1.45
         }'
```
- **Sample Response**:
```json
{
  "predicted_energy_kwh": 2.385,
  "model_name": "XGBoost",
  "unit": "kWh",
  "status": "success"
}
```

---

## Running Automated Tests

Run the automated test suite to verify model loading, health status, prediction logic, and input schema validation:
```bash
python test_api.py
```
Outputs:
- **Test 1**: Verify Model Loading at Startup (`[PASS]`)
- **Test 2**: GET /health Endpoint (`[PASS]`)
- **Test 3**: POST /predict with Valid Payload (`[PASS]`)
- **Test 4**: POST /predict with Out-of-Range Field (`[PASS]`, rejected with HTTP 422)
- **Test 5**: POST /predict with Missing Required Field (`[PASS]`, rejected with HTTP 422)

---

## Phase 3: MySQL Database Integration Guide

Phase 3 integrates MySQL database storage (`energy_prediction`) for storing continuous consumption time series, prediction audits, model metrics, and future optimization logs.

### 1. How to Install MySQL
- Download and run the official **MySQL Community Server 8.0** and **MySQL Workbench** installer from: [https://dev.mysql.com/downloads/installer/](https://dev.mysql.com/downloads/installer/)
- During installation, set the root password and ensure the Windows service (e.g. `MySQL80`) is set to start automatically.
- Ensure the MySQL command-line client is available in PATH (`C:\Program Files\MySQL\MySQL Server 8.0\bin`).

### 2. How to Configure Environment Variables (`.env`)
1. Duplicate the `.env.example` file to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your local MySQL root password:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_actual_mysql_password
   MYSQL_DATABASE=energy_prediction
   ```
   *(Note: `.env` is ignored by version control to keep your credentials safe).*

### 3. How to Create the Database Using `schema.sql`
You can initialize the schema using either the MySQL command-line client or MySQL Workbench:

**Option A: Using MySQL Command Line**
```bash
mysql -u root -p < database/schema.sql
```
*(Enter your MySQL password when prompted).*

**Option B: Using MySQL Workbench**
1. Open MySQL Workbench and connect to your local MySQL connection.
2. Go to **File -> Open SQL Script...** and select `database/schema.sql`.
3. Click the **Execute (Lightning bolt)** icon to run the complete script.
4. Refresh the **Schemas** panel on the left to see the `energy_prediction` database and its 4 tables:
   - `energy_consumption`
   - `predictions`
   - `optimization_results`
   - `model_metrics`

### 4. How to Test the Database Connection
Run the automated database test script:
```bash
python scripts/test_database.py
```
This script validates:
- Connection to the MySQL server
- Existence of all 4 required tables
- Execution of sample `SELECT` count queries
- Read and write capability for model metrics and predictions

### 5. How to Import the CSV Dataset into MySQL
Run the batch dataset import script:
```bash
python scripts/import_dataset_to_mysql.py
```
- Reads the read-only file `dataset/processed/energy_consumption_ml_dataset.csv`.
- Automatically calls `init_db()` to ensure tables exist.
- Performs batch inserts in chunks of 1,000 rows.
- Uses `ON DUPLICATE KEY UPDATE` to safely avoid duplicate timestamp errors.
- Displays a real-time progress bar, throughput speed, and an import summary report.

### 6. How to Verify Imported Records Using MySQL Workbench
1. In MySQL Workbench, double-click `energy_prediction` to make it the active database.
2. In a SQL Query tab, execute:
   ```sql
   -- Check total imported row count (expected: 34,127 rows)
   SELECT COUNT(*) AS total_records FROM energy_consumption;

   -- Inspect the first 10 chronological energy records
   SELECT * FROM energy_consumption ORDER BY timestamp ASC LIMIT 10;

   -- Inspect the latest records
   SELECT * FROM energy_consumption ORDER BY timestamp DESC LIMIT 10;
   ```
3. Right-click the `energy_consumption` table in the sidebar and select **Table Inspector** to inspect table size, indexes (`idx_timestamp`, `uq_timestamp`), and storage engine (`InnoDB`).

---

## Phase 4: Data-Driven Energy Optimization Engine

Phase 4 introduces an explainable, data-driven optimization module that compares forecasted consumption against historical MySQL smart-meter baselines, quantifies potential savings, classifies operational consumption tiers, and persists recommendations.

### Optimization Workflow
1. **Historical Baseline**: Queries actual records from `energy_consumption` for matching `hour`, `day_of_week`, and `weekend` patterns.
2. **Excess Calculation**: `excess_consumption = max(predicted_consumption - baseline_consumption, 0.0)`.
3. **Saving Percentage**: `(excess_consumption / predicted_consumption) * 100` if `predicted > 0` and `excess > 0`.
4. **Data-Driven Classification**:
   - `NORMAL`: Consumption is within historical bounds ($P \le B + 0.5 \times \sigma$).
   - `HIGH`: Moderately elevated consumption ($B + 0.5 \times \sigma < P \le B + 1.5 \times \sigma$).
   - `PEAK`: Significant consumption peak ($P > B + 1.5 \times \sigma$).
5. **Actionable Recommendations**: Conservative advice recommending flexible load reductions or shifting during high/peak periods.
6. **Persistence**: Saves records into `optimization_results` linked via foreign key to `predictions(id)`.

### Running Optimization Tests
```bash
python scripts/test_optimization.py
```
Validates:
- Real baseline extraction from MySQL (`34,127` rows)
- Excess and saving percentage math
- NORMAL / HIGH / PEAK classifications
- Recommendation text generation
- Foreign-key linked insertion into `optimization_results`
- API `POST /optimize` direct and feature-driven requests
- Input validation & HTTP 422 error handling

### API Optimization Endpoint
- **Route**: `POST /optimize`
- **Sample Request**:
```bash
curl -X POST "http://127.0.0.1:8000/optimize" \
     -H "Content-Type: application/json" \
     -d '{
           "predicted_consumption": 2.385,
           "hour": 18,
           "day_of_week": 4,
           "weekend": 0
         }'
```
- **Sample Response**:
```json
{
  "prediction_id": 4,
  "baseline_consumption": 1.1927,
  "predicted_consumption": 2.385,
  "excess_consumption": 1.1923,
  "potential_saving": 1.1923,
  "saving_percentage": 49.99,
  "status": "HIGH",
  "recommendation": "Moderately elevated energy consumption detected (1.19 kWh above historical baseline). Consider reducing or shifting flexible energy usage during this period (potential saving: 50.0%).",
  "unit": "kWh"
}
```

---

## Phase 5: Energy Consumption Web Dashboard

Phase 5 introduces an interactive, responsive web dashboard built with **React**, **Vite**, and **Recharts**, connecting directly to the FastAPI backend:

- **Live MySQL-Backed KPI Cards**: Total records (34,127), historical average consumption, historical peak, latest recorded consumption, average potential savings, and optimization frequency.
- **Interactive Consumption Trend Chart**: Recharts line chart displaying historical records with dynamic time-range filtering (24h, 7d, 30d), tooltips, and threshold indicators.
- **Next-Hour Prediction Panel**: Form accepting the 8 XGBoost features, with a "Load Latest from DB" shortcut and instant ML inference display.
- **Optimization Panel**: Live evaluation of consumption against MySQL baseline, status badges (`NORMAL`, `HIGH`, `PEAK`), and recommendations.
- **Historical Data Table**: Paginated view of real historical smart-meter records with status indicators.

### Running the Frontend Dashboard
```bash
cd frontend
npm run dev
```
Access the dashboard at: `http://localhost:5173`

---

## Phase 6: What-If Energy Consumption Simulation

Phase 6 adds an exploratory **What-If Simulation** engine and interactive dashboard component. Users and grid operators can simulate changes in operating schedules, calendar conditions, or previous-period consumption levels to understand the predicted impact before making real-world operational changes.

### Architectural Principles
1. **Strict 8-Feature Compatibility**: Uses only the trained XGBoost features (`hour`, `day`, `day_of_week`, `month`, `weekend`, `lag_1h_kwh`, `lag_24h_kwh`, `rolling_mean_24h_kwh`). No synthetic or unmodeled parameters (e.g. temperature or occupancy) are introduced.
2. **Ephemeral & Exploratory**: What-if simulations are purely analytical and **never written to MySQL**, preventing cluttering of historical prediction logs.
3. **Transparent & Safe Mathematics**:
   - $\text{Difference} = \hat{Y}_{\text{scenario}} - \hat{Y}_{\text{base}}$
   - $\text{Percentage Change} = \frac{\hat{Y}_{\text{scenario}} - \hat{Y}_{\text{base}}}{\hat{Y}_{\text{base}}} \times 100$ (with zero-division safeguard)
4. **Unified Classification**: Reuses Phase 4 historical baseline calculation and standard deviation tiering (`NORMAL`, `HIGH`, `PEAK`).
5. **Clear Language**: All interpretation and narrative texts explicitly specify values are *model-predicted exploratory estimates*, not guaranteed outcomes.

### API Endpoint: `POST /what-if`

#### Sample Request Payload:
```json
{
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
```

#### Sample Response:
```json
{
  "base_prediction_kwh": 2.0051,
  "scenario_prediction_kwh": 1.7415,
  "difference_kwh": -0.2636,
  "percentage_change": -13.15,
  "base_status": "HIGH",
  "scenario_status": "NORMAL",
  "base_baseline_kwh": 1.1927,
  "scenario_baseline_kwh": 1.5668,
  "interpretation": "The scenario predicts lower energy consumption by 0.264 kWh (13.15%) compared to the base scenario (2.005 kWh -> 1.742 kWh). The predicted consumption category changes from HIGH (base) to NORMAL (scenario). This is a predicted improvement in the consumption tier. Note: These are model-predicted values - not guaranteed real-world outcomes.",
  "model_name": "XGBoost",
  "unit": "kWh"
}
```

### Running Phase 6 Verification Tests
```bash
# 1. Run the comprehensive 14-test What-If test suite
python scripts/test_what_if.py

# 2. Run backend regression test suite
python test_api.py

# 3. Verify health and summary endpoints
python -c "import requests; print(requests.get('http://localhost:8000/health').json()); print(requests.get('http://localhost:8000/energy/summary').json())"
```



