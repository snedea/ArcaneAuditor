#!/usr/bin/env python3
"""
FastAPI server for the HTML frontend of Arcane Auditor.
This serves the simple HTML/JavaScript interface with FastAPI backend.
"""

from contextlib import asynccontextmanager
import sys
import tempfile
import threading
import time
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Optional
import webbrowser

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# FastAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configuration constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default limit
CHUNK_SIZE = 8192  # 8KB chunks for streaming

# Global job management for async analysis
analysis_jobs: Dict[str, 'AnalysisJob'] = {}
job_lock = threading.Lock()

def get_dynamic_config_info():
    """Dynamically discover configuration information from all config directories."""
    config_info = {}
    
    # Search in priority order: local_configs, user_configs, configs
    config_dirs = [
        project_root / "local_configs",
        project_root / "user_configs", 
        project_root / "configs"
    ]
    
    for config_dir in config_dirs:
        if not config_dir.exists():
            continue
            
        # Search for JSON files in the directory (not subdirectories)
        for config_file in config_dir.glob("*.json"):
            config_name = config_file.stem
        
            try:
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Count enabled rules
                enabled_rules = 0
                if 'rules' in config_data:
                    for rule_name, rule_config in config_data['rules'].items():
                        if rule_config.get('enabled', True):
                            enabled_rules += 1
                
                # Determine performance level based on rule count
                if enabled_rules <= 10:
                    performance = "Fast"
                elif enabled_rules <= 25:
                    performance = "Balanced"
                else:
                    performance = "Thorough"
                
                # Determine config type based on directory
                if config_dir.name == "local_configs":
                    config_type = "Personal"
                    description = f"Personal configuration with {enabled_rules} rules enabled"
                elif config_dir.name == "user_configs":
                    config_type = "Team"
                    description = f"Team configuration with {enabled_rules} rules enabled"
                else:
                    config_type = "Built-in"
                    description = f"Built-in configuration with {enabled_rules} rules enabled"
                
                config_info[config_name] = {
                    "name": config_name.replace('_', ' ').title(),
                    "description": description,
                    "rules_count": enabled_rules,
                    "performance": performance,
                    "type": config_type,
                    "path": str(config_file.relative_to(project_root))
                }
                
            except Exception as e:
                print(f"Warning: Failed to load config {config_name}: {e}")
    
    return config_info

def cleanup_orphaned_files():
    """Clean up orphaned files from previous server runs."""
    uploads_dir = Path(__file__).parent / "uploads"
    if uploads_dir.exists():
        current_time = time.time()
        files_found = 0
        files_deleted = 0
        
        for file_path in uploads_dir.glob("*.zip"):
            files_found += 1
            file_age = current_time - file_path.stat().st_mtime
            # Delete files older than 1 hour
            if file_age > 3600:
                try:
                    file_path.unlink()
                    files_deleted += 1
                    print(f"Cleaned up orphaned file: {file_path.name} (age: {file_age/60:.1f} minutes)")
                except Exception as e:
                    print(f"Failed to clean up {file_path.name}: {e}")
            else:
                print(f"Keeping file: {file_path.name} (age: {file_age/60:.1f} minutes)")
        
        print(f"Cleanup summary: {files_found} files found, {files_deleted} files deleted")


class AnalysisJob:
    """Represents an analysis job with status tracking."""
    def __init__(self, job_id: str, zip_path: Path, config: str = "default"):
        self.job_id = job_id
        self.zip_path = zip_path
        self.config = config
        self.status = "queued"  # queued, running, completed, failed
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.thread = None
    
    def to_dict(self):
        """Convert job to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "config": self.config
        }

class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    config: Optional[str] = None

class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    job_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Clean up orphaned files on server startup."""
    cleanup_orphaned_files()
    
    # Start periodic cleanup task
    import asyncio
    asyncio.create_task(periodic_cleanup())
    yield

# Initialize FastAPI app
app = FastAPI(
    title="Arcane Auditor API",
    description="Workday Extend Code Review Tool API",
    version="0.4.0",
    lifespan=lifespan
)

