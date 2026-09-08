@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m src.main >> pipeline_execution.log 2>&1