@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
if exist "frontend\package.json" (
  echo Building React + Framer frontend...
  cd frontend
  call npm ci
  call npm run build
  cd ..
)
python -m pip install --upgrade pyinstaller
pyinstaller --noconsole --name PreviewGen --icon=app.ico --add-data "app.ico;." --add-data "frontend\dist;frontend\dist" --collect-all psd_tools --collect-all trimesh --collect-all webview --collect-all ezdxf --collect-all olefile --collect-all cascadio --collect-all resvg_py --collect-all matplotlib app.py --clean -y
if errorlevel 1 (
  echo Build failed. Read the error above.
  pause
  exit /b 1
)
echo.
copy /y install_desktop_icon.bat dist\PreviewGen\Install-Desktop-Icon.bat >nul
copy /y app.ico dist\PreviewGen\app.ico >nul
copy /y USER_GUIDE.txt dist\PreviewGen\USER_GUIDE.txt >nul

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if defined ISCC (
  echo Compiling Windows Setup Wizard (PreviewGen-Setup.exe)...
  "%ISCC%" installer.iss
  if exist "dist\PreviewGen-Setup.exe" (
    echo.
    echo ==========================================================
    echo Installer Wizard created: dist\PreviewGen-Setup.exe
    echo Portable Executable is at: dist\PreviewGen\PreviewGen.exe
    echo ==========================================================
  )
) else (
  echo The portable executable is ready at: dist\PreviewGen\PreviewGen.exe
  echo Note: To build the Setup Wizard locally, install Inno Setup 6.
)
pause
