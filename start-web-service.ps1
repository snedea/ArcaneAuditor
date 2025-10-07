# Arcane Auditor Web Service Startup Script (PowerShell)
# This script starts the Arcane Auditor web service with default settings

Write-Host "Starting Arcane Auditor Web Service..." -ForegroundColor Green
Write-Host ""
Write-Host "Server will be available at: http://127.0.0.1:8080" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Change to the project root directory
Set-Location $PSScriptRoot

# Start the web server with auto-open browser
uv run python web/server.py --open-browser
