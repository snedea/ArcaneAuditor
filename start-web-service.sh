#!/bin/bash
# ==========================================================
# Arcane Auditor - Web Service Startup Script
# ----------------------------------------------------------
# Launches ArcaneAuditor Web Service.
#  • In dev mode: uses `uv run web/server.py`
#  • In packaged mode: runs ArcaneAuditorWeb executable
# Pass CLI args to override config (e.g. --port 9000 --no-browser)
# ==========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/../dist/ArcaneAuditorWeb"

if [ -f "$APP_PATH" ]; then
  echo "🌐 Starting Arcane Auditor (packaged mode)"
  "$APP_PATH" "$@"
else
  echo "🧙 Starting Arcane Auditor (developer mode via uv)"
  cd "$SCRIPT_DIR/.." || exit 1
  uv run web/server.py "$@"
fi
