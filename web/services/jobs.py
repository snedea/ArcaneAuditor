"""
Job management service for Arcane Auditor.

Handles analysis job creation, execution, and cleanup.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Dict

# Global job management for async analysis
analysis_jobs: Dict[str, 'AnalysisJob'] = {}
job_lock = threading.Lock()


class AnalysisJob:
    """Represents an analysis job with status tracking."""
    def __init__(self, job_id: str, zip_path: Path = None, config: str = "default", config_source: str = "built-in"):
        self.job_id = job_id
        self.zip_path = zip_path
        self.config = config
        self.config_source = config_source  # Track if config is built-in, personal, or team
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


def cleanup_orphaned_files():
    """Clean up orphaned files from previous server runs."""
    uploads_dir = Path(__file__).parent.parent / "uploads"
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
    line_idx = line - 1
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
    """Build a file_path -> lines mapping from all models in a ProjectContext."""
    source_map = {}
    for pmd in context.pmds.values():
        if pmd.source_content and pmd.file_path:
            source_map[pmd.file_path] = pmd.source_content.split('\n')
    for pod in context.pods.values():
        if pod.source_content and pod.file_path:
            source_map[pod.file_path] = pod.source_content.split('\n')
    for script in context.scripts.values():
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
        project_root = Path(__file__).parent.parent.parent
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

        # Build source content map for snippet extraction
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
                    "snippet": extract_snippet(source_map, finding.file_path, finding.line),
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
            "config_name": job.config,
            "config_source": job.config_source
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

