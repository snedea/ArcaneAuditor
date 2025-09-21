# Arcane Auditor Mystical Web Interface 🔮

A mystical web-based interface for the Arcane Auditor, designed for the Developers and Dragons initiative.

## 🚀 Quick Start

### Option 1: Simple Start (Recommended)

```bash
# Run the startup script (handles everything automatically)
python web/start_web_interface.py
```

The server will be available at: http://localhost:8000

### Option 2: Manual Start

#### 1. Install Dependencies

```bash
# Install web dependencies
pip install fastapi uvicorn[standard] python-multipart aiofiles

# For frontend development (optional)
cd web_frontend
npm install
npm run build
cd ..
```

#### 2. Start the Server

```bash
# Start the web server
python web_server.py
```

## 🌐 Accessing the Web Interface

Once the server is running, open your browser and navigate to:

- **Local**: http://localhost:8000
- **Network**: http://your-server-ip:8000 (for team access)

## 📋 Features

### Core Functionality

- ✅ **File Upload**: Drag-and-drop ZIP file upload
- ✅ **Real-time Analysis**: Immediate analysis results
- ✅ **Interactive Results**: Filter and sort findings by severity, file, or rule
- ✅ **Export Options**: Download results as Excel files
- ✅ **Configuration Management**: Save and load rule configurations

### User Interface

- 📱 **Responsive Design**: Works on desktop and mobile
- 🎨 **Modern UI**: Clean, intuitive interface
- 🔍 **Advanced Filtering**: Filter findings by severity level
- 📊 **Visual Summary**: Clear overview of analysis results

## 🛠️ Development

### Frontend Development

```bash
cd web_frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Backend Development

The web server is a single file (`web_server.py`) that wraps your existing CLI functionality. No changes to the core analysis logic are needed.

## 📁 File Structure

```
extend-reviewer/
├── web_server.py              # Main FastAPI web server
├── web_server_start.py        # Startup script with dependency management
├── web_frontend/              # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── types/            # TypeScript type definitions
│   │   └── App.tsx           # Main React app
│   ├── package.json          # Frontend dependencies
│   └── dist/                 # Built frontend (auto-generated)
├── uploads/                  # Temporary file storage
└── configs/                  # Saved configurations
```

## 🔧 Configuration

### Rule Configuration

- Access the configuration panel in the web interface
- Enable/disable specific rules
- Override severity levels
- Save configurations for reuse

### Server Configuration

The server runs with these defaults:

- **Host**: 0.0.0.0 (accessible from network)
- **Port**: 8000
- **File Storage**: `./uploads/` directory
- **Config Storage**: `./configs/` directory

## 🚀 Deployment Options

### Local Development

```bash
python web_server_start.py
```

### Team Server

```bash
# Run on team server for shared access
python web_server.py --host 0.0.0.0 --port 8000
```

### Docker (Optional)

```dockerfile
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "web_server.py"]
```

## 📊 API Endpoints

The web server provides these REST API endpoints:

- `POST /api/analyze` - Upload and analyze ZIP file
- `GET /api/rules` - List available rules
- `POST /api/config` - Save configuration
- `GET /api/config/{name}` - Load configuration
- `GET /api/configs` - List saved configurations
- `GET /api/health` - Health check

## 🔒 Security Notes

This web interface is designed for **internal team use only**:

- No authentication required
- No rate limiting
- Files stored temporarily in `./uploads/`
- Accessible to anyone on the network

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors:**

```bash
# Install dependencies
pip install fastapi uvicorn[standard] python-multipart aiofiles
```

**Frontend not loading:**

```bash
# Build the frontend
cd web_frontend
npm install
npm run build
cd ..
```

**Port already in use:**

```bash
# Use a different port
python web_server.py --port 8001
```

**File upload fails:**

- Ensure the file is a valid ZIP file
- Check file size limits (default: 50MB per file, 500MB per ZIP)
- Verify write permissions in the `./uploads/` directory

## 📝 Usage Tips

1. **First Time Setup**: Run `python web_server_start.py` for automatic setup
2. **Team Access**: Use `--host 0.0.0.0` to allow network access
3. **Configuration**: Save rule configurations for consistent team standards
4. **Results**: Download Excel files for detailed analysis and sharing
5. **Mobile**: The interface works on mobile devices for quick checks

## 🔄 Updates

To update the web interface:

1. Pull the latest changes from git
2. Run `python web_server_start.py` to update dependencies
3. Restart the server

The web interface automatically uses your existing CLI tool's core functionality, so updates to analysis rules are immediately available.
