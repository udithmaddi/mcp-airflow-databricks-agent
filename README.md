# GenAI DataOps Agent using MCP Server (Airflow + Databricks)

## Overview
This project builds a **GenAI DataOps Assistant** using an **MCP Server (Model Context Protocol)** to connect AI agents (Claude Desktop / other MCP clients) with real Data Engineering platforms like:
- Apache Airflow
- Databricks Jobs

The goal is to enable:
- Pipeline Monitoring
- Failure Detection
- Root Cause Analysis (RCA)
- Safe Auto-remediation (rerun / clear task)

---

## Problem Statement
In real-world Data Engineering pipelines, failures happen frequently due to:
- missing / late upstream data
- schema drift
- data quality issues (nulls / duplicates)
- Databricks job failures
- broken dependencies

Manual RCA is slow (30–90 minutes) and requires switching between UIs and logs.

---

## Solution
This MCP Server exposes Airflow + Databricks operations as **tools** so that a GenAI agent can:
- identify failed tasks in Airflow
- fetch Airflow logs
- extract Databricks Run ID
- fetch Databricks output and error traces
- generate RCA summary
- apply safe remediation via policy guardrails

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
