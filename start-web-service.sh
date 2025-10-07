#!/bin/bash
# Arcane Auditor Web Service Startup Script (Linux/macOS)
# Usage: ./start-web-service.sh [--port PORT] [--host HOST] [--no-browser] [--help]

# Default values
DEFAULT_PORT=8080
DEFAULT_HOST="127.0.0.1"
OPEN_BROWSER=true

# Parse command line arguments
PORT=$DEFAULT_PORT
HOST=$DEFAULT_HOST

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
        --help)
            echo "Arcane Auditor Web Service Startup Script"
            echo ""
            echo "Usage: $0 [--port PORT] [--host HOST] [--no-browser] [--help]"
            echo ""
            echo "Options:"
            echo "  --port PORT     Port to run the server on (default: $DEFAULT_PORT)"
            echo "  --host HOST     Host to bind to (default: $DEFAULT_HOST)"
            echo "  --no-browser    Don't open browser automatically"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Start with defaults (opens browser)"
            echo "  $0 --port 3000        # Start on port 3000"
            echo "  $0 --host 0.0.0.0     # Start on all interfaces"
            echo "  $0 --no-browser        # Start without opening browser"
            echo ""
            echo "The web interface will be available at: http://$DEFAULT_HOST:$DEFAULT_PORT"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Starting Arcane Auditor Web Service..."
echo ""
echo "Server will be available at: http://$HOST:$PORT"
echo "Press Ctrl+C to stop the server"
echo ""

# Change to the project root directory
cd "$(dirname "$0")"

# Start the web server
if [ "$OPEN_BROWSER" = true ]; then
    uv run python web/server.py --host "$HOST" --port "$PORT" --open-browser
else
    uv run python web/server.py --host "$HOST" --port "$PORT"
fi