async def periodic_cleanup():
    """Run cleanup every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        cleanup_orphaned_files()
        cleanup_old_jobs()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def cleanup_old_jobs():
    """Remove completed/failed jobs older than 1 hour."""
    current_time = time.time()
    with job_lock:
        jobs_to_remove = []
        for job_id, job in analysis_jobs.items():
            if job.status in ["completed", "failed"] and job.end_time:
                if current_time - job.end_time > 3600:  # 1 hour
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            job = analysis_jobs.pop(job_id)
            # Clean up temporary files
            if job.zip_path.exists():
                job.zip_path.unlink()

def run_analysis_background(job: AnalysisJob):
    """Run analysis in background thread."""
    try:
        job.status = "running"
        job.start_time = time.time()
        
        # Import analysis modules here to avoid import issues
        from file_processing.processor import FileProcessor
        from parser.app_parser import ModelParser
        from parser.rules_engine import RulesEngine
        from parser.config_manager import ConfigurationManager
        
        # Process ZIP file
        file_processing_start = time.time()
        processor = FileProcessor()
        source_files_map = processor.process_zip_file(job.zip_path)
        file_processing_time = time.time() - file_processing_start
        
        if not source_files_map:
            job.error = "No PMD Script files found in the uploaded ZIP"
            job.status = "failed"
            job.end_time = time.time()
            return
            
        # Create project context
        parsing_start = time.time()
        parser = ModelParser()
        context = parser.parse_files(source_files_map)
        parsing_time = time.time() - parsing_start
        
        # Run analysis with specified configuration
        config_start = time.time()
        config_manager = ConfigurationManager()
        print(f"DEBUG: Loading configuration '{job.config}' for job {job.job_id}")
        config = config_manager.load_config(job.config)
        print(f"DEBUG: Loaded config with {len(config.rules)} total rules")
        enabled_rules = sum(1 for rule in config.rules.values() if rule.enabled)
        print(f"DEBUG: {enabled_rules} rules are enabled")
        rules_engine = RulesEngine(config)
        config_time = time.time() - config_start
        
        analysis_start = time.time()
        findings = rules_engine.run(context)
        analysis_time = time.time() - analysis_start
        
        # Log performance metrics
        total_time = time.time() - job.start_time
        print(f"Performance metrics for job {job.job_id}:")
        print(f"  File processing: {file_processing_time:.2f}s")
        print(f"  Parsing: {parsing_time:.2f}s")
        print(f"  Config loading: {config_time:.2f}s")
        print(f"  Analysis: {analysis_time:.2f}s")
        print(f"  Total: {total_time:.2f}s")
            
        # Convert findings to serializable format
        result = {
            "findings": [
                {
                    "rule_id": finding.rule_id,
                    "severity": finding.severity,
                    "message": finding.message,
                    "file_path": finding.file_path,
                    "line": finding.line,
                    "column": finding.column
                    }
                    for finding in findings
            ],
            "summary": {
                "total_findings": len(findings),
                "rules_executed": len(rules_engine.rules),
                "by_severity": {
                    "error": len([f for f in findings if f.severity == "SEVERE"]),
                    "warning": len([f for f in findings if f.severity == "WARNING"]),
                    "info": len([f for f in findings if f.severity == "INFO"])
                }
            }
        }
        
        job.result = result
        job.status = "completed"
        job.end_time = time.time()
        
    except Exception as e:
        job.error = str(e)
        job.status = "failed"
        job.end_time = time.time()
        print(f"Analysis failed: {e}", file=sys.stderr)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), config: str = "default"):
    """Upload a ZIP file for analysis."""
    print(f"DEBUG: Received upload request with config='{config}'")
    
    # Validate file type
    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Validate configuration
    config_info = get_dynamic_config_info()
    if config not in config_info:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {config}")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    uploads_dir = Path(__file__).parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    zip_path = uploads_dir / f"{job_id}.zip"
    
    try:
        # Stream file to disk
        with open(zip_path, "wb") as buffer:
            while chunk := await file.read(CHUNK_SIZE):
                buffer.write(chunk)
        
        # Create analysis job with configuration
        job = AnalysisJob(job_id, zip_path, config)
        print(f"DEBUG: Created job {job_id} with config='{config}'")
        
        with job_lock:
            analysis_jobs[job_id] = job
        
        # Start background analysis
        job.thread = threading.Thread(target=run_analysis_background, args=(job,))
        job.thread.daemon = True
        job.thread.start()
        
        # Cleanup old jobs
        cleanup_old_jobs()
        
        return {"job_id": job_id, "status": "queued", "config": config}
            
    except Exception as e:
        # Clean up file if upload failed
        if zip_path.exists():
            zip_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/configs")
async def get_available_configs():
    """Get list of available configurations."""
    config_info = get_dynamic_config_info()
    available_configs = []
    
    for config_name, info in config_info.items():
        config_data = info.copy()
        config_data["id"] = config_name
        available_configs.append(config_data)
    
    return {"configs": available_configs}

@app.get("/api/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of an analysis job."""
    with job_lock:
        if job_id not in analysis_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = analysis_jobs[job_id]
        return JobStatusResponse(**job.to_dict())

