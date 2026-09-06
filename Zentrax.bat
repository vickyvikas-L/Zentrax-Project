@echo off
title Zentrax AI Assistant
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run Zentrax
python run.py %*

pause
