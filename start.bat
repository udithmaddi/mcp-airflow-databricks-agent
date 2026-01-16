@echo off
REM Silent wrapper for MCP Server
cd /d "%~dp0"
".venv\Scripts\python.exe" server.py
