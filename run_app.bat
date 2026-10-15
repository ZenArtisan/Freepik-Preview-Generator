@echo off
cd /d "%~dp0"

if exist "dist\PreviewGen\PreviewGen.exe" (
  start "" "dist\PreviewGen\PreviewGen.exe"
  exit /b 0
)

if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" main.py
  exit /b 0
)

if exist ".venv\Scripts\python.exe" (
  start "" ".venv\Scripts\python.exe" main.py
  exit /b 0
)

echo Setting up environment...
call setup_windows.bat
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" main.py
)
