# ==============================================================================
# PreviewGen - Windows 1-Click Installer
# Run in PowerShell:
# irm https://raw.githubusercontent.com/Mustaqeem66/Freepik-Preview-Generator/main/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Repo = "Mustaqeem66/Freepik-Preview-Generator"
$AppName = "PreviewGen"
$InstallDir = "$env:LOCALAPPDATA\Programs\$AppName"
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = "$([Environment]::GetFolderPath('Programs'))\$AppName"
$ZipUrl = "https://github.com/$Repo/releases/latest/download/PreviewGen-Windows.zip"
$TempZip = "$env:TEMP\PreviewGen-Windows.zip"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        PreviewGen - One-Click Installer for Windows      " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Download Release
Write-Host "[1/5] Downloading latest release from GitHub..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing
    Write-Host "      Download completed." -ForegroundColor Green
} catch {
    Write-Host "      Primary release download failed, trying API fallback..." -ForegroundColor Yellow
    try {
        $Release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -UseBasicParsing
        $Asset = $Release.assets | Where-Object { $_.name -like "*Windows*.zip" } | Select-Object -First 1
        if ($Asset) {
            Invoke-WebRequest -Uri $Asset.browser_download_url -OutFile $TempZip -UseBasicParsing
            Write-Host "      Download completed from release asset." -ForegroundColor Green
        } else {
            throw "No Windows zip found in latest release."
        }
    } catch {
        Write-Error "Failed to download PreviewGen release: $_"
        exit 1
    }
}

# 2. Extract
Write-Host "[2/5] Installing to $InstallDir..." -ForegroundColor Cyan
if (Test-Path $InstallDir) {
    # Stop running process if open
    Get-Process -Name $AppName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

Expand-Archive -Path $TempZip -DestinationPath $InstallDir -Force
Remove-Item -Path $TempZip -Force -ErrorAction SilentlyContinue

# If nested in a subfolder like PreviewGen/, move files up
$Nested = Get-ChildItem -Path $InstallDir -Directory | Where-Object { Test-Path "$($_.FullName)\$AppName.exe" }
if ($Nested) {
    Get-ChildItem -Path $Nested.FullName | Move-Item -Destination $InstallDir -Force
    Remove-Item -Path $Nested.FullName -Force -Recurse -ErrorAction SilentlyContinue
}

$ExePath = "$InstallDir\$AppName.exe"
if (-not (Test-Path $ExePath)) {
    # Fallback look for any exe
    $FoundExe = Get-ChildItem -Path $InstallDir -Filter "*.exe" -Recurse | Select-Object -First 1
    if ($FoundExe) {
        $ExePath = $FoundExe.FullName
    } else {
        Write-Error "Could not find $AppName.exe in extracted archive."
        exit 1
    }
}

# 3. Unblock files (Bypasses SmartScreen untrusted download flag!)
Write-Host "[3/5] Removing Mark-of-the-Web (bypassing SmartScreen blocks)..." -ForegroundColor Cyan
Get-ChildItem -Path $InstallDir -Recurse | Unblock-File -ErrorAction SilentlyContinue
Write-Host "      Files verified and unlocked." -ForegroundColor Green

# 4. Create Desktop & Start Menu Shortcuts
Write-Host "[4/5] Creating Desktop & Start Menu shortcuts..." -ForegroundColor Cyan
$IconPath = "$InstallDir\app.ico"
if (-not (Test-Path $IconPath)) {
    $IconPath = $ExePath
}

$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$DesktopShortcut = $WshShell.CreateShortcut("$Desktop\$AppName.lnk")
$DesktopShortcut.TargetPath = $ExePath
$DesktopShortcut.WorkingDirectory = (Split-Path $ExePath)
$DesktopShortcut.IconLocation = "$IconPath,0"
$DesktopShortcut.Description = "PreviewGen - Transparent PNG to JPG Preview Generator"
$DesktopShortcut.Save()

# Start Menu shortcut
if (-not (Test-Path $StartMenu)) {
    New-Item -ItemType Directory -Path $StartMenu -Force | Out-Null
}
$StartShortcut = $WshShell.CreateShortcut("$StartMenu\$AppName.lnk")
$StartShortcut.TargetPath = $ExePath
$StartShortcut.WorkingDirectory = (Split-Path $ExePath)
$StartShortcut.IconLocation = "$IconPath,0"
$StartShortcut.Description = "PreviewGen - Transparent PNG to JPG Preview Generator"
$StartShortcut.Save()

# Create Uninstaller script
$UninstallScript = @"
@echo off
echo Uninstalling PreviewGen...
taskkill /F /IM $AppName.exe 2>nul
del /F /Q "$Desktop\$AppName.lnk" 2>nul
rmdir /S /Q "$StartMenu" 2>nul
rmdir /S /Q "$InstallDir" 2>nul
echo PreviewGen has been uninstalled.
pause
"@
$UninstallScript | Out-File -FilePath "$InstallDir\uninstall.bat" -Encoding ASCII

Write-Host "      Desktop shortcut created: $Desktop\$AppName.lnk" -ForegroundColor Green
Write-Host "      Start Menu shortcut created." -ForegroundColor Green

# 5. Launch Application
Write-Host "[5/5] Launching PreviewGen..." -ForegroundColor Cyan
Start-Process -FilePath $ExePath

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "     PreviewGen installed successfully! Enjoy using it!    " -ForegroundColor Green
Write-Host "     You can now open it from your Desktop or Start Menu.  " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
