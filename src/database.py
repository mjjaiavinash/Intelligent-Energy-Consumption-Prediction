"""
src/database.py
===============
MySQL Database utility module for Intelligent Energy Consumption Prediction.

Handles:
- Secure connection management using environment variables (python-dotenv).
- Batch insertion of energy consumption time-series data.
- Insertion of prediction logs, optimization recommendations, and model metrics.
- Querying historical consumption records and recent prediction logs.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
import mysql.connector
from mysql.connector import Error, MySQLConnection
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


def get_db_config(use_database: bool = True) -> Dict[str, Any]:
    """
    Retrieve database configuration parameters securely from environment variables.
    Never hardcodes passwords or sensitive credentials.
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "energy_prediction")

    config = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
    }

    if use_database and database:
        config["database"] = database

    return config


def get_connection(use_database: bool = True) -> MySQLConnection:
    """
    Establish and return a connection to the MySQL server.
    Raises RuntimeError with clear guidance if connection fails.
    """
    config = get_db_config(use_database=use_database)
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except Error as e:
        db_info = f"{config.get('user')}@{config.get('host')}:{config.get('port')}"
        if use_database:
            db_info += f"/{config.get('database')}"
        raise RuntimeError(
            f"Failed to connect to MySQL server ({db_info}): {e}\n"
            "Please ensure MySQL is running and your .env file contains valid credentials "
            "(refer to .env.example for required variables)."
        ) from e


