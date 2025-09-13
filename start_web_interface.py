#!/usr/bin/env python3
"""
Start the Extend Reviewer Web Interface
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Check if frontend is built
    dist_dir = Path("web_frontend/dist")
    if not dist_dir.exists():
        print("❌ Frontend not built. Please run: python setup_web_interface.py")
        sys.exit(1)
    
    # Start the server
    print("🚀 Starting Extend Reviewer Web Interface...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📝 Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "web_server:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
