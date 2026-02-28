#!/usr/bin/env python3
"""
FastAPI server for the HTML frontend of Arcane Auditor.
This serves the simple HTML/JavaScript interface with FastAPI backend.
"""

from contextlib import asynccontextmanager
import json
import os
import sys
import io
import difflib
import re as _re_module
import tempfile
import threading
import zipfile
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
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Anthropic SDK for direct API calls (temperature control)
import anthropic

# Configuration constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default limit
CHUNK_SIZE = 8192  # 8KB chunks for streaming

# Cache-busting version: changes every time the server process starts
_asset_version = str(int(time.time()))

# Global job management for async analysis
analysis_jobs: Dict[str, 'AnalysisJob'] = {}
job_lock = threading.Lock()

def get_dynamic_config_info():
    """Dynamically discover configuration information from all config directories."""
    config_info = {}
    
    # Search in priority order: personal, teams, presets
    config_dirs = [
        project_root / "config" / "personal",
        project_root / "config" / "teams", 
        project_root / "config" / "presets"
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
                        # Check if rule is explicitly enabled (defaults to True if not present)
                        is_enabled = rule_config.get('enabled', True)
                        if is_enabled:
                            enabled_rules += 1
                
                # Determine performance level based on rule count
                if enabled_rules <= 10:
                    performance = "Fast"
                elif enabled_rules <= 25:
                    performance = "Balanced"
                else:
                    performance = "Thorough"
                
                # Determine config type based on directory
                if config_dir.name == "personal":
                    config_type = "Personal"
                    description = f"Personal configuration with {enabled_rules} rules enabled"
                elif config_dir.name == "teams":
                    config_type = "Team"
                    description = f"Team configuration with {enabled_rules} rules enabled"
                elif config_dir.name == "presets":
                    config_type = "Built-in"
                    description = f"Built-in configuration with {enabled_rules} rules enabled"
                
                # Create unique key by combining config name with directory type
                # This allows showing all versions (personal, team, built-in) in the UI
                config_key = f"{config_name}_{config_dir.name}"
                config_info[config_key] = {
                    "name": config_name.replace('_', ' ').title(),
                    "description": description,
                    "rules_count": enabled_rules,
                    "performance": performance,
                    "type": config_type,
                    "path": str(config_file.relative_to(project_root)),
                    "id": config_name,  # Original name for API compatibility
                    "source": config_dir.name,  # Track which directory it came from
                    "rules": config_data.get('rules', {})  # Include actual rules data
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
    def __init__(self, job_id: str, zip_path: Path = None, config: str = "default"):
        self.job_id = job_id
        self.zip_path = zip_path
        self.config = config
        self.status = "queued"  # queued, running, completed, failed
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.thread = None
        self.is_zip = True  # True for ZIP files, False for individual files
        self.individual_files = []  # List of Path objects for individual files
    
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

class RevalidateRequest(BaseModel):
    """Request model for inline re-validation."""
    files: Dict[str, str]   # file_path -> modified content
    config: str              # config path used for original analysis

class AutofixRequest(BaseModel):
    """Request model for AI autofix of a single finding."""
    file_path: str       # e.g., "test.pmd"
    file_content: str    # full file content
    finding: dict        # {rule_id, message, line, severity}

class ExportZipRequest(BaseModel):
    """Request model for exporting fixed files as a ZIP archive."""
    files: Dict[str, str]  # file_path → fixed content

class ExplainRequest(BaseModel):
    """Request model for AI explanation."""
    findings: dict

# Mtime-cached prompt loader: re-reads file only when it changes on disk
_explain_prompt_cache = {"mtime": 0.0, "content": ""}
EXPLAIN_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "explain_system.md"

_autofix_prompt_cache = {"mtime": 0.0, "content": ""}
AUTOFIX_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "autofix_system.md"

def get_explain_system_prompt() -> str:
    """Load system prompt from file, re-reading only when mtime changes."""
    try:
        current_mtime = EXPLAIN_PROMPT_PATH.stat().st_mtime
        if current_mtime != _explain_prompt_cache["mtime"]:
            _explain_prompt_cache["content"] = EXPLAIN_PROMPT_PATH.read_text(encoding="utf-8").strip()
            _explain_prompt_cache["mtime"] = current_mtime
            print(f"Reloaded explain prompt from {EXPLAIN_PROMPT_PATH}")
        return _explain_prompt_cache["content"]
    except FileNotFoundError:
        print(f"Warning: {EXPLAIN_PROMPT_PATH} not found, using fallback prompt", file=sys.stderr)
        return (
            "You are a code reviewer. Return ONLY a JSON array. "
            "Each object must have: index (int), explanation (str), suggestion (str), priority (high/medium/low)."
        )


def get_autofix_system_prompt() -> str:
    """Load autofix system prompt from file, re-reading only when mtime changes."""
    try:
        current_mtime = AUTOFIX_PROMPT_PATH.stat().st_mtime
        if current_mtime != _autofix_prompt_cache["mtime"]:
            _autofix_prompt_cache["content"] = AUTOFIX_PROMPT_PATH.read_text(encoding="utf-8").strip()
            _autofix_prompt_cache["mtime"] = current_mtime
            print(f"Reloaded autofix prompt from {AUTOFIX_PROMPT_PATH}")
        return _autofix_prompt_cache["content"]
    except FileNotFoundError:
        print(f"Warning: {AUTOFIX_PROMPT_PATH} not found, using fallback prompt", file=sys.stderr)
        return (
            "You are a code fixer. Return ONLY the complete corrected file content. "
            "Fix ONLY the specific finding described. No preamble, no code fences, no explanation."
        )


def compute_diff_warning(original: str, fixed: str) -> Optional[dict]:
    """Compare original and fixed file content; return a warning if suspicious lines were removed.

    A "suspicious removal" is a non-trivial line that was deleted without being
    modified or moved (i.e. no sufficiently-similar added line exists).
    """
    orig_lines = original.splitlines()
    fixed_lines = fixed.splitlines()

    diff = list(difflib.unified_diff(orig_lines, fixed_lines, lineterm=""))

    removed = []
    added = []
    for line in diff:
        if line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])

    # Filter out non-suspicious removals.
    # Each added line can only pair with one removed line (consumed on match)
    # to prevent a single added line from hiding multiple unrelated removals.
    available_added = list(range(len(added)))  # indices of unconsumed added lines
    suspicious = []
    for r in removed:
        stripped = r.strip()
        # Blank / whitespace-only
        if not stripped:
            continue
        # Comment-only lines (C/JS, Python/shell, SQL/Lua, XML/HTML)
        if (stripped.startswith("//") or stripped.startswith("/*")
                or stripped.startswith("*") or stripped == "*/"
                or stripped.startswith("#")
                or stripped.startswith("--")
                or stripped.startswith("<!--") or stripped == "-->"):
            continue
        # Very short lines (closing braces, parens)
        if len(stripped) < 4:
            continue
        # Check if any unconsumed added line is similar enough (modified/moved)
        best_idx = -1
        best_ratio = 0.0
        for ai in available_added:
            ratio = difflib.SequenceMatcher(None, stripped, added[ai].strip()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = ai
        if best_ratio > 0.4 and best_idx >= 0:
            available_added.remove(best_idx)  # consume the match
        else:
            suspicious.append(r)

    if not suspicious:
        return None

    return {
        "removed_line_count": len(suspicious),
        "removed_lines": suspicious[:10],
        "total_lines_original": len(orig_lines),
        "total_lines_fixed": len(fixed_lines),
    }


# Shared Anthropic API helper
_anthropic_client: Optional[anthropic.Anthropic] = None

def _get_anthropic_client() -> anthropic.Anthropic:
    """Get or create a shared Anthropic client.  Reads ANTHROPIC_API_KEY from env."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _anthropic_client


async def _call_claude(
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    temperature: float = 1.0,
    max_tokens: int = 16384,
) -> str:
    """Call the Anthropic API with the given prompts.  Returns the text response."""
    if model is None:
        model = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")
    client = _get_anthropic_client()
    response = await asyncio.to_thread(
        client.messages.create,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


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

# Rate limiting (in-memory, per-IP)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
_cors_origins = os.environ.get(
    "CORS_ORIGINS", "https://arcane.llam.ai"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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
            # Clean up any remaining temporary files
            if job.is_zip and job.zip_path and job.zip_path.exists():
                job.zip_path.unlink()
                print(f"Cleaned up remaining ZIP file: {job.zip_path.name}")
            elif not job.is_zip and job.individual_files:
                for file_path in job.individual_files:
                    if file_path.exists():
                        file_path.unlink()
                        print(f"Cleaned up remaining file: {file_path.name}")

def extract_snippet(source_map: dict, file_path: str, line: int, context_lines: int | None = None) -> dict | None:
    """Extract source lines around a finding's line number.

    Args:
        source_map: Dict mapping file_path -> list of source lines
        file_path: Path of the file the finding is in
        line: 1-based line number of the finding
        context_lines: Number of lines above/below, or None for the full file
    Returns:
        Dict with 'lines' and 'start_line', or None if snippet cannot be extracted.
    """
    lines = source_map.get(file_path)
    if not lines or line < 1:
        return None
    line_idx = line - 1  # Convert to 0-based
    if context_lines is None:
        start = 0
        end = len(lines)
    else:
        start = max(0, line_idx - context_lines)
        end = min(len(lines), line_idx + context_lines + 1)
    snippet_lines = []
    for i in range(start, end):
        snippet_lines.append({
            "number": i + 1,
            "text": lines[i],
            "highlight": (i == line_idx)
        })
    if not snippet_lines:
        return None
    return {"lines": snippet_lines, "start_line": start + 1}


def build_source_map(context) -> dict:
    """Build a file_path -> lines mapping from all models in a ProjectContext.

    This captures source content before context is discarded, enabling
    snippet extraction for findings.
    """
    source_map = {}
    for pmd in context.pmds.values():
        if pmd.source_content and pmd.file_path:
            source_map[pmd.file_path] = pmd.source_content.split('\n')
    for pod in context.pods.values():
        if pod.source_content and pod.file_path:
            source_map[pod.file_path] = pod.source_content.split('\n')
    for script in context.scripts.values():
        # ScriptModel stores content in .source, not .source_content
        content = getattr(script, 'source_content', None) or getattr(script, 'source', None)
        if content and script.file_path:
            source_map[script.file_path] = content.split('\n')
    if context.amd and hasattr(context.amd, 'source_content') and context.amd.source_content:
        source_map[context.amd.file_path] = context.amd.source_content.split('\n')
    if context.smd and hasattr(context.smd, 'source_content') and context.smd.source_content:
        source_map[context.smd.file_path] = context.smd.source_content.split('\n')
    return source_map


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
            
        # Process files based on job type
        file_processing_start = time.time()
        processor = FileProcessor()
        
        if job.is_zip:
            # ZIP file mode
            source_files_map = processor.process_zip_file(job.zip_path)
            
            # Delete ZIP file immediately after successful processing
            if job.zip_path and job.zip_path.exists():
                job.zip_path.unlink()
                print(f"Deleted processed ZIP file: {job.zip_path.name}")
        else:
            # Individual files mode
            source_files_map = processor.process_individual_files(job.individual_files)
            
            # Delete individual files immediately after successful processing
            for file_path in job.individual_files:
                if file_path.exists():
                    file_path.unlink()
                    print(f"Deleted processed file: {file_path.name}")
        
        file_processing_time = time.time() - file_processing_start
        
        if not source_files_map:
            job.error = "No valid source files found"
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
        # Use project root as base path for configuration loading
        project_root = Path(__file__).parent.parent
        config_manager = ConfigurationManager(project_root)
        config = config_manager.load_config(job.config)
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

        # Build source content map from context models for snippet extraction
        source_map = build_source_map(context)

        # Convert findings to serializable format
        result = {
            "findings": [
                {
                    "rule_id": finding.rule_id,
                    "rule_description": finding.rule_description,
                    "severity": finding.severity,
                    "message": finding.message,
                    "file_path": finding.file_path,
                    "line": finding.line,
                    "snippet": extract_snippet(source_map, finding.file_path, finding.line)
                    }
                    for finding in findings
            ],
            "summary": {
                "total_findings": len(findings),
                "rules_executed": len(rules_engine.rules),
                "by_severity": {
                    "action": len([f for f in findings if f.severity == "ACTION"]),
                    "advice": len([f for f in findings if f.severity == "ADVICE"])
                }
            },
            "config_name": job.config  # Add config name to result
        }
        
        # Add context awareness information if available
        if context.analysis_context:
            result["context"] = context.analysis_context.to_dict()
        
        job.result = result
        job.status = "completed"
        job.end_time = time.time()
        
    except Exception as e:
        job.error = str(e)
        job.status = "failed"
        job.end_time = time.time()
        print(f"Analysis failed: {e}", file=sys.stderr)


@app.post("/api/upload")
@limiter.limit("5/minute")
async def upload_file(
    request: Request,
    files: list[UploadFile] = File(...),
    config: str = Form("default")
):
    """
    Upload file(s) for analysis.
    
    Supports:
    - Single ZIP file: Complete application archive
    - Multiple individual files: .pmd, .pod, .amd, .smd, .script files
    """
    
    # Validate we have files
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Determine if this is a ZIP upload or individual files
    is_zip_upload = len(files) == 1 and files[0].filename.lower().endswith('.zip')
    
    # Validate configuration
    config_info = get_dynamic_config_info()
    if config not in config_info:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {config}")
    
    # Get the actual config path from the selected config key
    selected_config_info = config_info[config]
    actual_config_path = selected_config_info["path"]
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file(s)
    uploads_dir = Path(__file__).parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    try:
        if is_zip_upload:
            # ZIP file mode
            file = files[0]
            
            # Validate file size
            if file.size and file.size > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
            
            zip_path = uploads_dir / f"{job_id}.zip"
            
            # Stream file to disk
            with open(zip_path, "wb") as buffer:
                while chunk := await file.read(CHUNK_SIZE):
                    buffer.write(chunk)
            
            # Create analysis job for ZIP
            job = AnalysisJob(job_id, zip_path, actual_config_path)
            job.is_zip = True
        
        else:
            # Individual files mode
            saved_files = []
            
            for file in files:
                # Validate file extension
                valid_extensions = ['.pmd', '.pod', '.amd', '.smd', '.script']
                if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
                    raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Only {', '.join(valid_extensions)} files are allowed.")
                
                # Validate file size
                if file.size and file.size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail=f"File {file.filename} too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
                
                # Save file
                file_path = uploads_dir / f"{job_id}_{file.filename}"
                with open(file_path, "wb") as buffer:
                    while chunk := await file.read(CHUNK_SIZE):
                        buffer.write(chunk)
                
                saved_files.append(file_path)
            
            # Create analysis job for individual files
            job = AnalysisJob(job_id, None, actual_config_path)
            job.is_zip = False
            job.individual_files = saved_files
        
        with job_lock:
            analysis_jobs[job_id] = job
        
        # Start background analysis
        job.thread = threading.Thread(target=run_analysis_background, args=(job,))
        job.thread.daemon = True
        job.thread.start()
        
        # Cleanup old jobs
        cleanup_old_jobs()
        
        return {"job_id": job_id, "status": "queued", "config": actual_config_path}
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up files if upload failed
        if is_zip_upload and 'zip_path' in locals() and zip_path.exists():
            zip_path.unlink()
        elif 'saved_files' in locals():
            for file_path in saved_files:
                if file_path.exists():
                    file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

def get_rule_default_severities():
    """Get default severities for all rules by loading them from rule classes."""
    from parser.rules_engine import RulesEngine
    from parser.config import ArcaneAuditorConfig
    
    # Create a default config to discover all rules
    config = ArcaneAuditorConfig()
    engine = RulesEngine(config)
    
    # Build a map of rule name -> default severity
    severities = {}
    for rule in engine.rules:
        rule_name = rule.__class__.__name__
        severities[rule_name] = rule.SEVERITY
    
    return severities

@app.get("/api/configs")
async def get_available_configs(response: Response):
    """Get list of available configurations with resolved severities."""
    # Add cache-busting headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Get default severities from rule classes
    default_severities = get_rule_default_severities()
    
    config_info = get_dynamic_config_info()
    available_configs = []
    
    for config_name, info in config_info.items():
        config_data = info.copy()
        config_data["id"] = config_name
        
        # Resolve null severity_override values to actual rule defaults
        if "rules" in config_data:
            for rule_name, rule_config in config_data["rules"].items():
                if isinstance(rule_config, dict):
                    # If severity_override is null, resolve to rule's default
                    if rule_config.get("severity_override") is None:
                        if rule_name in default_severities:
                            rule_config["severity_override"] = default_severities[rule_name]
        
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
            # Use shared OutputFormatter logic for Excel generation
            from output.formatter import OutputFormatter, OutputFormat
            from datetime import datetime
            import tempfile
            from pathlib import Path
            
            # Convert web service findings to CLI format for compatibility
            findings = []
            for finding_data in job.result["findings"]:
                # Create a simple Finding-like object for compatibility
                class WebFinding:
                    def __init__(self, data):
                        self.rule_id = data["rule_id"]
                        self.severity = data["severity"]
                        self.line = data["line"]
                        self.message = data["message"]
                        self.file_path = data["file_path"]
                
                findings.append(WebFinding(finding_data))
            
            # Create a mock ProjectContext with context information if available
            class MockProjectContext:
                def __init__(self, context_data):
                    self.analysis_context = None
                    if context_data:
                        # Recreate AnalysisContext from stored data
                        from file_processing.context_tracker import AnalysisContext
                        self.analysis_context = AnalysisContext(
                            analysis_type=context_data.get("analysis_type", "unknown"),
                            files_analyzed=context_data.get("files_analyzed", []),
                            files_present=set(context_data.get("files_present", []))
                        )
            
            # Use OutputFormatter to generate Excel with context tab
            formatter = OutputFormatter(OutputFormat.EXCEL)
            total_files = len(set(finding.file_path for finding in findings if finding.file_path))
            total_rules = job.result["summary"]["rules_executed"]
            context = MockProjectContext(job.result.get("context"))
            
            excel_file_path = formatter.format_results(findings, total_files, total_rules, context)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"arcane-auditor-results-{timestamp}.xlsx"
            
            return FileResponse(
                path=excel_file_path,
                filename=filename,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

def parse_structured_explanation(raw_text: str) -> list | None:
    """Try to extract a JSON array from LLM output.

    Handles:
    - Raw JSON array
    - JSON wrapped in ```json ... ``` code fences
    - JSON preceded by preamble text

    Returns the parsed list on success, or None if parsing fails.
    """
    text = raw_text.strip()
    if not text:
        return None

    # Strip code fences if present
    if "```" in text:
        import re
        fence_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()

    # Find the outermost [...] bracket pair
    start = text.find("[")
    if start == -1:
        return None
    # Find matching closing bracket from the end
    end = text.rfind("]")
    if end == -1 or end <= start:
        return None

    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, list):
            return None
        # Validate each item has the required fields with correct types
        required = {"index", "explanation", "suggestion", "priority"}
        valid_priorities = {"high", "medium", "low"}
        validated = []
        for item in parsed:
            if not isinstance(item, dict) or not required.issubset(item.keys()):
                return None
            if not isinstance(item["index"], int):
                return None
            if not isinstance(item["explanation"], str):
                return None
            if not isinstance(item["suggestion"], str):
                return None
            if item["priority"] not in valid_priorities:
                return None
            validated.append(item)
        return validated
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _build_numbered_user_message(findings_data: dict) -> tuple[str, list]:
    """Build a numbered user message and return (message, findings_list).

    The findings_list preserves the original order so we can map
    structured responses back by index.
    """
    findings_list = findings_data.get("findings", [])
    summary = findings_data.get("summary", {})

    lines = [
        "Here are the Arcane Auditor findings for a Workday Extend application.",
        f"Summary: {json.dumps(summary)}",
        "",
    ]
    for i, f in enumerate(findings_list):
        lines.append(
            f"Finding #{i}: rule_id={f.get('rule_id','')}, "
            f"file_path={f.get('file_path','')}, "
            f"line={f.get('line','')}, "
            f"severity={f.get('severity','')}, "
            f"message={f.get('message','')}"
        )

    return "\n".join(lines), findings_list


@app.post("/api/explain")
@limiter.limit("10/minute")
async def explain_findings(request: Request, body: ExplainRequest):
    """Send analysis findings to Claude for AI-powered explanation."""
    findings = body.findings

    if not findings:
        raise HTTPException(status_code=400, detail="No findings provided")

    user_msg, findings_list = _build_numbered_user_message(findings)

    try:
        explanation = await _call_claude(
            system_prompt=get_explain_system_prompt(),
            user_message=user_msg,
            temperature=1.0,
        )

        if not explanation:
            raise HTTPException(status_code=502, detail="AI returned empty response")

        # Try structured JSON parsing first
        structured = parse_structured_explanation(explanation)
        if structured is not None:
            return {
                "explanations": structured,
                "format": "structured",
                "findings_order": [
                    {
                        "rule_id": f.get("rule_id", ""),
                        "file_path": f.get("file_path", ""),
                        "line": f.get("line", 0),
                    }
                    for f in findings_list
                ],
            }

        # Fallback: return raw markdown
        return {"explanation": explanation, "format": "markdown"}

    except anthropic.APITimeoutError:
        raise HTTPException(status_code=504, detail="AI explanation timed out")
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=503, detail="Anthropic API key not configured or invalid")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Explain endpoint error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"AI explanation failed: {str(e)}")


@app.post("/api/revalidate")
async def revalidate(request: RevalidateRequest):
    """Re-validate edited file contents against the rules engine.

    Accepts file contents directly (no file upload) and returns fresh findings.
    Used by the inline editor to show real-time fix progress.
    """
    from file_processing.models import SourceFile
    from parser.app_parser import ModelParser
    from parser.rules_engine import RulesEngine
    from parser.config_manager import ConfigurationManager

    if not request.files:
        return {"findings": [], "summary": {"total_findings": 0, "rules_executed": 0, "by_severity": {"action": 0, "advice": 0}}, "errors": []}

    errors = []
    source_files_map: Dict[str, SourceFile] = {}

    for file_path, content in request.files.items():
        try:
            source_files_map[file_path] = SourceFile(
                path=Path(file_path),
                content=content,
                size=len(content.encode("utf-8")),
            )
        except Exception as e:
            errors.append({"file_path": file_path, "error": str(e)})

    if not source_files_map:
        return {"findings": [], "summary": {"total_findings": 0, "rules_executed": 0, "by_severity": {"action": 0, "advice": 0}}, "errors": errors}

    try:
        parser = ModelParser()
        context = parser.parse_files(source_files_map)

        config_manager = ConfigurationManager(project_root)
        config = config_manager.load_config(request.config)
        rules_engine = RulesEngine(config)
        findings = rules_engine.run(context)

        source_map = build_source_map(context)

        # Propagate per-file parsing errors from ModelParser
        for err_str in context.parsing_errors:
            # Format is "file_path: error_message"
            parts = err_str.split(": ", 1)
            if len(parts) == 2:
                errors.append({"file_path": parts[0], "error": parts[1]})
            else:
                errors.append({"file_path": "_parse", "error": err_str})

        result = {
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "rule_description": f.rule_description,
                    "severity": f.severity,
                    "message": f.message,
                    "file_path": f.file_path,
                    "line": f.line,
                    "snippet": extract_snippet(source_map, f.file_path, f.line),
                }
                for f in findings
            ],
            "summary": {
                "total_findings": len(findings),
                "rules_executed": len(rules_engine.rules),
                "by_severity": {
                    "action": len([f for f in findings if f.severity == "ACTION"]),
                    "advice": len([f for f in findings if f.severity == "ADVICE"]),
                },
            },
            "errors": errors,
        }
        return result

    except Exception as e:
        return {
            "findings": [],
            "summary": {"total_findings": 0, "rules_executed": 0, "by_severity": {"action": 0, "advice": 0}},
            "errors": errors + [{"file_path": "_global", "error": str(e)}],
        }


def strip_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output if present."""
    import re
    stripped = text.strip()
    fence_match = re.match(r"^```(?:\w*)\s*\n([\s\S]*?)```\s*$", stripped)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped


@app.post("/api/autofix")
@limiter.limit("10/minute")
async def autofix_finding(request: Request, body: AutofixRequest):
    """Use Anthropic API to auto-fix a single finding in a file.

    Accepts the full file content and a finding description, returns the
    corrected file content.  Temperature is set to 0 for maximum fidelity.
    """
    if not body.file_content.strip():
        raise HTTPException(status_code=400, detail="Empty file content")

    if not body.finding:
        raise HTTPException(status_code=400, detail="No finding provided")

    # Build user message with file path, finding details, and full content
    finding = body.finding
    user_msg = (
        f"File: {body.file_path}\n\n"
        f"Finding to fix:\n"
        f"  Rule: {finding.get('rule_id', '')}\n"
        f"  Severity: {finding.get('severity', '')}\n"
        f"  Line: {finding.get('line', '')}\n"
        f"  Message: {finding.get('message', '')}\n\n"
        f"Full file content:\n{body.file_content}"
    )

    try:
        fixed_content = await _call_claude(
            system_prompt=get_autofix_system_prompt(),
            user_message=user_msg,
            temperature=0,
        )

        if not fixed_content:
            raise HTTPException(status_code=502, detail="AI returned empty response")

        # Strip code fences if LLM wrapped the output
        fixed_content = strip_code_fences(fixed_content)

        diff_warning = compute_diff_warning(body.file_content, fixed_content)
        return {"fixed_content": fixed_content, "file_path": body.file_path, "diff_warning": diff_warning}

    except anthropic.APITimeoutError:
        raise HTTPException(status_code=504, detail="Autofix timed out")
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=503, detail="Anthropic API key not configured or invalid")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Autofix endpoint error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Autofix failed: {str(e)}")


@app.post("/api/export-zip")
async def export_zip(request: ExportZipRequest):
    """Bundle fixed files into a ZIP archive and return it for download.

    Strips UUID job-ID prefixes from filenames so the exported files have
    their original names (e.g. ``dirtyPage.pmd`` instead of
    ``abcd1234_dirtyPage.pmd``).
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for raw_path, content in request.files.items():
            # Strip UUID prefix from the filename
            basename = raw_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            clean_name = _re_module.sub(r"^[a-f0-9-]+_", "", basename)
            zf.writestr(clean_name, content)

    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=fixed_files.zip"},
    )


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page with cache-busted asset references."""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index file not found")

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Inject a cache-buster query param on /static/ asset URLs.
    # Handles both quote styles and avoids double-appending if ?v= already present.
    import re
    def _bust(m):
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        if '?' in path:
            return m.group(0)  # already has query string, skip
        return f'{attr}={quote}/static/{path}?v={_asset_version}{quote}'
    content = re.sub(
        r"""(src|href)=(["'])/static/([^"']+)\2""",
        _bust,
        content,
    )
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
