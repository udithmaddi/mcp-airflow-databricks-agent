from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

# ==============================================================================
# SAMPLE AIRFLOW DAG
# This file mimics a real Data Engineering pipeline.
# It lives in Airflow and runs every day.
# ==============================================================================

# 1. Default Settings
default_args = {
    'owner': 'data_eng',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 14),
    'email_on_failure': False, # In real life, set to True
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 2. Define the Pipeline (DAG)
dag = DAG(
    'gold_sales_daily',
    default_args=default_args,
    description='Daily Gold Layer Sales Processing',
    schedule_interval='0 2 * * *', # Runs at 2:00 AM daily
    catchup=False,
)

def simulate_databricks_submit():
    """
    Fake Task: Simulates sending a job to Databricks.
    It prints a 'Run ID' so our MCP Agent can find it in the logs.
    """
    # We fake a Run ID (100235) that our server knows.
    run_id = 100235 
    logging.info(f"Triggering Databricks Job for Sales processing...")
    
    # Crucial: We log the ID so the Agent can extract it with Regex!
    logging.info(f"Run ID: {run_id}")
    
    # Simulate Success (Normally this would wait for the job to finish)
    logging.info("Databricks Job Completed Successfully.")

# 3. Task Workflow
with dag:
    # Task A: Start
    start_task = PythonOperator(
        task_id='start_pipeline',
        python_callable=lambda: logging.info("Pipeline started.")
    )

    # Task B: Run the 'Gold' processing on Databricks
    process_gold = PythonOperator(
        task_id='process_silver', # Named 'silver' for testing purposes
        python_callable=simulate_databricks_submit
    )

    # Set dependency: Start -> Process
    start_task >> process_gold
