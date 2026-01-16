import asyncio
import logging
import sys
import os
from typing import Any

# ==============================================================================
# MCP SERVER ENTRY POINT
# This file is the "Main Door" of the application.
# It connects the AI (Claude) to our Python tools.
# ==============================================================================

# 1. SETUP PATHS
# We need to make sure Python sees our local files (like tools.py).
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
import tools  # Import our actual code from tools.py

# 2. INITIALIZE SERVER
# Give the server a name so the AI knows who it is talking to.
app = Server("AirflowDatabricksAssistant")

# 3. SETUP LOGGING
# We log info so we can see what happens in the terminal.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# ==============================================================================
# TOOL DEFINITIONS
# Here we tell Claude: "These are the tools you can use."
# ==============================================================================
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """
    Returns a list of all tools available to the AI.
    Each tool has a Name, Description, and Input Schema (what arguments it needs).
    """
    return [
        # Tool 1: Get Basic Info about a DAG Run
        types.Tool(
            name="airflow_get_dag_run",
            description="Get metadata for a specific DAG run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id"],
            },
        ),
        # Tool 2: Find which tasks failed
        types.Tool(
            name="airflow_get_failed_tasks",
            description="Get list of failed tasks for a DAG run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id"],
            },
        ),
        # Tool 3: Get the logs (text) for a specific task
        types.Tool(
            name="airflow_get_task_log",
            description="Get raw logs for a task.",
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
        # Tool 4: Specifically extract Databricks ID from logs (Critical for RCA)
        types.Tool(
            name="airflow_extract_databricks_run_id",
            description="Extract Databricks Run ID from a task's logs.",
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
        # Tool 5: Get Databricks Error Details
         types.Tool(
            name="dbx_get_run_output",
            description="Get Databricks run output/error trace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                },
                "required": ["run_id"],
            },
        ),
        # Tool 6: Trigger a Databricks Job
        types.Tool(
            name="dbx_run_now",
            description="Trigger a Databricks Job.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "integer"},
                    "params": {"type": "object"},
                },
                "required": ["job_id"],
            },
        ),
        # Tool 7: The "Smart" Tool - Do Full RCA automatically
        types.Tool(
            name="generate_rca",
            description="Perform RCA on a pipeline failure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                },
                "required": ["dag_id", "run_id"],
            },
        ),
        # Tool 8: Fix it - Rerun the pipeline if safe
        types.Tool(
            name="rerun_failed_pipeline",
            description="Attempt to rerun a failed pipeline if safe.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "mode": {"type": "string", "default": "failed_only"},
                },
                "required": ["dag_id", "run_id"],
            },
        )
    ]

# ==============================================================================
# TOOL EXECUTION
# When the AI asks to run a tool, this function runs it.
# ==============================================================================
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests from the AI.
    It looks at the 'name' and calls the matching function in tools.py.
    """
    logger.info(f"Calling tool: {name} with args: {arguments}")
    
    try:
        # Route the request to the correct function in tools.py
        if name == "airflow_get_dag_run":
            result = tools.airflow_get_dag_run(arguments["dag_id"], arguments["run_id"])
        elif name == "airflow_get_failed_tasks":
            result = tools.airflow_get_failed_tasks(arguments["dag_id"], arguments["run_id"])
        elif name == "airflow_get_task_log":
            result = tools.airflow_get_task_log(arguments["dag_id"], arguments["run_id"], arguments["task_id"])
        elif name == "airflow_extract_databricks_run_id":
            # This is the new helper tool we added for production
            result = tools.airflow_extract_databricks_run_id(arguments["dag_id"], arguments["run_id"], arguments["task_id"])
        elif name == "dbx_get_run_output":
            result = tools.dbx_get_run_output(int(arguments["run_id"]))
        elif name == "dbx_run_now":
            result = tools.dbx_run_now(int(arguments["job_id"]), arguments.get("params"))
        elif name == "generate_rca":
            result = tools.generate_rca(arguments["dag_id"], arguments["run_id"])
        elif name == "rerun_failed_pipeline":
            result = tools.rerun_failed_pipeline(arguments["dag_id"], arguments["run_id"], arguments.get("mode", "failed_only"))
        else:
            raise ValueError(f"Unknown tool: {name}")

        # Return the result as text to the AI
        return [types.TextContent(type="text", text=str(result))]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

# ==============================================================================
# MAIN LOOP
# This keeps the server running and listening for commands.
# ==============================================================================
async def main():
    # Use Standard Input/Output (stdio) to communicate with Claude
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
