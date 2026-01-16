# GenAI DataOps Agent using MCP Server (Airflow + Databricks)

A **GenAI-powered DataOps Assistant** that uses an **MCP Server (Model Context Protocol)** to connect AI agents (Claude Desktop / MCP clients) with real Data Engineering platforms like **Apache Airflow** and **Databricks** for monitoring, RCA, and safe remediation.

---

## Project Description
In production Data Engineering environments, pipeline failures happen frequently due to:
- missing / late upstream data
- schema drift
- data quality issues (nulls / duplicates)
- Databricks transformation failures
- broken dependencies

Manual Root Cause Analysis (RCA) often takes **30–90 minutes** because engineers must switch between:
- Airflow UI
- task logs
- Databricks UI / run output
- SQL and validation queries

This project solves the problem by building an MCP Server that exposes DataOps actions as **tools**, allowing an AI agent to:
- detect failures
- fetch logs automatically
- extract Databricks run details
- generate RCA summary
- safely rerun pipelines with guardrails

### Why these technologies?
- **Airflow** → industry standard workflow scheduler
- **Databricks** → widely used transformation platform for DE
- **MCP Server** → bridges GenAI + real tools using structured tool calling
- **Claude Desktop / MCP Client** → interactive conversational DataOps experience

### Challenges handled
- extracting Databricks run id from Airflow logs
- handling multiple failure patterns (Airflow vs Databricks errors)
- implementing safe remediation guardrails

### Future enhancements
- Slack / MS Teams alerts
- auto ticket creation (Jira / ServiceNow)
- automated data quality checks (schema drift, nulls, duplicates)
- multi-DAG monitoring dashboard
- approval workflow for remediation actions

---

## Table of Contents
1. [Problem Statement](#-problem-statement)
2. [Solution](#-solution)
3. [Architecture](#-architecture)
4. [Key Features](#-key-features)
5. [Tech Stack](#-tech-stack)
6. [Project Structure](#-project-structure)
7. [Installation & Run](#-installation--run)
8. [How to Use](#-how-to-use)
9. [Authentication / Credentials](#-authentication--credentials)
10. [Demo Workflow](#-demo-workflow)
11. [Screenshots](#-screenshots)
12. [Security Notes](#-security-notes)
13. [Contributing](#-contributing)
14. [License](#-license)

---

## Problem Statement
Failures in Data Engineering pipelines frequently happen due to:
- upstream data delays or missing partitions
- schema drift and breaking transformations
- bad data quality (null spikes, duplicates)
- compute failures in Databricks
- dependency failures between tasks

### Challenges without automation
- RCA is manual and time-consuming (**30–90 minutes**)
- engineers switch between multiple tools
- high dependency on senior engineers
- SLA breaches due to delayed resolution

---

## Solution
We implement an **MCP Server-based DataOps layer** that exposes operations as tools:

The GenAI agent can:
- check Airflow DAG run status
- identify failed tasks
- fetch Airflow logs
- extract Databricks run id
- fetch Databricks run output/error trace
- generate RCA summary
- safely rerun pipelines with guardrails

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
