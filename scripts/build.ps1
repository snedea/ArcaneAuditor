# scripts/build.ps1
# 🧙 Arcane Auditor build script (PowerShell version)

# --- Setup -------------------------------------------------------------------

# Move to the repo root (parent of this script directory)
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot
Write-Host "🏗️  Building Arcane Auditor from $RepoRoot"

# --- Clean old artifacts -----------------------------------------------------
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# --- Create clean build environment -----------------------------------------
Write-Host "🐍 Creating isolated build environment..."
$BuildEnv = Join-Path $RepoRoot ".buildenv"
python -m venv $BuildEnv

& (Join-Path $BuildEnv "Scripts\activate.ps1")
pip install -U pip
pip install pyinstaller typer click pydantic lark-parser

# --- Build -------------------------------------------------------------------
Write-Host "🪄 Running PyInstaller..."
pyinstaller ArcaneAuditor.spec --clean

# --- Cleanup -----------------------------------------------------------------
deactivate

Write-Host "🧹 Cleaning up temporary build environment..."
Remove-Item -Recurse -Force $BuildEnv -ErrorAction SilentlyContinue

Write-Host "`n✅ Build complete!"
Write-Host "   Final binary: dist\ArcaneAuditor.exe"
