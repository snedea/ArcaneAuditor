@echo off
REM Arcane Auditor Web Service Startup Script (Windows) - Advanced
REM This script allows you to specify custom port and host settings

setlocal enabledelayedexpansion

REM Default values
set DEFAULT_PORT=8080
set DEFAULT_HOST=127.0.0.1
set DEFAULT_OPEN_BROWSER=true

REM Parse command line arguments
set PORT=%DEFAULT_PORT%
set HOST=%DEFAULT_HOST%
set OPEN_BROWSER=%DEFAULT_OPEN_BROWSER%

:parse_args
if "%~1"=="" goto :start_server
if "%~1"=="--port" (
    set PORT=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--host" (
    set HOST=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--no-browser" (
    set OPEN_BROWSER=false
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo Usage: %0 [--port PORT] [--host HOST] [--no-browser] [--help]
    echo.
    echo Options:
    echo   --port PORT     Port to run the server on (default: %DEFAULT_PORT%)
    echo   --host HOST     Host to bind to (default: %DEFAULT_HOST%)
    echo   --no-browser    Don't open browser automatically
    echo   --help          Show this help message
    echo.
    echo Examples:
    echo   %0                    # Start with defaults
    echo   %0 --port 3000        # Start on port 3000
    echo   %0 --host 0.0.0.0     # Start on all interfaces
    echo   %0 --no-browser        # Start without opening browser
    exit /b 0
)
shift
goto :parse_args

:start_server
echo Starting Arcane Auditor Web Service...
echo.
echo Server will be available at: http://%HOST%:%PORT%
echo Press Ctrl+C to stop the server
echo.

REM Change to the project root directory
cd /d "%~dp0"

REM Start the web server
if "%OPEN_BROWSER%"=="true" (
    uv run python web/server.py --host %HOST% --port %PORT% --open-browser
) else (
    uv run python web/server.py --host %HOST% --port %PORT%
)

pause
