@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==========================================================
echo        PreviewGen - Local Desktop Installer
echo ==========================================================
echo.

set "TARGET_EXE=%~dp0PreviewGen.exe"
set "WORKING_DIR=%~dp0"
set "APP_ICO=%~dp0app.ico"

if not exist "!TARGET_EXE!" (
    set "TARGET_EXE=%~dp0dist\PreviewGen\PreviewGen.exe"
    set "WORKING_DIR=%~dp0dist\PreviewGen"
    if not exist "!TARGET_EXE!" (
        if exist "%~dp0build_windows.bat" (
            echo Executable not found in dist\. Building now with build_windows.bat...
            call "%~dp0build_windows.bat"
        )
        if not exist "!TARGET_EXE!" (
            echo.
            echo [ERROR] PreviewGen.exe was not found.
            pause
            exit /b 1
        )
    )
)

if not exist "!APP_ICO!" (
    if exist "%WORKING_DIR%\app.ico" (
        set "APP_ICO=%WORKING_DIR%\app.ico"
    )
)

echo Creating Desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$wsh = New-Object -ComObject WScript.Shell; " ^
    "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
    "if (Test-Path $desktop) { " ^
    "  $s = $wsh.CreateShortcut(\"$desktop\PreviewGen.lnk\"); " ^
    "  $s.TargetPath = '!TARGET_EXE!'; " ^
    "  $s.WorkingDirectory = '!WORKING_DIR!'; " ^
    "  $s.IconLocation = '!APP_ICO!,0'; " ^
    "  $s.Description = 'PreviewGen - Transparent PNG to JPG Preview Generator'; " ^
    "  $s.Save(); " ^
    "}"

echo Creating Start Menu shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$wsh = New-Object -ComObject WScript.Shell; " ^
    "$startMenu = \"$([Environment]::GetFolderPath('Programs'))\PreviewGen\"; " ^
    "if (!(Test-Path $startMenu)) { New-Item -ItemType Directory -Path $startMenu -Force | Out-Null }; " ^
    "$s = $wsh.CreateShortcut(\"$startMenu\PreviewGen.lnk\"); " ^
    "  $s.TargetPath = '!TARGET_EXE!'; " ^
    "  $s.WorkingDirectory = '!WORKING_DIR!'; " ^
    "  $s.IconLocation = '!APP_ICO!,0'; " ^
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
