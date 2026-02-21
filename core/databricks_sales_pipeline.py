from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import time

# ==============================================================================
# DATABRICKS SALES PIPELINE
# Orchestrates: Bronze -> Silver -> Gold
# ==============================================================================

default_args = {
    'owner': 'data_eng',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 14),
    'email_on_failure': False, 
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

# RENAMED DAG ID to match filename
dag = DAG(
    'databricks_sales_pipeline',
    default_args=default_args,
    description='End-to-End Databricks Pipeline (Bronze->Silver->Gold)',
    schedule_interval='0 2 * * *', # Daily at 2 AM
    catchup=False,
)

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------

def trigger_databricks_job(layer_name, job_id, run_id_to_log):
    """
    Simulates triggering a Databricks Notebook Job.
    """
    logging.info(f"--- Starting Layer: {layer_name.upper()} ---")
    logging.info(f"Triggering Databricks Job ID: {job_id}")
    
    # Log the Run ID so our MCP Agent can find it
    logging.info(f"Run ID: {run_id_to_log}")
    
    # Simulate processing time
    time.sleep(1) 
    
    # Simulate Success
    logging.info(f"{layer_name.capitalize()} Layer Completed Successfully.")
    return "Success"

# ------------------------------------------------------------------------------
# TASKS
# ------------------------------------------------------------------------------

with dag:
    # Task 1: Bronze Ingestion
    bronze_task = PythonOperator(
        task_id='ingest_bronze',
        python_callable=trigger_databricks_job,
        op_kwargs={'layer_name': 'bronze', 'job_id': 1001, 'run_id_to_log': 200101}
    )

    # Task 2: Silver Transformation
    silver_task = PythonOperator(
        task_id='process_silver',
        python_callable=trigger_databricks_job,
        op_kwargs={'layer_name': 'silver', 'job_id': 1002, 'run_id_to_log': 200102}
    )

    # Task 3: Gold Analysis
    gold_task = PythonOperator(
        task_id='analyze_gold',
        python_callable=trigger_databricks_job,
        op_kwargs={'layer_name': 'gold', 'job_id': 1003, 'run_id_to_log': 200103}
    )

    # Define Dependencies
    bronze_task >> silver_task >> gold_task
