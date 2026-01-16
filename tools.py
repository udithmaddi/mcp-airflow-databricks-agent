import logging
import re
import json
from typing import Dict, Any, List, Optional

from airflow_client import AirflowClient
from databricks_client import DatabricksClient
from rca_engine import RCAEngine
from policy import PolicyGuardrails

# ==============================================================================
# TOOLS ORCHESTRATION
# This file contains the logic for each tool.
# It connects the parts together: Airflow -> Extract ID -> Databricks -> RCA.
# ==============================================================================

# Initialize our helper classes
logger = logging.getLogger("MCPTools")
airflow = AirflowClient()
databricks = DatabricksClient()
rca = RCAEngine()
policy = PolicyGuardrails()

def _extract_run_id(log_text: str) -> Optional[int]:
    """
    HELPER FUNCTION:
    This looks at a text log and finds the Databricks 'Run ID'.
    It uses 'Regex' (pattern matching) to find numbers like: "Run ID: 12345".
    """
    patterns = [
        r"run_id[=: ]+(\d+)",                         # matches "run_id=123"
        r"Run ID[=: ]+(\d+)",                         # matches "Run ID: 123"
        r"Submitted run[^\d]*(\d+)",                  # matches "Submitted run 123"
        r"databricks run now response.*run_id[\"':\s]+(\d+)" # matches JSON response
    ]
    for p in patterns:
        match = re.search(p, log_text, re.IGNORECASE)
        if match:
            return int(match.group(1)) # We found it! Return the number.
    return None # We didn't find any ID.

# ------------------------------------------------------------------------------
# AIRFLOW TOOLS
# ------------------------------------------------------------------------------

def airflow_get_dag_run(dag_id: str, run_id: str) -> str:
    """Tool: Get details about a specific Pipeline run."""
    try:
        # Ask Airflow Client for data, convert to JSON string
        return json.dumps(airflow.get_dag_run(dag_id, run_id))
    except Exception as e:
        return json.dumps({"error": str(e)})

def airflow_get_failed_tasks(dag_id: str, run_id: str) -> str:
    """Tool: Find out WHICH tasks failed."""
    try:
        return json.dumps(airflow.get_failed_tasks(dag_id, run_id))
    except Exception as e:
        return json.dumps([{"error": str(e)}])

