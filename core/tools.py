import logging
import re
import json
import os
from typing import Dict, Any, List, Optional

# Import the helpers (The "Phones" to talk to other systems)
from airflow_client import AirflowClient
from databricks_client import DatabricksClient
from rca_engine import RCAEngine
from policy import PolicyGuardrails

# ==============================================================================
# 🧰 TOOLS LIBRARY
# This file (`tools.py`) is the "Utility Belt".
# It contains the actual Python code for every action the Agent can take.
# ==============================================================================

# Initialize our helpers
logger = logging.getLogger("MCPTools")
airflow = AirflowClient()       # To talk to Airflow
databricks = DatabricksClient() # To talk to Databricks
rca = RCAEngine()               # To analyze errors
policy = PolicyGuardrails()     # To keep us safe

# ------------------------------------------------------------------------------
# 🕵️‍♂️ HELPER: The "ID Finder"
# ------------------------------------------------------------------------------
def _extract_run_id(log_text: str) -> Optional[int]:
    """
    Looks at a messy text log and finds the 'Databricks Run ID'.
    Example: Finds '12345' in 'Run ID: 12345'.
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
            return int(match.group(1)) # Found it!
    return None # Not found

# ------------------------------------------------------------------------------
# ☁️ AIRFLOW TOOLS (Orchestration)
# ------------------------------------------------------------------------------

def airflow_get_dag_run(dag_id: str, run_id: str) -> str:
    """Ask Airflow: 'How is this pipeline run doing?'"""
    try:
        return json.dumps(airflow.get_dag_run(dag_id, run_id))
    except Exception as e:
        return json.dumps({"error": str(e)})

def airflow_get_failed_tasks(dag_id: str, run_id: str) -> str:
    """Ask Airflow: 'Which specific tasks failed?'"""
    try:
        return json.dumps(airflow.get_failed_tasks(dag_id, run_id))
    except Exception as e:
        return json.dumps([{"error": str(e)}])

def airflow_get_task_log(dag_id: str, run_id: str, task_id: str) -> str:
    """
    Ask Airflow: 'Give me the log file for this task.'
    We also try to find the Databricks ID inside it to help the Agent.
    """
    try:
        # 1. Fetch text logs
        log_text = airflow.get_task_log(dag_id, run_id, task_id, 1)
        
        # 2. Check for basic errors
        if log_text.startswith("Error") or "Log not found" in log_text:
             return json.dumps({"error": log_text})

        # 3. Look for the hidden Databricks ID
        dbx_run_id = _extract_run_id(log_text)
        
        # 4. Prepare a clean summary
        response = {
            "dag_id": dag_id,
            "task_id": task_id,
            "run_id": run_id,
            "databricks_run_id": dbx_run_id,
            "log_content": log_text[-2000:] if len(log_text) > 2000 else log_text # Last 2000 chars only
        }
        return json.dumps(response, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def airflow_extract_databricks_run_id(dag_id: str, run_id: str, task_id: str) -> Optional[int]:
    """Helper: Just find the ID."""
    try:
        log_text = airflow.get_task_log(dag_id, run_id, task_id, 1)
        return _extract_run_id(log_text)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None

# ------------------------------------------------------------------------------
# 🧱 DATABRICKS TOOLS (Compute)
# ------------------------------------------------------------------------------

def dbx_get_run_output(run_id: int) -> str:
    """Ask Databricks: 'What exactly went wrong on the cluster?'"""
    try:
        return json.dumps(databricks.get_run_output(run_id))
    except Exception as e:
        return json.dumps({"error": str(e)})

def dbx_run_now(job_id: int, params: Dict = None) -> str:
    """Ask Databricks: 'Please run this Job now.'"""
    # SAFETY FIRST: Check if we are allowed to do this
    if not policy.check_safety("dbx_run_now", params):
         return json.dumps({"error": "Action blocked by Safety Policy."})
    try:
        return json.dumps(databricks.run_now(job_id, params))
    except Exception as e:
        return json.dumps({"error": str(e)})

# ------------------------------------------------------------------------------
# 🧠 INTELLIGENT WORKFLOWS
# ------------------------------------------------------------------------------

def read_notebook_code(notebook_name: str) -> str:
    """
    Ask File System: 'Show me the code in this notebook.'
    The Agent reads this to understand HOW business logic is calculated.
    """
    try:
        # Security: Only allow reading .py files in 'notebooks' folder
        safe_name = os.path.basename(notebook_name)
        if not safe_name.endswith(".py"):
             safe_name += ".py"
        
        notebook_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notebooks")
        file_path = os.path.join(notebook_dir, safe_name)
        
        if not os.path.exists(file_path):
            files = [f for f in os.listdir(notebook_dir) if f.endswith(".py")]
            return json.dumps({
                "error": f"Notebook '{safe_name}' not found.",
                "available_notebooks": files,
                "hint": "Please pick one from the available list."
            })
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return json.dumps({"notebook_name": safe_name, "content": content})
    except Exception as e:
        return json.dumps({"error": str(e)})

def read_local_data_sample(filename: str = "sales_data.csv", limit: int = 50) -> str:
    """
    Ask File System: 'Show me a preview of the raw data.'
    """
    try:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), safe_name)
        
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File '{safe_name}' not found."})
            
        lines = []
        with open(file_path, "r", encoding="utf-8") as f:
            header = f.readline().strip()
            lines.append(header)
            for _ in range(limit):
                line = f.readline()
                if not line: break
                lines.append(line.strip())
                
        return json.dumps({
            "filename": safe_name, 
            "preview": "\n".join(lines),
            "note": "This is just a SAMPLE preview."
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def generate_rca(dag_id: str, run_id: str) -> str:
    """
    🕵️‍♂️ THE DETECTIVE WORKFLOW
    This function does the heavy lifting:
    1. Finds failed tasks in Airflow.
    2. gets their logs.
    3. Finds the Databricks Run ID.
    4. Gets the Databricks Error.
    5. Sends all this to the 'RCA Engine' to understand WHY it failed.
    """
    # 1. Who failed?
    failed_tasks_list = airflow_get_failed_tasks(dag_id, run_id)
    failed_tasks = json.loads(failed_tasks_list)

    if not failed_tasks or (isinstance(failed_tasks, list) and len(failed_tasks) > 0 and "error" in failed_tasks[0]):
        return json.dumps({"status": "No failed tasks found."})

    report = {"dag_id": dag_id, "run_id": run_id, "tasks": []}

    for task in failed_tasks:
        t_id = task["task_id"]
        try_num = task["try_number"]
        
        # 2. Get the Logs
        af_log = airflow.get_task_log(dag_id, run_id, t_id, try_num)
        
        task_analysis = {"task_id": t_id, "root_cause_analysis": None}

        # 3. Find the Databricks ID
        db_run_id = _extract_run_id(af_log)
        
        log_context = af_log
        if db_run_id:
            task_analysis["databricks_run_id"] = db_run_id
            # 4. Get Databricks Details
            db_out = dbx_get_run_output(db_run_id)
            db_out_dict = json.loads(db_out)
            error_trace = db_out_dict.get("error_trace", "") or db_out_dict.get("error", "")
            log_context += f"\n--- Databricks Error ---\n{error_trace}"
        
        # 5. Analyze it!
        rca_result = rca.analyze(log_context)
        task_analysis["root_cause_analysis"] = rca_result
        report["tasks"].append(task_analysis)

    return json.dumps(report, indent=2)

def rerun_failed_pipeline(dag_id: str, run_id: str, mode: str = "failed_only") -> str:
    """
    🚑 AUTO-HEAL WORKFLOW
    1. Analyze why it failed.
    2. Check Policy (Is it safe to rerun?).
    3. If safe, restart the pipeline.
    """
    rca_report = json.loads(generate_rca(dag_id, run_id))
    tasks = rca_report.get("tasks", [])
    
    if not tasks:
        return json.dumps({"status": "Nothing to rerun."})

    for task in tasks:
        # Check Safety Policy
        rca_res = task["root_cause_analysis"]
        root_cause = rca_res.get("root_cause", "Unknown")
        validation = policy.validate_rerun(dag_id, 1, root_cause)
        
        if not validation["allowed"]:
            return json.dumps({"status": "Rerun Blocked", "reason": validation["reason"]})

    # Trigger Rerun
    try:
        res = airflow.trigger_dag_run(dag_id, conf={"rerun_initiator": "mcp_agent", "original_run": run_id})
        return json.dumps({"status": "Rerun Triggered", "details": res})
    except Exception as e:
        return json.dumps({"error": f"Failed: {e}"})

import sqlite3

def run_local_sql(query: str) -> str:
    """
    ⚡ LOCAL ANALYTICS ENGINE
    1. Creates a temporary database in memory.
    2. Loads 'sales_data.csv' into it.
    3. Runs your SQL query.
    4. Gives you the answer.
    """
    try:
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Define the Schema
        cursor.execute('''
            CREATE TABLE sales (
                order_id TEXT, date TEXT, customer_id INTEGER, 
                category TEXT, product TEXT, amount REAL, status TEXT
            )
        ''')
        
        # Load Data
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales_data.csv")
        if not os.path.exists(csv_path): return json.dumps({"error": "Data file not found."})
             
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Skip header
            cursor.executemany('INSERT INTO sales VALUES (?,?,?,?,?,?,?)', reader)
        conn.commit()
        
        # Run Query
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        results = [dict(zip(columns, row)) for row in rows]
            
        if len(results) > 50:
             return json.dumps({"warning": "Result truncated to 50 rows.", "data": results[:50]})
             
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if 'conn' in locals(): conn.close()
