#!/usr/bin/env python3
"""
FastAPI server for the HTML frontend of Arcane Auditor.
This serves the simple HTML/JavaScript interface with FastAPI backend.
"""

import os
import sys
import json
import tempfile
import threading
import time
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Optional, List
import webbrowser

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# FastAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
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

class AnalysisJob:
    """Represents an analysis job with status tracking."""
    def __init__(self, job_id: str, zip_path: Path):
        self.job_id = job_id
        self.zip_path = zip_path
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
            "end_time": self.end_time
        }

class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    job_id: str

# Initialize FastAPI app
app = FastAPI(
    title="Arcane Auditor API",
    description="Workday Extend Code Review Tool API",
    version="0.1.3"
)

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
        processor = FileProcessor()
        source_files_map = processor.process_zip_file(job.zip_path)
        
        if not source_files_map:
            job.error = "No PMD Script files found in the uploaded ZIP"
            job.status = "failed"
            job.end_time = time.time()
            return
        
        # Create project context
        parser = ModelParser()
        context = parser.parse_files(source_files_map)
        
        # Run analysis
        config_manager = ConfigurationManager()
        config = config_manager.load_config("comprehensive")
        rules_engine = RulesEngine(config)
        
        findings = rules_engine.run(context)
        
        # Convert findings to serializable format
        result = {
            "findings": [
                {
                    "rule": finding.rule_id,
                    "severity": finding.severity,
                    "message": finding.message,
                    "file": finding.file_path,
                    "line": finding.line,
                    "column": finding.column
                }
                for finding in findings
            ],
            "summary": {
                "total_findings": len(findings),
                "by_severity": {
                    "error": len([f for f in findings if f.severity == "error"]),
                    "warning": len([f for f in findings if f.severity == "warning"]),
                    "info": len([f for f in findings if f.severity == "info"])
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
async def upload_file(file: UploadFile = File(...)):
    """Upload a ZIP file for analysis."""
    # Validate file type
    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
    
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
        
        # Create analysis job
        job = AnalysisJob(job_id, zip_path)
        
        with job_lock:
            analysis_jobs[job_id] = job
        
        # Start background analysis
        job.thread = threading.Thread(target=run_analysis_background, args=(job,))
        job.thread.daemon = True
        job.thread.start()
        
        # Cleanup old jobs
        cleanup_old_jobs()
        
        return {"job_id": job_id, "status": "queued"}
        
    except Exception as e:
        # Clean up file if upload failed
        if zip_path.exists():
            zip_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

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
            # Generate Excel file
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from datetime import datetime
            
            wb = Workbook()
            
            # Summary sheet
            ws_summary = wb.active
            ws_summary.title = "Summary"
            
            # Add summary data
            summary = job.result["summary"]
            ws_summary["A1"] = "Total Findings"
            ws_summary["B1"] = summary["total_findings"]
            ws_summary["A2"] = "Errors"
            ws_summary["B2"] = summary["by_severity"]["error"]
            ws_summary["A3"] = "Warnings"
            ws_summary["B3"] = summary["by_severity"]["warning"]
            ws_summary["A4"] = "Info"
            ws_summary["B4"] = summary["by_severity"]["info"]
            
            # Style summary sheet
            header_font = Font(bold=True)
            for cell in ws_summary["A1:A4"]:
                cell[0].font = header_font
            
            # Findings sheet
            ws_findings = wb.create_sheet("Findings")
            
            # Headers
            headers = ["Rule", "Severity", "Message", "File", "Line"]
            for col, header in enumerate(headers, 1):
                cell = ws_findings.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            # Add findings data
            for row, finding in enumerate(job.result["findings"], 2):
                ws_findings.cell(row=row, column=1, value=finding["rule"])
                ws_findings.cell(row=row, column=2, value=finding["severity"])
                ws_findings.cell(row=row, column=3, value=finding["message"])
                ws_findings.cell(row=row, column=4, value=finding["file"])
                ws_findings.cell(row=row, column=5, value=finding["line"])
            
            # Auto-adjust column widths
            for column in ws_findings.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws_findings.column_dimensions[column_letter].width = adjusted_width
            
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
static_dir = Path(__file__).parent / "simple-frontend"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

def main():
    """Main function to run the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Arcane Auditor FastAPI Server")
    parser.add_argument("--port", type=int, default=8081, help="Port to run the server on")
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
