@echo off
cd /d "%~dp0"

if exist "dist\PreviewGen\PreviewGen.exe" (
  start "" "dist\PreviewGen\PreviewGen.exe"
  exit /b 0
)
if not exist "frontend\dist\index.html" (
  echo Building frontend and setting up environment...
  call setup_windows.bat
)

if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" app.py
  exit /b 0
)

if exist ".venv\Scripts\python.exe" (
  start "" ".venv\Scripts\python.exe" app.py
  exit /b 0
)

echo Setting up environment...
call setup_windows.bat
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" app.py
)
