@echo off
cd /d "%~dp0"
echo ==== MediaHub: instalando entorno ====
python --version >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python. Instalalo desde python.org y marca "Add to PATH".
    pause
    exit /b 1
)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Listo. Ahora abre run.bat
pause
