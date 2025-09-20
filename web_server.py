"""
Web server for Extend Reviewer - provides a web interface for the code review tool.
This wraps the existing CLI functionality in a FastAPI web server for internal team use.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import existing core logic (no changes needed!)
from file_processing import FileProcessor
from parser.rules_engine import RulesEngine
from parser.app_parser import ModelParser
from parser.config import ExtendReviewerConfig
from output.formatter import OutputFormatter, OutputFormat
from parser.rules.base import Finding

# Create FastAPI app
app = FastAPI(
    title="Extend Reviewer Web",
    description="Web interface for Workday Extend application code review",
    version="1.0.0"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
CONFIG_DIR = Path("configs")
STATIC_DIR = Path("web_frontend/dist")

UPLOAD_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Serve static files if they exist
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    # Also serve assets directly
    if (STATIC_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

# Global analysis state (simple in-memory storage for internal use)
analysis_cache: Dict[str, Dict[str, Any]] = {}


class AnalysisResult:
    """Simple data class for analysis results."""
    def __init__(self, findings: List[Finding], total_files: int, total_rules: int, 
                 zip_filename: str, config_used: Optional[str] = None):
        self.findings = findings
        self.total_files = total_files
        self.total_rules = total_rules
        self.zip_filename = zip_filename
        self.config_used = config_used
        self.timestamp = datetime.now().isoformat()


def save_config(name: str, config: ExtendReviewerConfig) -> str:
    """Save configuration to file."""
    config_path = CONFIG_DIR / f"{name}.json"
    config.to_file(str(config_path))
    return str(config_path)


def load_config(name: str) -> Optional[ExtendReviewerConfig]:
    """Load configuration from file."""
    config_path = CONFIG_DIR / f"{name}.json"
    if config_path.exists():
        return ExtendReviewerConfig.from_file(str(config_path))
    return None


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main HTML page."""
    if STATIC_DIR.exists():
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    
    # Fallback HTML if no frontend is built yet
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Extend Reviewer Web</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
            .upload-area.dragover { border-color: #007bff; background-color: #f8f9fa; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .results { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 4px; }
            .finding { margin: 10px 0; padding: 10px; border-left: 4px solid #dc3545; background: white; }
            .finding.severe { border-left-color: #dc3545; }
            .finding.warning { border-left-color: #ffc107; }
            .finding.info { border-left-color: #17a2b8; }
        </style>
    </head>
    <body>
        <h1>🔍 Extend Reviewer Web</h1>
        <p>Upload a Workday Extend application ZIP file to analyze it for code quality issues.</p>
        
        <div class="upload-area" id="uploadArea">
            <p>📁 Drag and drop your ZIP file here, or click to select</p>
            <input type="file" id="fileInput" accept=".zip" style="display: none;">
            <button onclick="document.getElementById('fileInput').click()">Choose File</button>
        </div>
        
        <div id="results" class="results" style="display: none;">
            <h3>Analysis Results</h3>
            <div id="resultsContent"></div>
        </div>

        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const results = document.getElementById('results');
            const resultsContent = document.getElementById('resultsContent');

            // Drag and drop functionality
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFile(files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFile(e.target.files[0]);
                }
            });

            async function handleFile(file) {
                if (!file.name.endsWith('.zip')) {
                    alert('Please select a ZIP file');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                try {
                    uploadArea.innerHTML = '<p>🔄 Analyzing... Please wait</p>';
                    
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`Server error: ${response.status} - ${errorText}`);
                    }

                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    console.error('Upload error:', error);
                    uploadArea.innerHTML = '<p>❌ Error: ' + error.message + '</p><button onclick="resetUpload()">Try Again</button>';
                }
            }

            function displayResults(data) {
                uploadArea.innerHTML = '<p>✅ Analysis Complete!</p><button onclick="resetUpload()">Analyze Another File</button>';
                
                let html = `<h4>📊 Summary</h4>`;
                html += `<p>Files analyzed: ${data.total_files} | Rules executed: ${data.total_rules} | Issues found: ${data.findings.length}</p>`;
                
                if (data.findings.length === 0) {
                    html += '<p>✅ No issues found! Your code looks great!</p>';
                } else {
                    html += '<h4>🚨 Issues Found</h4>';
                    data.findings.forEach(finding => {
                        const severityClass = finding.severity.toLowerCase();
                        html += `
                            <div class="finding ${severityClass}">
                                <strong>[${finding.rule_id}:${finding.line}]</strong> ${finding.message}<br>
                                <small>File: ${finding.file_path} | Severity: ${finding.severity}</small>
                            </div>
                        `;
                    });
                }

                resultsContent.innerHTML = html;
                results.style.display = 'block';
            }

            function resetUpload() {
                uploadArea.innerHTML = '<p>📁 Drag and drop your ZIP file here, or click to select</p><button onclick="document.getElementById(\'fileInput\').click()">Choose File</button>';
                results.style.display = 'none';
                fileInput.value = '';
            }
        </script>
    </body>
    </html>
    """)


@app.post("/api/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    config_name: Optional[str] = Form(None),
    output_format: str = Form("json")
):
    """
    Analyze a Workday Extend application ZIP file.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP file")
    
    try:
        # Save uploaded file temporarily
        temp_file_path = UPLOAD_DIR / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Load configuration
        config = None
        if config_name:
            config = load_config(config_name)
            if not config:
                raise HTTPException(status_code=400, detail=f"Configuration '{config_name}' not found")
        else:
            # Try to load default configuration, fallback to fresh config if not found
            config = load_config("default")
            if not config:
                config = ExtendReviewerConfig()  # Use fresh default configuration
        
        # Process the file using existing core logic
        processor = FileProcessor()
        source_files_map = processor.process_zip_file(temp_file_path)
        
        if not source_files_map:
            raise HTTPException(status_code=400, detail="No source files found to analyze")
        
        # Parse files into models
        pmd_parser = ModelParser()
        context = pmd_parser.parse_files(source_files_map)
        
        # Run rules analysis
        rules_engine = RulesEngine(config)
        findings = rules_engine.run(context)
        
        # Format results
        format_type = OutputFormat(output_format.lower())
        formatter = OutputFormatter(format_type)
        total_files = len(context.pmds) + len(context.scripts) + (1 if context.amd else 0)
        total_rules = len(rules_engine.rules)
        
        # Store results in cache
        analysis_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        analysis_cache[analysis_id] = {
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity,
                    "message": f.message,
                    "file_path": f.file_path,
                    "line": f.line,
                    "column": f.column
                }
                for f in findings
            ],
            "total_files": total_files,
            "total_rules": total_rules,
            "zip_filename": file.filename,
            "config_used": config_name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Clean up temporary file
        temp_file_path.unlink(missing_ok=True)
        
        # Return results
        return analysis_cache[analysis_id]
        
    except Exception as e:
        # Clean up temporary file on error
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules")
async def list_rules():
    """List all available rules and their current status."""
    config = ExtendReviewerConfig()
    
    rules_info = []
    rule_configs = config.rules.model_dump()
    
    for rule_name, rule_config in rule_configs.items():
        field_info = config.rules.__class__.model_fields.get(rule_name)
        description = field_info.description if field_info else "No description available"
        
        rules_info.append({
            "name": rule_name,
            "enabled": rule_config["enabled"],
            "severity": rule_config.get("severity_override") or "default",
            "description": description
        })
    
    return {"rules": rules_info}


@app.post("/api/config")
async def save_configuration(
    name: str = Form(...),
    config_data: str = Form(...)
):
    """Save a configuration preset."""
    try:
        config_dict = json.loads(config_data)
        config = ExtendReviewerConfig(**config_dict)
        config_path = save_config(name, config)
        return {"message": f"Configuration '{name}' saved successfully", "path": config_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")


@app.get("/api/config/{name}")
async def get_configuration(name: str):
    """Get a saved configuration."""
    config = load_config(name)
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration '{name}' not found")
    
    return config.model_dump()


@app.get("/api/configs")
async def list_configurations():
    """List all saved configurations."""
    configs = []
    for config_file in CONFIG_DIR.glob("*.json"):
        config_name = config_file.stem
        config = load_config(config_name)
        if config:
            configs.append({
                "name": config_name,
                "rules_count": len([r for r in config.rules.model_dump().values() if r["enabled"]]),
                "created": config_file.stat().st_mtime
            })
    
    return {"configurations": configs}


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis results by ID."""
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_cache[analysis_id]


@app.post("/api/download/excel")
async def download_excel(request_data: dict):
    """Download analysis results as Excel file."""
    try:
        findings_data = request_data.get('findings', [])
        
        # Convert dict findings back to Finding objects
        findings = []
        for finding_dict in findings_data:
            # Create a mock rule object for the Finding
            class MockRule:
                def __init__(self, rule_id, severity, description):
                    self.__class__.__name__ = rule_id
                    self.SEVERITY = severity
                    self.DESCRIPTION = description
            
            mock_rule = MockRule(
                finding_dict.get('rule_id', 'Unknown'),
                finding_dict.get('severity', 'INFO'), 
                finding_dict.get('rule_description', 'No description')
            )
            
            finding = Finding(
                rule=mock_rule,
                message=finding_dict.get('message', ''),
                line=finding_dict.get('line', 0),
                column=finding_dict.get('column', 0),
                file_path=finding_dict.get('file_path', '')
            )
            findings.append(finding)
        
        # Create Excel file
        formatter = OutputFormatter(OutputFormat.EXCEL)
        excel_file_path = formatter.format_results(findings, len(set(f.file_path for f in findings)), 25)
        
        # Return the Excel file
        return FileResponse(
            path=excel_file_path,
                   filename=f"arcane-auditor-results-{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
