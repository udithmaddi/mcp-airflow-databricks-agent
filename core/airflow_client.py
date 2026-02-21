import requests
import os
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load secrets from .env file
load_dotenv()

# Setup helper logger
logger = logging.getLogger("AirflowClient")

class AirflowClient:
    """
    This class handles talking to the Apache Airflow Web API.
    It's like a remote control for Airflow.
    """
    def __init__(self):
        # 1. Load Settings
        self.base_url = os.getenv("AIRFLOW_URL", "http://localhost:8080").rstrip('/')
        self.username = os.getenv("AIRFLOW_USERNAME", "admin")
        self.password = os.getenv("AIRFLOW_PASSWORD", "admin")
        
        # 2. Setup Authentication (Basic Auth)
        self.auth = (self.username, self.password)
        self.headers = {"Content-Type": "application/json"}

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Helper: Makes a GET request to Airflow.
        """
        url = f"{self.base_url}/api/v1/{endpoint}"
        try:
            logger.debug(f"GET {url}")
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)
            response.raise_for_status() # Raise error if status is 4xx or 5xx
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Airflow API Error: {str(e)}")
            raise

    def get_dag_run(self, dag_id: str, dag_run_id: str) -> Dict[str, Any]:
        """
        Get info about a specific run of a pipeline.
        Example: status (success/failed), start_date, etc.
        """
        return self._get(f"dags/{dag_id}/dagRuns/{dag_run_id}")

    def get_failed_tasks(self, dag_id: str, dag_run_id: str) -> List[Dict[str, Any]]:
        """
        Finds all tasks that broke in a specific run.
        """
        # Get all task instances (TIs)
        data = self._get(f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances")
        tasks = data.get("task_instances", [])
        
        # Filter for only 'failed' ones
        failed = [t for t in tasks if t["state"] == "failed"]
        logger.info(f"Found {len(failed)} failed tasks for {dag_id} run {dag_run_id}")
        return failed

    def get_task_log(self, dag_id: str, dag_run_id: str, task_id: str, try_number: int) -> str:
        """
        Downloads the text logs for a task. 
        This is what the AI reads to find errors.
        """
        url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}"
        try:
            logger.debug(f"Fetching logs from {url}")
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=30)
            
            if response.status_code == 404:
                return "Log not found."
            
            response.raise_for_status()
            return response.text # Return the raw log text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch logs: {e}")
            return f"Error fetching logs: {str(e)}"

    def trigger_dag_run(self, dag_id: str, conf: Dict = None) -> Dict:
        """
        Remote Button Press: Starts a DAG run.
        Useful for restarting a pipeline after fixing it.
        """
        url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns"
        payload = {"conf": conf or {}}
        try:
            response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to trigger DAG {dag_id}: {e}")
            raise
