@echo off
cd /d "%~dp0"
if not exist .venv (
    echo Primero ejecuta setup.bat
    pause
    exit /b 1
)
call .venv\Scripts\activate
python app.py
if errorlevel 1 pause
