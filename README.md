
# mcp-airflow-databricks-agent
=======
# How to Run the Airflow-Databricks MCP Server

## 1. Setup (Done)
- **Virtual Environment**: A Python 3.13 virtual environment has been created in `.venv`.
- **Dependencies**: Installed into `.venv` using `requirements.txt`.
- **Config**: `.env` file is ready with your credentials.

## 2. Run the Server
We have created a helper script to ensure you use the correct Python environment.

### Option A: Using the Helper Script (Recommended)
Simply double-click or run:
```powershell
.\start.bat
```

### Option B: Manual Execution
If you prefer running manual commands, ensure you use the python from the `.venv`:
```powershell
.\.venv\Scripts\python.exe server.py
```

## 3. Testing
To verify logic locally:
```powershell
.\.venv\Scripts\python.exe demo.py
```

## 4. Connecting to Claude Desktop
Update your configuration to point to the virtual environment's python executable:
```json
{
  "mcpServers": {
    "dataops-assistant": {
      "command": "C:\\Users\\UdithKumarMaddi\\Desktop\\MCP_Server\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\UdithKumarMaddi\\Desktop\\MCP_Server\\server.py"]
    }
  }
}
```
