import asyncio
import logging
import sys
import os
from typing import Any

# ==============================================================================
# 🎤 PRESENTATION NOTE: THE "FRONT DOOR"
# This file (`server.py`) is the main entry point.
# It connects the Artificial Intelligence (Claude) to our Code.
# It listens for commands like "Run SQL" or "Check Logs".
# ==============================================================================

# 1. SETUP: Make sure we can see our own tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
import tools  # This is where our actual features live

# 2. INITIALIZE: Give the Assistant a Name
app = Server("AirflowDatabricksAssistant")

# 3. LOGGING: So we can see what's happening in the black terminal window
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# ==============================================================================
# 🛠️ TOOL DEFINITIONS (The "Menu")
# Here we define the Menu of actions Claude is allowed to take.
# Each tool has a Name (what to call) and inputs (what it needs).
# ==============================================================================
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # --- AIRFLOW TOOLS (Orchestration) ---
        types.Tool(
            name="airflow_get_dag_run",
            description="🔍 Get details about a specific Pipeline run (Status, Start Time).",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id"],
            },
        ),
        types.Tool(
            name="airflow_get_failed_tasks",
            description="❌ Find out exactly WHICH tasks failed (so we don't check everything).",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id"],
            },
        ),
        types.Tool(
            name="airflow_get_task_log",
            description="📄 Read the text logs from Airflow to see error messages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "task_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id", "task_id"],
            },
        ),
        types.Tool(
            name="airflow_extract_databricks_run_id",
            description="🔢 Helper: Find the 'Databricks Job ID' hidden inside the text logs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "task_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id", "task_id"],
            },
        ),
        
        # --- DATABRICKS TOOLS (Compute) ---
        types.Tool(
            name="dbx_get_run_output",
            description="📉 Get specific error details from the Databricks cluster.",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                },
                "required": ["run_id"],
            },
        ),
        types.Tool(
            name="dbx_run_now",
            description="▶️ Trigger a Databricks Job manually.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "integer"},
                    "params": {"type": "object"},
                },
                "required": ["job_id"],
            },
        ),

        # --- INTELLIGENT AGENT TOOLS (The "Brain") ---
        types.Tool(
            name="generate_rca",
            description="🕵️‍♂️ THE DETECTIVE: Automatically analyze logs to find the Root Cause.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id"],
            },
        ),
        types.Tool(
            name="rerun_failed_pipeline",
            description="🚑 AUTO-HEAL: Attempt to fix and restart the pipeline (Checked by Policy).",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "mode": {"type": "string", "default": "failed_only"},
                },
                "required": ["dag_id", "run_id"],
            },
        ),
        
        # --- DATA ANALYSIS TOOLS (Business Intelligence) ---
        types.Tool(
            name="read_notebook_code",
            description="📖 READ LOGIC: Read Python/SQL code to understand Business Rules. PRIORITY: 1. `03_gold_analysis` (Look for `gold_sales_all`). 2. Use that logic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "notebook_name": {"type": "string", "description": "Name of the notebook (e.g., 03_gold_analysis)"},
                },
                "required": ["notebook_name"],
            },
        ),
        types.Tool(
            name="read_local_data_sample",
            description="👀 PEEK DATA: Read the first 50 rows of data to see column names.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filename to read (default: sales_data.csv)"},
                    "limit": {"type": "integer", "description": "Number of rows to read (default: 50)"}
                },
            },
        ),
        types.Tool(
            name="run_local_sql",
            description="⚡ RUN ANALYSIS: Run SQL on the data. LOGIC: 1. Use user filters if asked. 2. Else, use Silver filters (COMPLETED/PENDING).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL Query to execute (SQLite syntax)."},
                },
                "required": ["query"],
            },
        )
    ]

# ==============================================================================
# 🚀 EXECUTION ENGINE
# When Claude picks a tool from the menu, we run the code here.
# ==============================================================================
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    logger.info(f"Command Received: {name} | Args: {arguments}")
    
    try:
        # Route the command to the right Python function
        if name == "airflow_get_dag_run":
            result = tools.airflow_get_dag_run(arguments["dag_id"], arguments["run_id"])
        elif name == "airflow_get_failed_tasks":
            result = tools.airflow_get_failed_tasks(arguments["dag_id"], arguments["run_id"])
        elif name == "airflow_get_task_log":
            result = tools.airflow_get_task_log(arguments["dag_id"], arguments["run_id"], arguments["task_id"])
        elif name == "airflow_extract_databricks_run_id":
            result = tools.airflow_extract_databricks_run_id(arguments["dag_id"], arguments["run_id"], arguments["task_id"])
        elif name == "dbx_get_run_output":
            result = tools.dbx_get_run_output(int(arguments["run_id"]))
        elif name == "dbx_run_now":
            result = tools.dbx_run_now(int(arguments["job_id"]), arguments.get("params"))
        elif name == "generate_rca":
            result = tools.generate_rca(arguments["dag_id"], arguments["run_id"])
        elif name == "rerun_failed_pipeline":
            result = tools.rerun_failed_pipeline(arguments["dag_id"], arguments["run_id"], arguments.get("mode", "failed_only"))
        elif name == "read_notebook_code":
            result = tools.read_notebook_code(arguments["notebook_name"])
        elif name == "read_local_data_sample":
            result = tools.read_local_data_sample(arguments.get("filename", "sales_data.csv"), arguments.get("limit", 50))
        elif name == "run_local_sql":
             result = tools.run_local_sql(arguments["query"])
        else:
            raise ValueError(f"Unknown tool: {name}")

        # Send the result back to Claude
        return [types.TextContent(type="text", text=str(result))]
    
    except Exception as e:
        logger.error(f"Error running {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

# ==============================================================================
# 🔄 MAIN LISTENER
# Keep the server open and waiting for requests.
# ==============================================================================
async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
