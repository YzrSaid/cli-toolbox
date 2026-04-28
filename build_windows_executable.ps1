#Requires -Version 5.1
<#
.SYNOPSIS
    Builds the CLI Toolbox Windows executable using PyInstaller.
.DESCRIPTION
    Creates a self-contained cli-toolbox.exe in the dist\ folder.
    Run this script on a Windows machine with Python 3.10+ installed.
.EXAMPLE
    .\build_windows_executable.ps1
#>

$ErrorActionPreference = "Stop"

$ROOT_DIR    = $PSScriptRoot
$DIST_DIR    = "$ROOT_DIR\dist"
$BUILD_DIR   = "$ROOT_DIR\build"
$SPEC_FILE   = "$ROOT_DIR\cli-toolbox.spec"
$VENV_DIR    = "$ROOT_DIR\.build-venv-win"
$PYTHON_BIN  = "$VENV_DIR\Scripts\python.exe"

Write-Host "[1/3] Setting up build environment..." -ForegroundColor Cyan

if (-not (Test-Path $VENV_DIR)) {
    python -m venv $VENV_DIR
}

& $PYTHON_BIN -m pip install -q --upgrade pip
& $PYTHON_BIN -m pip install -q -r "$ROOT_DIR\requirements.txt"

Write-Host "[2/3] Building Windows executable with PyInstaller..." -ForegroundColor Cyan

& $PYTHON_BIN -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name cli-toolbox `
    --hidden-import pillow_heif `
    --collect-all pyfiglet `
    --collect-all rich `
    "$ROOT_DIR\main.py"

if (Test-Path $BUILD_DIR) { Remove-Item -Recurse -Force $BUILD_DIR }
if (Test-Path $SPEC_FILE) { Remove-Item -Force $SPEC_FILE }

Write-Host "[3/3] Done!" -ForegroundColor Green
Write-Host ""
Write-Host "Executable : $DIST_DIR\cli-toolbox.exe" -ForegroundColor White
