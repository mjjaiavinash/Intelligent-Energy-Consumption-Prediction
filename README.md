# Intelligent Energy Consumption Prediction and Optimization
> **College Machine Learning Subject Capstone Project**  
> An end-to-end predictive machine learning platform for next-hour household electrical energy forecasting, data-driven peak shaving optimization, and What-If scenario analysis.

---

## 1. Project Overview

Residential and commercial buildings consume a major portion of generated electrical energy. Because electricity cannot be easily or cheaply stored at scale in typical domestic environments, anticipating demand spikes before they occur is critical for both grid stability and consumer energy cost management.

This project delivers a complete, reproducible **Machine Learning regression methodology** for **next-hour energy consumption forecasting (`energy_consumption_kwh`)**. The system ingests multi-year smart-meter measurements, engineers calendar and auto-regressive lag dynamics while strictly preventing target leakage, evaluates multiple regression algorithms, selects the best-performing model (XGBoost), and connects predictions into downstream optimization and What-If simulation engines.

```
Real Energy Dataset (UCI)
          ↓
  Data Preprocessing (Hourly aggregation, timestamp validation)
          ↓
  Feature Engineering (Calendar dynamics + 1h/24h Lags + 24h Rolling Mean)
          ↓
  Exploratory Data Analysis (Diurnal cycles, seasonality, distribution)
          ↓
  Feature Selection & Leakage Prevention (Strict past-only inputs)
          ↓
  Train Multiple ML Models (Linear Regression, Random Forest, XGBoost)
          ↓
  Chronological Model Evaluation (MAE, MSE, RMSE, R²)
          ↓
  Model Comparison & Benchmarking
          ↓
  XGBoost Final Model Selection
          ↓
  Energy Consumption Prediction (FastAPI)
          ↓
  Data-Driven Optimization (MySQL Baseline vs Forecast)
          ↓
  What-If Scenario Simulation
          ↓
  Interactive Dashboard (React + Vite + Recharts)
```

---

## 2. Problem Statement

Electrical energy consumption is highly non-linear, stochastic, and volatile. It fluctuates based on human routines, work schedules, seasonal climate changes, and simultaneous appliance operation.

Traditional static estimation methods fail to capture short-term demand surges. Predicting next-hour energy usage poses several key challenges:
1. **Diurnal and Weekly Seasonality:** Energy consumption varies dramatically between daytime activity peaks and nighttime baselines, as well as between workdays and weekends.
2. **Auto-regressive Dependencies:** Recent past consumption strongly influences near-future consumption (e.g., HVAC continuous running).
3. **Prevention of Target Leakage:** Concurrent measurements recorded during the forecast hour itself cannot be used for forward forecasting because they are unavailable prior to the forecast interval.

Solving this problem requires an intelligent, data-driven machine learning regression model that operates strictly on historical smart-meter telemetry.

---

## 3. Project Objectives

- **Analyze Historical Energy Data:** Examine multi-year smart-meter observations from the UCI Individual Household Electric Power Consumption benchmark.
- **Perform Data Preprocessing:** Clean, aggregate minute-level measurements into hourly energy values (kWh), and handle missing readings.
- **Engineer Temporal & Auto-regressive Features:** Extract diurnal, weekly, and seasonal calendar signals alongside 1-hour lag, 24-hour lag, and 24-hour rolling averages.
- **Conduct Exploratory Data Analysis (EDA):** Identify consumption patterns, distribution skewness, diurnal shapes, and feature correlations.
- **Train Multiple Regression Algorithms:** Benchmarking Linear Regression, Random Forest Regressor, and XGBoost Regressor under identical experimental conditions.
- **Validate Chronologically Without Shuffling:** Evaluate models using strict forward-in-time train/test splitting (80% train / 20% test).
- **Compare Evaluation Metrics:** Quantify forecasting precision using MAE, MSE, RMSE, and $R^2$.
- **Select the Optimal Model:** Objectively select the model with the lowest error and highest variance explanation.
- **Deploy Predictive REST API:** Serve real-time inference via FastAPI with schema validation and CORS protection.
- **Integrate Data-Driven Optimization:** Identify elevated and peak consumption against historical smart-meter baselines stored in MySQL.
- **Provide What-If Scenario Analysis:** Enable interactive evaluation of hypothetical operational changes and efficiency shifts.

