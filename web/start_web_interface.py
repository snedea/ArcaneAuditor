#!/usr/bin/env python3
"""
Start the Extend Reviewer Web Interface
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Get the web directory path
    web_dir = Path(__file__).parent
    project_root = web_dir.parent
    
    # Check if frontend is built
    dist_dir = web_dir / "frontend" / "dist"
    if not dist_dir.exists():
        print("❌ Frontend not built. Please run: python web/setup_web_interface.py")
        sys.exit(1)
    
    # Start the server from the web directory
    print("🧙‍♂️ Starting Arcane Auditor Web Interface...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📝 Press Ctrl+C to stop the server")
    print()
    
    try:
        # Use uv run to ensure we're in the virtual environment
        subprocess.run([
            "uv", "run", "uvicorn", "web_server:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ], cwd=str(web_dir))
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
