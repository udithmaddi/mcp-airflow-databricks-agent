from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import time

# ==============================================================================
# FAILED DATABRICKS PIPELINE
# Simulates a pipeline failure for RCA testing
# ==============================================================================

default_args = {
    'owner': 'data_eng',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 14),
    'email_on_failure': False, 
    'retries': 0, # No retries for failure simulation
    'retry_delay': timedelta(minutes=2),
}

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

def trigger_fail_job(layer_name, job_id, run_id_to_log):
    """
    Simulates a FAILED Databricks Notebook Job.
    """
    logging.info(f"--- Starting Layer: {layer_name.upper()} ---")
    logging.info(f"Triggering Databricks Job ID: {job_id}")
    logging.info(f"Run ID: {run_id_to_log}")
    time.sleep(1)
    raise Exception(f"Job {job_id} failed in {layer_name} layer!")

# ------------------------------------------------------------------------------
# DAG DEFINITION
# ------------------------------------------------------------------------------

dag_fail = DAG(
    'databricks_sales_pipeline_failure',
    default_args=default_args,
    description='Simulates a Failed Pipeline',
    schedule_interval='0 3 * * *', # run at 3 AM
    catchup=False,
)

with dag_fail:
    # Task 1: Bronze Ingestion (Success)
    bronze_fail_task = PythonOperator(
        task_id='ingest_bronze_fail',
        python_callable=trigger_databricks_job,
        op_kwargs={'layer_name': 'bronze', 'job_id': 1004, 'run_id_to_log': 200104}
    )

    # Task 2: Silver Transformation (Fail)
    silver_fail_task = PythonOperator(
        task_id='process_silver_fail',
        python_callable=trigger_fail_job,
        op_kwargs={'layer_name': 'silver', 'job_id': 1005, 'run_id_to_log': 200105}
    )

    # Task 3: Gold Analysis (Skipped due to upstream failure)
    gold_fail_task = PythonOperator(
        task_id='analyze_gold_fail',
        python_callable=trigger_databricks_job,
        op_kwargs={'layer_name': 'gold', 'job_id': 1006, 'run_id_to_log': 200106}
    )

    bronze_fail_task >> silver_fail_task >> gold_fail_task
