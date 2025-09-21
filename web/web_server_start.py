#!/usr/bin/env python3
"""
Simple script to start the Arcane Auditor web server.
This script handles dependency installation and server startup.
"""

import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        subprocess.check_call([
            "uv", "run", "python", "-c", 
            "import fastapi, uvicorn; print('Dependencies available')"
        ], stdout=subprocess.DEVNULL)
        print("✅ Dependencies already available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Dependencies not available. Please run: uv add fastapi uvicorn[standard] python-multipart aiofiles")
        return False

def build_frontend():
    """Build the React frontend if needed."""
    frontend_dir = Path("web/frontend")
    if not frontend_dir.exists():
        print("⚠️  Frontend not found, will serve basic HTML interface")
        return False
    
    dist_dir = frontend_dir / "dist"
    if dist_dir.exists():
        print("✅ Frontend already built")
        return True
    
    print("🏗️  Building frontend...")
    try:
        # Check if npm is available
        subprocess.check_call(["npm", "--version"], stdout=subprocess.DEVNULL)
        
        # Install frontend dependencies
        subprocess.check_call(["npm", "install"], cwd=frontend_dir)
        
        # Build frontend
        subprocess.check_call(["npm", "run", "build"], cwd=frontend_dir)
        
        print("✅ Frontend built successfully")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  npm not found or build failed, will serve basic HTML interface")
        return False

def start_server():
    """Start the web server."""
    print("🚀 Starting Arcane Auditor Web Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📝 Press Ctrl+C to stop the server")
    print()
    
    try:
        # Start server using uv run
        subprocess.run([
            "uv", "run", "python", "web_server.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main function."""
    print("🔍 Arcane Auditor Web Server Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the arcane-auditor root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Build frontend
    build_frontend()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
