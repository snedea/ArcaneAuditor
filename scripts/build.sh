#!/bin/bash
# scripts/build.sh
# Arcane Auditor build script (Bash version for macOS/Linux)

set -e  # Exit on error

# --- Setup -------------------------------------------------------------------

# Move to the repo root (parent of this script directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
echo "Building Arcane Auditor from $REPO_ROOT"

# --- Clean old artifacts -----------------------------------------------------
echo "Cleaning old build artifacts..."
rm -rf build dist

# --- Create clean build environment -----------------------------------------
echo "Creating isolated build environment..."
BUILD_ENV="$REPO_ROOT/.buildenv"
python3 -m venv "$BUILD_ENV"

# Activate the virtual environment
source "$BUILD_ENV/bin/activate"

# Upgrade pip and install dependencies
pip install -U pip
pip install pyinstaller typer click pydantic lark-parser uvicorn fastapi starlette python-multipart openpyxl psutil

# --- Build -------------------------------------------------------------------
echo "Running PyInstaller..."
pyinstaller ArcaneAuditor.spec --clean
pyinstaller ArcaneAuditorWeb.spec --clean

# --- Cleanup -----------------------------------------------------------------
deactivate

echo "Cleaning up temporary build environment..."
rm -rf "$BUILD_ENV"

echo ""
echo "Build complete!"
echo "   Final binary (CLI): dist/ArcaneAuditorCLI"
echo "   Final binary (Web): dist/ArcaneAuditorWeb"