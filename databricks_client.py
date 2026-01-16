import requests
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("DatabricksClient")

class DatabricksClient:
    """
    This class handles talking to the Databricks API.
    It allows us to check if a Job failed and why.
    """
    def __init__(self):
        # 1. Load Credentials (Host URL and Secret Token)
        self.host = os.getenv("DATABRICKS_HOST", "").rstrip('/')
        self.token = os.getenv("DATABRICKS_TOKEN", "")
        
        # Check if they exist (WARN if missing)
        if not self.host or not self.token:
            logger.warning("Databricks credentials missing in environment.")
        
        # 2. Setup Headers (Authentication)
        # Bearer Token is standard for Databricks
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _post(self, endpoint: str, json_data: Dict) -> Dict:
        """
        Helper: Sends data (POST) to Databricks.
        """
        url = f"{self.host}/api/2.1/{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=json_data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Databricks API Error: {e}")
            raise

    def get_run_output(self, run_id: int) -> Dict[str, Any]:
        """
        Fetch the 'Output' of a specific run.
        This usually contains the Error Message or Stack Trace.
        """
        url = f"{self.host}/api/2.1/jobs/runs/get-output"
        try:
            response = requests.get(url, headers=self.headers, params={"run_id": run_id}, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get run output for {run_id}: {e}")
            return {"error": str(e)}

    def run_now(self, job_id: int, params: Dict = None) -> Dict[str, Any]:
        """
        Start a Job immediately.
        Used when the AI decides to "Retry" the pipeline.
        """
        payload = {"job_id": job_id}
        if params:
            payload["notebook_params"] = params
        
        return self._post("jobs/run-now", payload)
    
    def get_run(self, run_id: int) -> Dict[str, Any]:
        """
        Get general info about a run (Status, Start Time, etc).
        """
        url = f"{self.host}/api/2.1/jobs/runs/get"
        try:
            response = requests.get(url, headers=self.headers, params={"run_id": run_id})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get run info {run_id}: {e}")
            raise
