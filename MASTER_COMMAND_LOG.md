# Project History: Step-by-Step Commands

This document records the exact sequence of actions taken to build this project from scratch.

## Step 1: Initialize Environment
We needed a Python 3.10+ environment because `mcp` SDK requires it.
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\activate
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Step 2: Server Verification (Sanity Check)
Before connecting AI, we verified the server code worked locally.
```powershell
.\.venv\Scripts\python.exe demo.py
# (Output: "Scenario 2: OOM Log Analysis...")
```

## Step 3: Configure Claude Desktop
We linked Claude to our local server.
*   **Attempt 1**: Used `start.bat`. *Failed (No icon).*
*   **Attempt 2**: Used `python.exe` directly in config. **Success.**

**Command used to generate clear config:**
```powershell
# (We ran this Python one-liner to write the JSON cleanly)
.\.venv\Scripts\python.exe -c "import json, os; ... open(path, 'w').write(...)"
```

## Step 4: Fix Airflow Permissions
Claude tried to read logs but got `403 Forbidden`.
**Reason**: Airflow was using Session Auth (browser cookies). We needed Basic Auth (API).
**Command run in WSL**:
```bash
sed -i "s/auth_backends = airflow.api.auth.backend.session/auth_backends = airflow.api.auth.backend.basic_auth/g" ~/airflow_home/airflow.cfg
```

## Step 5: Deploy Test Data
We created a failing DAG to test the RCA capability.
**Command to deploy:**
```powershell
copy "C:\Users\UdithKumarMaddi\Desktop\MCP_Server\gold_sales_daily.py" "\\wsl.localhost\Ubuntu-22.04\home\udith_2903\airflow_home\dags\gold_sales_daily.py"
```

## Step 6: Final Verification
1.  Restarted Airflow (`airflow standalone`).
2.  Triggered `gold_sales_daily` in UI.
3.  Asked Claude: "Analyze the failure".
**Result**: Success.
