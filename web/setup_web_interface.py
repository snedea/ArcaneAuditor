#!/usr/bin/env python3
"""
Setup script for Extend Reviewer Web Interface.
This script handles the complete setup for external users.
"""

import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_node_installed():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Node.js is not installed")
    print("   Please install Node.js from: https://nodejs.org/")
    print("   Minimum version: 16.x or higher")
    return False

def check_npm_installed():
    """Check if npm is installed."""
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ npm is not installed")
    print("   npm should come with Node.js installation")
    return False

def install_python_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    try:
        # Check if uv is available
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        print("   Using uv package manager...")
        subprocess.run([
            "uv", "add", "fastapi", "uvicorn[standard]", "python-multipart", "aiofiles"
        ], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   Using pip package manager...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "fastapi", "uvicorn[standard]", "python-multipart", "aiofiles"
        ], check=True)
    
    print("✅ Python dependencies installed")
    return True

def build_frontend():
    """Build the React frontend."""
    print("🏗️  Building React frontend...")
    
    frontend_dir = Path("web/frontend")
    if not frontend_dir.exists():
        print("❌ web/frontend directory not found")
        return False
    
    try:
        # Install npm dependencies
        print("   Installing npm dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        # Build the frontend
        print("   Building production assets...")
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
        
        print("✅ Frontend built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend build failed: {e}")
        return False

def create_startup_script():
    """Create a simple startup script."""
    startup_script = """#!/usr/bin/env python3
\"\"\"
Start the Extend Reviewer Web Interface
\"\"\"

import subprocess
import sys
from pathlib import Path

def main():
    # Check if frontend is built
    dist_dir = Path("web/frontend/dist")
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
        print("\\n👋 Server stopped")

if __name__ == "__main__":
    main()
"""
    
    with open("start_web_interface.py", "w") as f:
        f.write(startup_script)
    
    print("✅ Created start_web_interface.py")

def create_readme():
    """Create a README for the web interface."""
    readme_content = """# Extend Reviewer Web Interface Setup

## Prerequisites

- Python 3.8 or higher
- Node.js 16.x or higher (includes npm)

## Quick Setup

1. **Run the setup script:**
   ```bash
   python setup_web_interface.py
   ```

2. **Start the web interface:**
   ```bash
   python start_web_interface.py
   ```

3. **Open your browser:**
   Go to: http://localhost:8000

## Manual Setup (if needed)

### 1. Install Python Dependencies
```bash
# Using uv (recommended)
uv add fastapi uvicorn[standard] python-multipart aiofiles

# Or using pip
pip install fastapi uvicorn[standard] python-multipart aiofiles
```

### 2. Build Frontend
```bash
cd web/frontend
npm install
npm run build
cd ..
```

### 3. Start Server
```bash
python -m uvicorn web_server:app --host 0.0.0.0 --port 8000
```

## Features

- 📁 Drag-and-drop file upload
- ⚙️ Rule configuration management
- 📊 Interactive results display
- 🔍 Filter and sort findings
- 📥 Export results as Excel files

## Troubleshooting

### "Node.js not found"
Install Node.js from: https://nodejs.org/

### "Frontend not built"
Run: `python setup_web_interface.py`

### "Port 8000 already in use"
Use a different port: `--port 8001`

## For Development

To modify the frontend:
```bash
cd web/frontend
npm run dev  # Development server with hot reload
```

To rebuild after changes:
```bash
cd web/frontend
npm run build
```
"""
    
    with open("WEB_INTERFACE_README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created WEB_INTERFACE_README.md")

def main():
    """Main setup function."""
    print("🔍 Extend Reviewer Web Interface Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the extend-reviewer root directory")
        sys.exit(1)
    
    # Check prerequisites
    print("\\n📋 Checking prerequisites...")
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_installed():
        sys.exit(1)
    
    if not check_npm_installed():
        sys.exit(1)
    
    # Install dependencies
    print("\\n📦 Installing dependencies...")
    if not install_python_dependencies():
        sys.exit(1)
    
    # Build frontend
    print("\\n🏗️  Building frontend...")
    if not build_frontend():
        sys.exit(1)
    
    # Create helper files
    print("\\n📝 Creating helper files...")
    create_startup_script()
    create_readme()
    
    print("\\n🎉 Setup complete!")
    print("\\n📖 Next steps:")
    print("   1. Run: python start_web_interface.py")
    print("   2. Open: http://localhost:8000")
    print("   3. Upload a Workday Extend ZIP file to analyze")
    print("\\n📚 For more info, see: WEB_INTERFACE_README.md")

if __name__ == "__main__":
    main()