def airflow_get_task_log(dag_id: str, run_id: str, task_id: str) -> str:
    """
    Tool: Get the log file for a task.
    We return a 'Cleaned' version that includes metadata.
    """
    try:
        # 1. Fetch text from Airflow
        log_text = airflow.get_task_log(dag_id, run_id, task_id, 1)
        
        # 2. Check for basic errors
        if log_text.startswith("Error") or "Log not found" in log_text:
             return json.dumps({"error": log_text})

        # 3. Try to be smart and find the Databricks ID immediately
        dbx_run_id = _extract_run_id(log_text)
        
        # 4. Build a nice JSON response
        response = {
            "dag_id": dag_id,
            "task_id": task_id,
            "run_id": run_id,
            "databricks_run_id": dbx_run_id,
            # Return only the last 2000 chars so we don't overwhelm the AI
            "log_content": log_text[-2000:] if len(log_text) > 2000 else log_text
        }
        return json.dumps(response, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def airflow_extract_databricks_run_id(dag_id: str, run_id: str, task_id: str) -> Optional[int]:
    """
    Tool: Just find the Databricks ID.
    Useful if the AI wants to double-check a specific task.
    """
    try:
        log_text = airflow.get_task_log(dag_id, run_id, task_id, 1)
        return _extract_run_id(log_text)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None

# ------------------------------------------------------------------------------
# DATABRICKS TOOLS
# ------------------------------------------------------------------------------

def dbx_get_run_output(run_id: int) -> str:
    """Tool: Get the error message from Databricks."""
    try:
        return json.dumps(databricks.get_run_output(run_id))
    except Exception as e:
        return json.dumps({"error": str(e)})

def dbx_run_now(job_id: int, params: Dict = None) -> str:
    """Tool: Trigger a Job (Run a notebook)."""
    # SAFETY CHECK: Is this safe?
    if not policy.check_safety("dbx_run_now", params):
         return json.dumps({"error": "Action blocked by safety policy."})
    try:
        return json.dumps(databricks.run_now(job_id, params))
    except Exception as e:
        return json.dumps({"error": str(e)})

# ------------------------------------------------------------------------------
# INTELLIGENT WORKFLOWS (The "Agent" Logic)
# ------------------------------------------------------------------------------

def generate_rca(dag_id: str, run_id: str) -> str:
    """
    Tool: The "Magic Button".
    It:
    1. Finds failed tasks
    2. Reads their logs
    3. Finds the Databricks ID
    4. Fetches Databricks Error
    5. Analyzes everything to find the Root Cause
    """
    # 1. Get failed tasks
    failed_tasks_list = airflow_get_failed_tasks(dag_id, run_id)
    failed_tasks = json.loads(failed_tasks_list)

    if not failed_tasks or (isinstance(failed_tasks, list) and len(failed_tasks) > 0 and "error" in failed_tasks[0]):
        return json.dumps({"status": "No failed tasks found."})

    report = {"dag_id": dag_id, "run_id": run_id, "tasks": []}

    for task in failed_tasks:
        t_id = task["task_id"]
        try_num = task["try_number"]
        
        # 2. Get Airflow Log
        af_log = airflow.get_task_log(dag_id, run_id, t_id, try_num)
        
        task_analysis = {
            "task_id": t_id,
            "root_cause_analysis": None
        }

        # 3. Find Databricks ID
        db_run_id = _extract_run_id(af_log)
        
        log_context = af_log
        if db_run_id:
            task_analysis["databricks_run_id"] = db_run_id
            
            # 4. Get Databricks Output
            db_out = dbx_get_run_output(db_run_id)
            db_out_dict = json.loads(db_out)

            error_trace = db_out_dict.get("error_trace", "") or db_out_dict.get("error", "")
            log_context += f"\n--- Databricks Error ---\n{error_trace}"
        
        # 5. Analyze (RCA)
        rca_result = rca.analyze(log_context)
        task_analysis["root_cause_analysis"] = rca_result
        report["tasks"].append(task_analysis)

    return json.dumps(report, indent=2)

def rerun_failed_pipeline(dag_id: str, run_id: str, mode: str = "failed_only") -> str:
    """
    Tool: Auto-Heal.
    Attempts to rerun. But strictly CHECKS POLICY first.
    """
    # 1. Analyze failure first
    rca_report_str = generate_rca(dag_id, run_id)
    rca_report = json.loads(rca_report_str)
    
    # 2. Check if it's safe to rerun (Policy)
    tasks = rca_report.get("tasks", [])
    if not tasks:
        return json.dumps({"status": "Nothing to rerun."})

    for task in tasks:
        rca_res = task["root_cause_analysis"]
        root_cause = rca_res.get("root_cause", "Unknown")
        
        # Check Policy Class
        current_try = 1 # In real app, get this from Airflow
        validation = policy.validate_rerun(dag_id, current_try, root_cause)
        
        if not validation["allowed"]:
            # BLOCKED!
            return json.dumps({
                "status": "Rerun Blocked",
                "reason": validation["reason"],
                "task_id": task["task_id"]
            })

    # 3. If safe, Trigger Rerun
    logger.info(f"Rerun allowed for {dag_id}. Triggering...")
    try:
        res = airflow.trigger_dag_run(dag_id, conf={"rerun_initiator": "mcp_agent", "original_run": run_id})
        return json.dumps({"status": "Rerun Triggered", "new_run_details": res})
    except Exception as e:
        return json.dumps({"error": f"Failed to trigger rerun: {e}"})
