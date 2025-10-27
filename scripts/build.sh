#!/bin/bash
# scripts/build.sh
# Arcane Auditor build script (Bash version for macOS)

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
pip install pyinstaller typer click pydantic lark-parser uvicorn fastapi starlette python-multipart openpyxl psutil pywebview requests

# --- Build -------------------------------------------------------------------
echo "Running PyInstaller..."

# Build CLI
pyinstaller ArcaneAuditorCLI.spec --clean

# Build Web server
pyinstaller ArcaneAuditorWeb.spec --clean

# Build Desktop app
pyinstaller ArcaneAuditorDesktop.spec --clean

# --- Code Signing (macOS) ----------------------------------------------------
if [ -n "$CODESIGN_IDENTITY" ]; then
    echo ""
    echo "=== Code Signing macOS Executables ==="
    echo "Using identity: $CODESIGN_IDENTITY"
    echo ""
    
    # Sign CLI executable
    echo "Signing ArcaneAuditorCLI..."
    codesign --force --options runtime \
        --sign "$CODESIGN_IDENTITY" \
        --entitlements entitlements.plist \
        --timestamp \
        dist/ArcaneAuditorCLI
    codesign --verify --verbose=2 dist/ArcaneAuditorCLI
    echo "✅ ArcaneAuditorCLI signed"
    echo ""
    
    # Sign Web server executable
    echo "Signing ArcaneAuditorWeb..."
    codesign --force --options runtime \
        --sign "$CODESIGN_IDENTITY" \
        --entitlements entitlements.plist \
        --timestamp \
        dist/ArcaneAuditorWeb
    codesign --verify --verbose=2 dist/ArcaneAuditorWeb
    echo "✅ ArcaneAuditorWeb signed"
    echo ""
    
    # Sign Desktop .app bundle (deep sign for all nested components)
    echo "Deep signing ArcaneAuditor.app..."
    codesign --force --deep --options runtime \
        --sign "$CODESIGN_IDENTITY" \
        --entitlements entitlements.plist \
        --timestamp \
        dist/ArcaneAuditor.app
    codesign --verify --deep --strict --verbose=2 dist/ArcaneAuditor.app
    echo "✅ ArcaneAuditor.app signed"
    echo ""
    
    echo "✅ All executables signed successfully"
else
    echo ""
    echo "⚠️  CODESIGN_IDENTITY not set - skipping code signing"
    echo "   Set CODESIGN_IDENTITY environment variable to enable signing"
fi

# --- Cleanup -----------------------------------------------------------------
deactivate

echo "Cleaning up temporary build environment..."
rm -rf "$BUILD_ENV"

echo ""
echo "Build complete!"
echo "   Final binary (CLI): dist/ArcaneAuditorCLI"
echo "   Final binary (Web): dist/ArcaneAuditorWeb"
echo "   Final app (Desktop): dist/ArcaneAuditor.app"