---

## 4. Dataset

The project utilizes the **Individual Household Electric Power Consumption Dataset** from the UCI Machine Learning Repository:
- **Raw Observations:** 2,075,259 minute-level electrical telemetry records.
- **Temporal Span:** December 16, 2006 to November 26, 2010 (~47 months).
- **Measurement Variables:** Global active power (kW), global reactive power (kW), voltage (V), global intensity (A), and sub-metering zones 1, 2, and 3 (Wh).
- **Processed Hourly Dataset:** `dataset/processed/energy_consumption_ml_dataset.csv` contains **34,127 hourly records** with zero missing values.
- **Target Variable:** `energy_consumption_kwh` (hourly energy consumption in kilowatt-hours).

---

## 5. Data Preprocessing

Data preprocessing is automated in `src/preprocess.py`:
1. **Datetime Parsing:** Combines `Date` and `Time` into high-resolution timestamps (`YYYY-MM-DD HH:MM:SS`).
2. **Missing Value Handling:** Semicolon delimiter parsed; `'?'` characters coerced to numeric NaN.
3. **Hourly Aggregation:** Minute-level active power (kW) is resampled to hourly means to produce energy in kilowatt-hours (kWh).
4. **Data Validation:** Checks ensure timestamps are strictly monotonically increasing, missing values are zero, and measurements reside within physically valid boundaries.
5. **Safe File Handling:** Includes automated comparison with the verified processed dataset before writing, preventing silent overwriting of model-aligned datasets.

---

## 6. Feature Engineering

The forecasting engine utilizes strictly **8 machine learning features**:

| Feature Name | Type | Domain / Range | Description & Physical Rationale |
| :--- | :---: | :---: | :--- |
| `hour` | Integer | $0 - 23$ | Diurnal human activity cycle (sleep, cooking, evening peaks). |
| `day` | Integer | $1 - 31$ | Day of the month; reflects monthly billing cycles and routines. |
| `day_of_week` | Integer | $0 - 6$ | Day index (Monday=0, Sunday=6); differentiates weekday vs. weekend patterns. |
| `month` | Integer | $1 - 12$ | Annual seasonality (winter heating vs. summer baseline). |
| `weekend` | Binary | $0 \text{ or } 1$ | Flag indicating Saturday/Sunday lifestyle and occupancy shifts. |
| `lag_1h_kwh` | Float | $\ge 0$ kWh | Energy consumption of the immediate preceding hour ($t-1$). Captures auto-regressive momentum. |
| `lag_24h_kwh` | Float | $\ge 0$ kWh | Energy consumption at the exact same hour yesterday ($t-24$). Captures circadian cycle periodicity. |
| `rolling_mean_24h_kwh` | Float | $\ge 0$ kWh | Rolling mean of the preceding 24 hours (excluding forecast hour). Captures baseline consumption level. |

### Strict Prevention of Target Leakage
Concurrent electrical features (`avg_reactive_power`, `avg_voltage`, `avg_global_intensity`, `sub_metering_1`, `sub_metering_2`, `sub_metering_3`) are retained in the database for historical reporting, but are **strictly excluded** from ML model inputs. Because these quantities are recorded during the forecast hour itself, using them would introduce artificial data leakage and inflate test accuracy.

---

## 7. Exploratory Data Analysis (EDA)

Key empirical insights discovered through exploratory analysis:
- **Diurnal Curve:** Sharp morning peak (~7:00–9:00 AM) and pronounced evening peak (~6:00–9:00 PM), with lowest demand during overnight hours (~2:00–5:00 AM).
- **Weekly Patterns:** Weekend consumption exhibits higher midday usage compared to weekdays, reflecting home occupancy.
- **Seasonal Trend:** Winter months (December to February) display elevated consumption compared to summer months (June to August).
- **Distribution:** Target consumption is positively skewed (mean $\approx 1.09$ kWh, median $\approx 0.77$ kWh, max $= 6.56$ kWh).
- **Correlation:** `lag_1h_kwh` ($r \approx 0.75$) and `rolling_mean_24h_kwh` ($r \approx 0.61$) exhibit the strongest linear correlation with next-hour consumption.