def init_db(schema_path: str = "database/schema.sql") -> None:
    """
    Execute the schema.sql script to initialize the database and create tables.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    # First connect without specifying database to ensure database creation
    conn = get_connection(use_database=False)
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        cursor = conn.cursor()
        
        # Split script into individual SQL statements by semicolon
        # Ignore comments and empty statements
        statements = []
        for raw_stmt in sql_script.split(";"):
            clean_lines = [
                line for line in raw_stmt.splitlines() 
                if not line.strip().startswith("--") and not line.strip().startswith("#")
            ]
            clean_stmt = "\n".join(clean_lines).strip()
            if clean_stmt:
                statements.append(clean_stmt)

        for stmt in statements:
            cursor.execute(stmt)

        conn.commit()
        print(f"--> [SUCCESS] Database and tables successfully initialized from {schema_path}.")
    finally:
        conn.close()


def insert_energy_records(records: List[Dict[str, Any]], batch_size: int = 1000) -> Tuple[int, int]:
    """
    Batch insert energy consumption records into the 'energy_consumption' table.
    Safely handles duplicate timestamps by updating values on duplicate key.

    Returns:
    --------
    (successful_records, failed_records) : Tuple[int, int]
    """
    if not records:
        return 0, 0

    query = """
        INSERT INTO energy_consumption (
            timestamp, hour, day, day_of_week, month, weekend,
            lag_1h_kwh, lag_24h_kwh, rolling_mean_24h_kwh, energy_consumption_kwh
        ) VALUES (
            %(timestamp)s, %(hour)s, %(day)s, %(day_of_week)s, %(month)s, %(weekend)s,
            %(lag_1h_kwh)s, %(lag_24h_kwh)s, %(rolling_mean_24h_kwh)s, %(energy_consumption_kwh)s
        )
        ON DUPLICATE KEY UPDATE
            hour = VALUES(hour),
            day = VALUES(day),
            day_of_week = VALUES(day_of_week),
            month = VALUES(month),
            weekend = VALUES(weekend),
            lag_1h_kwh = VALUES(lag_1h_kwh),
            lag_24h_kwh = VALUES(lag_24h_kwh),
            rolling_mean_24h_kwh = VALUES(rolling_mean_24h_kwh),
            energy_consumption_kwh = VALUES(energy_consumption_kwh);
    """

    conn = get_connection(use_database=True)
    successful = 0
    failed = 0

    try:
        cursor = conn.cursor()
        total = len(records)

        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]
            try:
                cursor.executemany(query, batch)
                conn.commit()
                successful += len(batch)
            except Error as batch_err:
                print(f"    [WARN] Error inserting batch {i} to {i+len(batch)}: {batch_err}")
                conn.rollback()
                failed += len(batch)

        return successful, failed
    finally:
        conn.close()


def insert_prediction(
    predicted_energy_kwh: float,
    model_name: str,
    prediction_time: Optional[Any] = None,
    target_time: Optional[Any] = None
) -> int:
    """
    Insert a prediction record into the 'predictions' table.
    Returns the generated record ID.
    """
    import datetime
    if prediction_time is None:
        prediction_time = datetime.datetime.now()

    query = """
        INSERT INTO predictions (
            prediction_time, target_time, predicted_energy_kwh, model_name
        ) VALUES (%s, %s, %s, %s);
    """

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor()
        cursor.execute(query, (prediction_time, target_time, predicted_energy_kwh, model_name))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_optimization_result(
    prediction_id: Optional[int],
    baseline_consumption: float,
    predicted_consumption: float,
    potential_saving: float,
    saving_percentage: float,
    recommendation: str
) -> int:
    """
    Insert an optimization recommendation into the 'optimization_results' table.
    Returns the generated record ID.
    """
    query = """
        INSERT INTO optimization_results (
            prediction_id, baseline_consumption, predicted_consumption,
            potential_saving, saving_percentage, recommendation
        ) VALUES (%s, %s, %s, %s, %s, %s);
    """

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor()
        cursor.execute(query, (
            prediction_id,
            baseline_consumption,
            predicted_consumption,
            potential_saving,
            saving_percentage,
            recommendation
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_model_metrics(
    model_name: str,
    mae: float,
    mse: float,
    rmse: float,
    r2_score: float
) -> int:
    """
    Insert model evaluation metrics into the 'model_metrics' table.
    Returns the generated record ID.
    """
    query = """
        INSERT INTO model_metrics (
            model_name, mae, mse, rmse, r2_score
        ) VALUES (%s, %s, %s, %s, %s);
    """

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor()
        cursor.execute(query, (model_name, mae, mse, rmse, r2_score))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_historical_energy_records(limit: int = 100, order_by: str = "timestamp DESC") -> List[Dict[str, Any]]:
    """
    Retrieve historical consumption records from the 'energy_consumption' table.
    """
    # Whitelist allowed order_by clauses to prevent SQL injection
    allowed_order = {
        "timestamp DESC": "timestamp DESC",
        "timestamp ASC": "timestamp ASC",
        "id DESC": "id DESC",
        "id ASC": "id ASC"
    }
    clean_order = allowed_order.get(order_by, "timestamp DESC")

    query = f"""
        SELECT id, timestamp, hour, day, day_of_week, month, weekend,
               lag_1h_kwh, lag_24h_kwh, rolling_mean_24h_kwh, energy_consumption_kwh
        FROM energy_consumption
        ORDER BY {clean_order}
        LIMIT %s;
    """

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def get_recent_predictions(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve recent model forecasts from the 'predictions' table.
    """
    query = """
        SELECT id, prediction_time, target_time, predicted_energy_kwh, model_name, created_at
        FROM predictions
        ORDER BY prediction_time DESC
        LIMIT %s;
    """

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def get_prediction_by_id(prediction_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific prediction record from 'predictions' table by its primary key.
    """
    query = """
        SELECT id, prediction_time, target_time, predicted_energy_kwh, model_name, created_at
        FROM predictions
        WHERE id = %s;
    """

    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (prediction_id,))
        row = cursor.fetchone()
        return row
    finally:
        conn.close()


def get_energy_summary() -> Dict[str, Any]:
    """
    Compute aggregate KPIs from MySQL:
    - average_consumption
    - peak_consumption
    - latest_consumption
    - total_records
    - latest_timestamp
    - average_potential_saving
    """
    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Consumption stats
        cursor.execute("""
            SELECT 
                ROUND(AVG(energy_consumption_kwh), 4) AS average_consumption,
                ROUND(MAX(energy_consumption_kwh), 4) AS peak_consumption,
                COUNT(*) AS total_records
            FROM energy_consumption;
        """)
        stats_row = cursor.fetchone() or {}

        # 2. Latest record
        cursor.execute("""
            SELECT 
                timestamp,
                ROUND(energy_consumption_kwh, 4) AS latest_consumption
            FROM energy_consumption
            ORDER BY timestamp DESC
            LIMIT 1;
        """)
        latest_row = cursor.fetchone() or {}

        # 3. Optimization stats
        cursor.execute("""
            SELECT 
                ROUND(AVG(potential_saving), 4) AS average_potential_saving,
                ROUND(AVG(saving_percentage), 2) AS average_saving_percentage,
                COUNT(*) AS total_optimizations
            FROM optimization_results;
        """)
        opt_row = cursor.fetchone() or {}

        return {
            "average_consumption": float(stats_row.get("average_consumption") or 0.0),
            "peak_consumption": float(stats_row.get("peak_consumption") or 0.0),
            "total_records": int(stats_row.get("total_records") or 0),
            "latest_consumption": float(latest_row.get("latest_consumption") or 0.0),
            "latest_timestamp": latest_row.get("timestamp"),
            "average_potential_saving": float(opt_row.get("average_potential_saving") or 0.0),
            "average_saving_percentage": float(opt_row.get("average_saving_percentage") or 0.0),
            "total_optimizations": int(opt_row.get("total_optimizations") or 0)
        }
    finally:
        conn.close()


def get_recent_optimization_results(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve recent energy optimization results from 'optimization_results'.
    """
    query = """
        SELECT id, prediction_id, baseline_consumption, predicted_consumption,
               potential_saving, saving_percentage, recommendation, created_at
        FROM optimization_results
        ORDER BY id DESC
        LIMIT %s;
    """
    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


