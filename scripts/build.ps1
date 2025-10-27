# scripts/build.ps1
# Arcane Auditor build script (PowerShell version)

# --- Setup -------------------------------------------------------------------

# Move to the repo root (parent of this script directory)
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot
Write-Host "Building Arcane Auditor from $RepoRoot"

# --- Clean old artifacts -----------------------------------------------------
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# --- Create clean build environment -----------------------------------------
Write-Host "Creating isolated build environment..."
$BuildEnv = Join-Path $RepoRoot ".buildenv"
python -m venv $BuildEnv

& (Join-Path $BuildEnv "Scripts\activate.ps1")
pip install -U pip
pip install pyinstaller typer click pydantic lark-parser uvicorn fastapi starlette python-multipart openpyxl psutil pywebview requests

# --- Build -------------------------------------------------------------------
Write-Host "Building Desktop version..."
pyinstaller ArcaneAuditorDesktop.spec --clean

Write-Host "Building CLI version..."
pyinstaller ArcaneAuditorCLI.spec --clean

Write-Host "Building Web version..."
pyinstaller ArcaneAuditorWeb.spec --clean

# --- Cleanup -----------------------------------------------------------------
deactivate

Write-Host "Cleaning up temporary build environment..."
Remove-Item -Recurse -Force $BuildEnv -ErrorAction SilentlyContinue

Write-Host "--------------------------------"
Write-Host "Build complete!"
Write-Host "   Final binary (CLI): dist\ArcaneAuditorCLI.exe"
Write-Host "   Final binary (Web): dist\ArcaneAuditorWeb.exe"
Write-Host "   Final binary (Desktop): dist\ArcaneAuditor.exe"