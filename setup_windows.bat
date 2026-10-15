@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 py -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Setup failed.
  pause
  exit /b 1
)
echo.
echo Setup complete. Double-click run_app.bat.
pause
