# GenAI DataOps Agent using MCP Server (Airflow + Databricks)
## Overview
This project builds a **GenAI DataOps Assistant** using an **MCP Server (Model Context Protocol)** to connect AI agents (Claude Desktop / other MCP clients) with real Data Engineering platforms like:
- **Apache Airflow**
- **Databricks Jobs**
  
The goal is to enable:
- Pipeline Monitoring
- Failure Detection
- Root Cause Analysis (RCA)
- Safe Auto-remediation (rerun / clear task)
---
## Problem Statement
In real-world Data Engineering pipelines, failures happen frequently due to:
- Missing / late upstream data
- Schema drift
- Data quality issues (nulls / duplicates)
- Databricks job failures
- Broken dependencies
Manual RCA is slow (30–90 minutes) and requires switching between UIs and logs.
---
## Solution
This MCP Server exposes Airflow + Databricks operations as **tools** so that a GenAI agent can:
- Identify failed tasks in Airflow
- Fetch Airflow logs
- Extract Databricks Run ID
- Fetch Databricks output and error traces
- Generate RCA summary
- Apply safe remediation via policy guardrails
---
## Architecture
```text
[User / Data Engineer]
        |
        v
[GenAI Agent / Claude Desktop]
        |
        v
     (MCP Client)
        |
        v
+-----------------------------------+
|        MCP Server (DataOps)       |
|  - Airflow Tools                  |
|  - Databricks Tools               |
|  - RCA Engine                     |
|  - Safe Remediation Policy        |
+-----------------------------------+
        |                     |
        v                     v
 [Apache Airflow]         [Databricks]
```
## Key Features
- Airflow DAG run monitoring
- Failed task detection
- Airflow task log extraction
- Databricks Run ID parsing from logs
- Databricks run output and error trace retrieval
- RCA summary generation
- Safe remediation actions (clear task / rerun) with guardrails
---
## Tech Stack
- **Python**
- **Apache Airflow** (REST API)
- **Databricks Jobs API**
- **MCP Server** (Model Context Protocol)
- **Claude Desktop / MCP Client**
---
## Project Structure
```text
MCP_Server/
│
├── Databricks Notebooks/
│   ├── 01_bronze_ingest.py
│   ├── 02_silver_transform.py
│   ├── 03_gold_analysis.py
│
├── MCP_Screenshot/
│   ├── Screenshot 2026-01-15 143536...
│   ├── Screenshot 2026-01-23 130625...
│   ├── Screenshot 2026-01-23 130713...
│   ├── Screenshot 2026-01-23 130802...
│   ├── Screenshot 2026-01-23 130923...
│   ├── Screenshot 2026-01-23 131001...
│   ├── Screenshot 2026-01-23 153338...
│   ├── Screenshot_01.png
│   ├── Screenshot_02.png
│   ├── Screenshot_03(1).png
│   ├── Screenshot_03(2).png
│   ├── Screenshot_03.png
│   ├── Screenshot_04(1).png
│   ├── Screenshot_04(2).png
│   ├── Screenshot_04.png
│   ├── Screenshot_05.png
│   ├── Screenshot_06.png
│   ├── Screenshot_07.png
│
├── core/
│   ├── README.md
│   ├── airflow_client.py
│   ├── databricks_client.py
│   ├── databricks_sales_pipeline.py
│   ├── databricks_sales_pipeline_failure.py
│   ├── demo.py
│   ├── generate_data.py
│   ├── policy.py
│   ├── rca_engine.py
│   ├── requirements.txt
│   ├── sales_data.csv
│   ├── server.py
│   ├── start.bat
│   ├── tools.py
│
├── .env.template
├── .gitignore
├── MASTER_COMMAND_LOG.md
├── README.md
└── RUN_INSTRUCTIONS.md
```
---
## Installation and Run
### 1) Clone Repository
```bash
git clone <your-repo-url>
cd MCP_Server
```
### 2) Create Virtual Environment
**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```
**Linux/Mac**
```bash
python -m venv .venv
source .venv/bin/activate
```
### 3) Install Dependencies
```bash
pip install -r requirements.txt
```
### 4) Setup Environment Variables
Create `.env` from template:
**Windows**
```bash
copy .env.template .env
```
**Linux/Mac**
```bash
cp .env.template .env
```
Fill Airflow and Databricks credentials inside `.env`.
### 5) Run MCP Server
```bash
python server.py
```
Or Windows shortcut:
```bash
start.bat
```
---
## How to Use
### Option 1: Claude Desktop + MCP Client
Start server locally:
```bash
python server.py
```
Configure Claude Desktop to connect to this MCP server.
Use prompts like:
**Monitoring**
```text
Check DAG status for <dag_id>.
```
**Failure detection**
```text
List failed tasks in DAG <dag_id> and fetch logs.
```
**RCA**
```text
Generate RCA summary for this DAG failure including Databricks trace.
```
**Remediation**
```text
Rerun only failed tasks safely (apply policy guardrails).
```
### Option 2: Run Demo Script
```bash
python demo.py
```
---
## Authentication and Credentials
This project requires authentication for both Airflow and Databricks.
Required `.env` variables:
```env
AIRFLOW_BASE_URL=http://localhost:8080
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin
DATABRICKS_HOST=https://dbc-xxxxxxxxxxxx.cloud.databricks.com
DATABRICKS_TOKEN=dapiXXXXXXXXXXXXXXXX
```
---
## Demo Workflow
Typical automation flow:
1. Agent checks Airflow DAG run state
2. If failed, fetch failed tasks
3. Fetch task logs
4. Extract Databricks run ID
5. Fetch Databricks run output/error trace
6. Generate RCA summary
7. Safe remediation (rerun/clear) if allowed by policy
---
## Sample RCA Output
## Root Cause: Databricks job failed due to schema drift
### Details:
• Column `amount` expected DOUBLE but received STRING
• Source: s3://raw-data/transactions/
• Timestamp: 2026-01-16 14:30:15
### Impact:
• Gold table refresh failed
• Dashboards showing stale data
### Suggested Fix:
• Add schema validation step
• Apply safe casting: CAST(amount AS DOUBLE)
• Rerun failed tasks only
