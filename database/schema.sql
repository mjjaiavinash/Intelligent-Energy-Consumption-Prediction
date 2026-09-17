-- ====================================================================
-- Database Schema: Intelligent Energy Consumption Prediction & Optimization
-- Database: energy_prediction
-- ====================================================================

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS energy_prediction
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE energy_prediction;

-- ====================================================================
-- Table 1: energy_consumption
-- Stores historical hourly smart-meter energy consumption and lag features.
-- ====================================================================
CREATE TABLE IF NOT EXISTS energy_consumption (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    hour TINYINT,
    day TINYINT,
    day_of_week TINYINT,
    month TINYINT,
    weekend BOOLEAN,
    lag_1h_kwh DECIMAL(10,4),
    lag_24h_kwh DECIMAL(10,4),
    rolling_mean_24h_kwh DECIMAL(10,4),
    energy_consumption_kwh DECIMAL(10,4),
    INDEX idx_timestamp (timestamp),
    UNIQUE KEY uq_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- Table 2: predictions
-- Stores model prediction events, timestamps, and model provenance.
-- ====================================================================
CREATE TABLE IF NOT EXISTS predictions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prediction_time DATETIME NOT NULL,
    target_time DATETIME NULL,
    predicted_energy_kwh DECIMAL(10,4) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prediction_time (prediction_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- Table 3: optimization_results
-- Stores energy optimization recommendations and estimated savings.
-- ====================================================================
CREATE TABLE IF NOT EXISTS optimization_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prediction_id BIGINT NULL,
    baseline_consumption DECIMAL(10,4),
    predicted_consumption DECIMAL(10,4),
    potential_saving DECIMAL(10,4),
    saving_percentage DECIMAL(6,2),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_opt_prediction FOREIGN KEY (prediction_id) 
        REFERENCES predictions(id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- Table 4: model_metrics
-- Stores offline training and evaluation metrics across model iterations.
-- ====================================================================
CREATE TABLE IF NOT EXISTS model_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    mae DECIMAL(10,6),
    mse DECIMAL(10,6),
    rmse DECIMAL(10,6),
    r2_score DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