@app.get("/api/download/{job_id}")
async def download_excel(job_id: str):
    """Download analysis results as Excel file."""
    with job_lock:
        if job_id not in analysis_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = analysis_jobs[job_id]
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed")
        
        if not job.result:
            raise HTTPException(status_code=500, detail="No results available")
        
        try:
            # Generate Excel file using the superior CLI method
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
            from datetime import datetime
            from pathlib import Path
            
            wb = Workbook()
            
            # Remove default sheet
            wb.remove(wb.active)
            
            # Convert web service findings to CLI format
            findings = []
            for finding_data in job.result["findings"]:
                # Create a simple Finding-like object for compatibility
                class WebFinding:
                    def __init__(self, data):
                        self.rule_id = data["rule_id"]
                        self.severity = data["severity"]
                        self.line = data["line"]
                        self.column = data.get("column", 1)
                        self.message = data["message"]
                        self.file_path = data["file_path"]
                
                findings.append(WebFinding(finding_data))
            
            # Group findings by file
            findings_by_file = {}
            for finding in findings:
                file_path = finding.file_path or "Unknown"
                if file_path not in findings_by_file:
                    findings_by_file[file_path] = []
                findings_by_file[file_path].append(finding)
            
            # Create summary sheet
            summary_sheet = wb.create_sheet("Summary")
            summary_sheet.append(["Analysis Summary"])
            summary_sheet.append(["Files Analyzed", len(findings_by_file)])
            summary_sheet.append(["Rules Executed", job.result["summary"]["rules_executed"]])
            summary_sheet.append(["Total Issues", len(findings)])
            summary_sheet.append(["Severe", len([f for f in findings if f.severity == "SEVERE"])])
            summary_sheet.append(["Warnings", len([f for f in findings if f.severity == "WARNING"])])
            summary_sheet.append(["Info", len([f for f in findings if f.severity == "INFO"])])
            summary_sheet.append([])
            summary_sheet.append(["File", "Issues", "Severe", "Warnings", "Info"])
            
            # Style summary sheet
            summary_sheet['A1'].font = Font(bold=True, size=14)
            for row in range(1, 8):
                summary_sheet[f'A{row}'].font = Font(bold=True)
            
            # Add file summary data
            for file_path, file_findings in findings_by_file.items():
                severe_count = len([f for f in file_findings if f.severity == "SEVERE"])
                warning_count = len([f for f in file_findings if f.severity == "WARNING"])
                info_count = len([f for f in file_findings if f.severity == "INFO"])
                summary_sheet.append([file_path, len(file_findings), severe_count, warning_count, info_count])
            
            # Create sheets for each file
            for file_path, file_findings in findings_by_file.items():
                # Clean sheet name (Excel has restrictions)
                sheet_name = Path(file_path).stem[:31]  # Excel sheet name limit
                sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).strip()
                if not sheet_name:
                    sheet_name = "Unknown"
                
                ws = wb.create_sheet(sheet_name)
                
                # Headers
                headers = ["Rule ID", "Severity", "Line", "Column", "Message", "File Path"]
                ws.append(headers)
                
                # Style headers
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True)
                for col_num, header in enumerate(headers, 1):
                    cell = ws.cell(row=1, column=col_num)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center")
                
                # Add findings
                for finding in file_findings:
                    row = [
                        finding.rule_id,
                        finding.severity,
                        finding.line,
                        finding.column,
                        finding.message,
                        finding.file_path
                    ]
                    ws.append(row)
                    
                    # Color code by severity
                    severity_colors = {
                        "SEVERE": "FFCCCC",    # Light red
                        "WARNING": "FFFFCC",  # Light yellow
                        "INFO": "CCE5FF",     # Light blue
                        "HINT": "E6FFE6"      # Light green
                    }
                    
                    if finding.severity in severity_colors:
                        fill = PatternFill(start_color=severity_colors[finding.severity], 
                                         end_color=severity_colors[finding.severity], 
                                         fill_type="solid")
                        for col_num in range(1, len(headers) + 1):
                            ws.cell(row=ws.max_row, column=col_num).fill = fill
                
                # Auto-adjust column widths
                for column in ws.columns:
                    max_length = 0
                    column_letter = get_column_letter(column[0].column)
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            wb.save(temp_file.name)
            temp_file.close()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"arcane-auditor-results-{timestamp}.xlsx"
            
            return FileResponse(
                path=temp_file.name,
                filename=filename,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page."""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index file not found")
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.3"}

# Mount static files at /static to avoid conflicts with API routes
static_dir = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

def main():
    """Main function to run the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Arcane Auditor FastAPI Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--open-browser", action="store_true", help="Open browser automatically")
    
    args = parser.parse_args()
    
    if args.open_browser:
        # Open browser after a short delay
        def open_browser():
            time.sleep(1)
            webbrowser.open(f"http://{args.host}:{args.port}")
        
        threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"Starting Arcane Auditor FastAPI server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
