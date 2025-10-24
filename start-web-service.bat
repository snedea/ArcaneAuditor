@echo off
REM ==========================================================
REM Arcane Auditor - Web Service Startup
REM ----------------------------------------------------------
REM • Dev mode: uses `uv run web\server.py`
REM • Packaged mode: runs ArcaneAuditorWeb.exe if it exists
REM ==========================================================

setlocal
set "APP_NAME=ArcaneAuditorWeb.exe"
set "APP_PATH=%~dp0..\dist\%APP_NAME%"

if exist "%APP_PATH%" (
    echo Starting Arcane Auditor (packaged mode)
    "%APP_PATH%" %*
) else (
    echo Starting Arcane Auditor (developer mode via uv)
    uv run web\server.py %*
)

pause
