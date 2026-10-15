@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pyinstaller
pyinstaller --noconsole --name PreviewGen --icon=app.ico --add-data "app.ico;." main.py --clean -y
if errorlevel 1 (
  echo Build failed. Read the error above.
  pause
  exit /b 1
)
echo.
echo Build complete. The executable is at: dist\PreviewGen\PreviewGen.exe
pause