Visualization artifacts are saved in `plots/` and embedded in `notebooks/ML_Project_Complete_Analysis.ipynb`:
- `plots/energy_consumption_over_time.png`
- `plots/actual_vs_predicted.png`
- `plots/model_performance_comparison.png`
- `plots/feature_importance_xgboost.png`
- `plots/feature_importance_random_forest.png`

---

## 8. Machine Learning Methodology

### Chronological Train-Test Split (No Shuffling)
For time-series forecasting, standard random shuffling is invalid because it leaks future information into training. The dataset is partitioned chronologically:
- **Training Set (80%):** Earliest 27,301 hours (Dec 17, 2006 to Feb 10, 2010).
- **Held-Out Test Set (20%):** Latest 6,826 hours (Feb 10, 2010 to Nov 26, 2010).

```
[--------------------- 80% Training Set ---------------------][--- 20% Held-Out Test Set ---]
2006-12-17                                          2010-02-10                      2010-11-26
```

---

## 9. Models Evaluated

Three diverse regression architectures were trained and evaluated on the identical chronological partition:

1. **Linear Regression (Baseline):**
   - Ordinary Least Squares regression assuming linear feature-target relationships.
   - Serves as the benchmark baseline.

2. **Random Forest Regressor (Bagging Ensemble):**
   - Ensemble of 100 independent decision trees (`max_depth=16`, `random_state=42`).
   - Reduces variance and models non-linear interactions across features.

3. **XGBoost Regressor (Gradient Boosting):**
   - Scalable gradient-boosted decision tree algorithm optimizing pseudo-residuals.
   - Hyperparameters: `n_estimators=100`, `learning_rate=0.08`, `max_depth=6`, `subsample=0.8`, `colsample_bytree=0.8`.

---

## 10. Model Evaluation

Models were evaluated on the held-out test set using Mean Absolute Error (MAE), Mean Squared Error (MSE), Root Mean Squared Error (RMSE), and Coefficient of Determination ($R^2$):

| Model | MAE (kWh) | MSE ($\text{kWh}^2$) | RMSE (kWh) | $R^2$ Score | Ranking |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **XGBoost Regressor** | **0.3324** | **0.2286** | **0.4781** | **0.5870** | **Best Model (1st)** |
| **Random Forest Regressor** | 0.3379 | 0.2387 | 0.4886 | 0.5687 | 2nd |
| **Linear Regression** | 0.3807 | 0.2825 | 0.5315 | 0.4896 | 3rd (Baseline) |

---

## 11. Final Model Selection

**XGBoost was objectively selected as the production forecasting model.**

### Scientific Rationale:
- **Lowest Prediction Errors:** Achieved the lowest MAE ($0.3324$ kWh) and lowest RMSE ($0.4781$ kWh) on unseen test data.
- **Highest Explained Variance:** Achieved an $R^2$ of $0.5870$ ($58.7\%$ of variance explained), outperforming Linear Regression by $+9.7\%$ and Random Forest by $+1.8\%$.
- **Robust Generalization:** Gradient boosting with regularization effectively captured non-linear interactions between hour-of-day and recent lag dynamics without overfitting.

The trained model is persisted in `models/best_energy_model.joblib` alongside schema metadata in `models/model_metadata.json`.

---

## 12. Optimization Engine

The machine learning predictions feed directly into a data-driven energy optimization engine:
1. **Dynamic Baseline:** Retrieves the historical mean consumption for the target hour and day-type from MySQL (`energy_consumption`).
2. **Consumption Classification:**
   - **NORMAL:** Predicted $\le \text{Baseline} + 10\%$
   - **HIGH:** Predicted between $\text{Baseline} + 10\%$ and $\text{Baseline} + 30\%$
   - **PEAK:** Predicted $> \text{Baseline} + 30\%$
3. **Actionable Recommendations:** Suggests load shifting (e.g., washing machine, dryer, water heating) to off-peak periods.

> *Clarification:* Potential savings represent analytical estimates benchmarked against historical smart-meter averages; they are not guaranteed savings.

