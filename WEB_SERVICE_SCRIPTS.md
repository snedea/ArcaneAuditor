# Arcane Auditor Web Service Startup Scripts

This directory contains convenient scripts to start the Arcane Auditor web service without having to remember the command syntax.

## Available Scripts

### Windows
- **`start-web-service.bat`** - Comprehensive startup script with built-in options

### Linux/macOS
- **`start-web-service.sh`** - Comprehensive startup script with built-in options

## Usage Examples

### Simple Usage (Default Settings)
```bash
# Windows
start-web-service.bat

# Linux/macOS
./start-web-service.sh
```

### Advanced Usage with Options
```bash
# Start on port 3000
start-web-service.bat --port 3000

# Start on all network interfaces
start-web-service.bat --host 0.0.0.0

# Start without opening browser
start-web-service.bat --no-browser

# Show help
start-web-service.bat --help
```

## Default Settings

- **Host**: `127.0.0.1` (localhost)
- **Port**: `8080`
- **Auto-open browser**: `true`

## Requirements

### With UV (Recommended) ⭐
- `uv` package manager (automatically manages Python 3.12+)
- All project dependencies installed (`uv sync`)

> 💡 **Note:** The startup scripts use UV by default. UV automatically downloads and manages Python - no separate installation needed!

### With pip (Alternative)
- Python 3.12+ must be pre-installed
- All project dependencies installed (`pip install -r requirements.txt`)
- Modify the script to use `python web/server.py` instead of `uv run python web/server.py`

## Troubleshooting

If you encounter issues:

1. Make sure you're in the project root directory
2. Ensure all dependencies are installed: `uv sync`
3. Check that port 8080 is not already in use
4. For Linux/macOS, ensure the script is executable: `chmod +x start-web-service.sh`
