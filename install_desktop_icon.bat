@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==========================================================
echo        PreviewGen - Local Desktop Installer
echo ==========================================================
echo.

set "TARGET_EXE=%~dp0dist\PreviewGen\PreviewGen.exe"
set "APP_ICO=%~dp0app.ico"

if not exist "!TARGET_EXE!" (
    echo Executable not found in dist\. Building now with build_windows.bat...
    call build_windows.bat
    if not exist "!TARGET_EXE!" (
        echo.
        echo [ERROR] Build failed or dist\PreviewGen\PreviewGen.exe was not created.
        pause
        exit /b 1
    )
)

echo Creating Desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$wsh = New-Object -ComObject WScript.Shell; " ^
    "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
    "$s = $wsh.CreateShortcut(\"$desktop\PreviewGen.lnk\"); " ^
    "$s.TargetPath = '%TARGET_EXE%'; " ^
    "$s.WorkingDirectory = '%~dp0dist\PreviewGen'; " ^
    "$s.IconLocation = '%APP_ICO%,0'; " ^
    "$s.Description = 'PreviewGen - Transparent PNG to JPG Preview Generator'; " ^
    "$s.Save()"

echo Creating Start Menu shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$wsh = New-Object -ComObject WScript.Shell; " ^
    "$startMenu = \"$([Environment]::GetFolderPath('Programs'))\PreviewGen\"; " ^
    "if (!(Test-Path $startMenu)) { New-Item -ItemType Directory -Path $startMenu -Force | Out-Null }; " ^
    "$s = $wsh.CreateShortcut(\"$startMenu\PreviewGen.lnk\"); " ^
    "$s.TargetPath = '%TARGET_EXE%'; " ^
    "$s.WorkingDirectory = '%~dp0dist\PreviewGen'; " ^
    "$s.IconLocation = '%APP_ICO%,0'; " ^
    "$s.Description = 'PreviewGen - Transparent PNG to JPG Preview Generator'; " ^
    "$s.Save()"

echo.
echo ==========================================================
echo [SUCCESS] PreviewGen installed to your Desktop & Start Menu!
echo ==========================================================
echo.
echo Launching PreviewGen now...
start "" "!TARGET_EXE!"
exit /b 0