---

## 13. What-If Scenario Simulation

The What-If module enables hypothetical scenario evaluation:
- Compares a **Base scenario** against an adjusted **Scenario feature vector**.
- Users simulate temporal load shifts (e.g., shifting cooking from 7:00 PM to 9:00 PM) or reduced preceding usage.
- The trained XGBoost model predicts both scenarios and computes difference ($\Delta$), percentage change, and status shifts.

> *Methodological Note:* What-If simulation explores changes in the model's supported forecasting inputs. It does not directly simulate individual physical appliances or guarantee real-world energy savings.

---

## 14. System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   React Frontend                       │
│        (Vite + React 18 + Recharts + Lucide Icons)     │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP REST (CORS Restricted)
┌──────────────────────────▼─────────────────────────────┐
│                 FastAPI REST Backend                   │
│        Endpoints: /predict, /optimize, /what-if        │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
┌──────────────▼─────────────┐ ┌───────────▼─────────────┐
│    Trained XGBoost Model   │ │      MySQL Database     │
│ (models/best_energy_model) │ │  (energy_consumption,   │
│   Joblib + 8 ML Features   │ │   predictions, metrics) │
└────────────────────────────┘ └─────────────────────────┘
```

---

## 15. Technology Stack

- **Machine Learning & Data Science:** Python 3.9+, Scikit-Learn, XGBoost, Pandas, NumPy, Joblib.
- **Data Exploration & Plotting:** Matplotlib, Seaborn.
- **Backend Service:** FastAPI, Uvicorn, Pydantic v2.
- **Relational Database:** MySQL 8.0, PyMySQL.
- **Interactive Dashboard:** React 18, Vite, Recharts, Lucide React, Vanilla CSS.

---

## 16. Project Structure

```
Intelligent-Energy-Consumption-Prediction/
├── dataset/
│   ├── raw/
│   │   ├── README.md                           # Source & download instructions for UCI dataset
│   │   └── household_power_consumption.txt     # Raw dataset (excluded from git due to 100MB limit)
│   └── processed/
│       └── energy_consumption_ml_dataset.csv   # 34,127 hourly ML dataset records
├── notebooks/
│   └── ML_Project_Complete_Analysis.ipynb      # Complete 23-section executable ML notebook
├── models/
│   ├── best_energy_model.joblib                # Serialized production XGBoost model
│   ├── feature_names.json                      # Strict 8-feature input schema ordering
│   └── model_metadata.json                     # Training hyperparameters & test metrics
├── plots/
│   ├── actual_vs_predicted.png                 # Test window actual vs predicted chart
│   ├── model_performance_comparison.png        # Bar charts comparing MAE, RMSE, R²
│   ├── energy_consumption_over_time.png        # Historical time-series plot
│   ├── feature_importance_xgboost.png          # XGBoost feature importance
│   └── feature_importance_random_forest.png    # Random Forest feature importance
├── src/
│   ├── preprocess.py                           # Reproducible raw-to-processed pipeline
│   ├── data_analysis.py                        # EDA and dataset validation
│   ├── train_models.py                         # Multi-model training and evaluation pipeline
│   ├── evaluate.py                             # Evaluation metrics calculation
│   ├── predict.py                              # Standalone prediction module
│   ├── optimization.py                         # Baseline derivation and load classification
│   ├── what_if.py                              # What-If scenario comparison engine
│   └── database.py                             # MySQL schema management and CRUD queries
├── api/
│   ├── __init__.py
│   ├── main.py                                 # FastAPI application with CORS & endpoints
│   └── schemas.py                              # Pydantic request/response schemas
├── database/
│   └── schema.sql                              # MySQL DDL schema
├── scripts/
│   ├── build_notebook.py                       # Automated ML notebook generator & runner
│   ├── import_dataset_to_mysql.py              # Batch CSV importer into MySQL
│   ├── test_database.py                        # Database integration tests
│   ├── test_api.py                             # API endpoint test runner
│   ├── test_optimization.py                    # Optimization engine tests
│   └── test_what_if.py                         # What-If simulation test suite
├── frontend/                                   # React + Vite frontend application
├── test_api.py                                 # Root API test suite
├── requirements.txt                            # Python dependencies
├── .env.example                                # Template for environment credentials
├── .gitignore                                  # Git exclusion configuration
└── README.md                                   # Comprehensive ML documentation
```

---

## 17. Installation

### 1. Clone the Repository
```bash
git clone https://github.com/mjjaiavinash/Intelligent-Energy-Consumption-Prediction.git
cd Intelligent-Energy-Consumption-Prediction
```

### 2. Set Up Python Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and set your MySQL credentials:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=energy_prediction
```

