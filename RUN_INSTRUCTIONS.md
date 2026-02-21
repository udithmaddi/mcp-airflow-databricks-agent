# Quick Start Guide

## Step 1: Install Dependencies
(Only do this once)
Open PowerShell in this folder and run:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Step 2: Start the Server
To run the server, simply double-click the `start.bat` file in this folder.
*   **Success**: You will see a black window saying "Starting Airflow-Databricks MCP Assistant...".
*   **Note**: Keep this window open while you use the assistant.

## Step 3: Test Connection (Optional)
To verify everything is working without using Claude yet, run:
```powershell
.\.venv\Scripts\python.exe demo.py
```
If you see JSON output describing a "Scenario Result", it is working!

## Step 4: Use with Claude
1.  Open your Claude Desktop config file.
2.  Add the server configuration pointing to `C:\Users\UdithKumarMaddi\Desktop\MCP_Server\start.bat`.
3.  Restart Claude and look for the connection icon.