---

## 18. Running the Project

### A. Run Reproducible Preprocessing Pipeline
```bash
python src/preprocess.py
```

### B. Explore the Complete ML Notebook
Open and run `notebooks/ML_Project_Complete_Analysis.ipynb` in VS Code or JupyterLab:
```bash
jupyter lab notebooks/ML_Project_Complete_Analysis.ipynb
```

### C. Start FastAPI Backend Service
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation is available at:
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

### D. Start React Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your web browser.

---

## 19. API Endpoints

| Method | Endpoint | Description | Sample Request Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health status, model name, and feature count | None |
| `POST` | `/predict` | Predict next-hour energy consumption (kWh) | `{"hour": 18, "day": 26, "day_of_week": 4, "month": 11, "weekend": 0, "lag_1h_kwh": 1.65, "lag_24h_kwh": 1.72, "rolling_mean_24h_kwh": 1.15}` |
| `POST` | `/optimize` | Evaluate consumption against historical baseline | `{"predicted_consumption": 2.85, "hour": 18, "day_of_week": 4, "weekend": 0}` |
| `POST` | `/what-if` | Run What-If scenario simulation comparison | `{"base_features": {...}, "scenario_features": {...}}` |
| `GET` | `/energy/summary` | Aggregate historical metrics from MySQL | None |
| `GET` | `/energy/history` | Retrieve chronological energy history records | None |

---

## 20. Testing & Verification

Run the automated test suites:

```bash
# 1. Database Integration Tests
python scripts/test_database.py

# 2. FastAPI Endpoint Tests (9/9 passed)
python test_api.py

# 3. Energy Optimization Engine Tests (10/10 passed)
python scripts/test_optimization.py

# 4. What-If Simulation Tests (14/14 passed)
python scripts/test_what_if.py

# 5. Frontend Production Build
cd frontend && npm run build
```

---

## 21. Limitations

1. **Single Household Context:** Dataset observations derive from a single residential smart-meter; cross-building generalization requires transfer learning or retraining.
2. **Lack of Meteorological Variables:** The historical dataset lacks outdoor temperature, solar radiation, and humidity data, which drive HVAC heating/cooling loads.
3. **No Direct Device Control:** The platform delivers analytical forecasts and recommendations without physical hardware relay actuation.
4. **Estimated Savings:** Potential savings represent statistical approximations benchmarked against historical baselines, not guaranteed utility bill savings.
5. **Feature Scope:** What-If scenario exploration is constrained to the 8 engineered features supported by the trained model.

---

## 22. Future Scope

1. **IoT Smart-Meter Telemetry:** Ingest live meter streams via MQTT or Kafka message brokers.
2. **Weather API Integration:** Incorporate ambient temperature, humidity, and solar index as exogenous inputs.
3. **Time-of-Use (ToU) Tariff Optimization:** Optimize electricity cost directly alongside consumption based on dynamic hourly utility pricing.
4. **Walk-Forward Time-Series Cross-Validation:** Evaluate multi-period rolling window performance across changing years.
5. **Automated MLOps Pipeline:** Implement MLflow tracking, drift detection, and automated scheduled retraining.

---

## 23. Conclusion

This project demonstrates a rigorous, end-to-end Machine Learning solution for residential energy forecasting and optimization. By engineering temporal and auto-regressive lag features without data leakage, evaluating multiple regression architectures, and objectively selecting XGBoost ($R^2 = 0.587$, $\text{MAE} = 0.3324$ kWh), the system accurately captures demand dynamics. The machine learning foundation powers the FastAPI backend, MySQL database, data-driven optimization engine, What-If simulator, and React dashboard, providing an actionable platform for smart home energy management.
