"""
AI-powered routes for Arcane Auditor.

Handles AI explain, autofix, revalidation, and export-zip endpoints.
"""

import io
import json
import os
import re as _re_module
import sys
import difflib
import zipfile
import asyncio
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Request, HTTPException, Response
from pydantic import BaseModel

import anthropic

from web.services.jobs import build_source_map, extract_snippet

# Project root for config loading
project_root = Path(__file__).parent.parent.parent

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

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
    files: Dict[str, str]  # file_path -> fixed content


class ExplainRequest(BaseModel):
    """Request model for AI explanation."""
    findings: dict


# ---------------------------------------------------------------------------
# Mtime-cached prompt loaders
# ---------------------------------------------------------------------------

_explain_prompt_cache = {"mtime": 0.0, "content": ""}
EXPLAIN_PROMPT_PATH = project_root / "prompts" / "explain_system.md"

_autofix_prompt_cache = {"mtime": 0.0, "content": ""}
AUTOFIX_PROMPT_PATH = project_root / "prompts" / "autofix_system.md"


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


# ---------------------------------------------------------------------------
# Diff warning computation
# ---------------------------------------------------------------------------

def compute_diff_warning(original: str, fixed: str) -> Optional[dict]:
    """Compare original and fixed file content; return a warning if suspicious lines were removed."""
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

    available_added = list(range(len(added)))
    suspicious = []
    for r in removed:
        stripped = r.strip()
        if not stripped:
            continue
        if (stripped.startswith("//") or stripped.startswith("/*")
                or stripped.startswith("*") or stripped == "*/"
                or stripped.startswith("#")
                or stripped.startswith("--")
                or stripped.startswith("<!--") or stripped == "-->"):
            continue
        if len(stripped) < 4:
            continue
        best_idx = -1
        best_ratio = 0.0
        for ai in available_added:
            ratio = difflib.SequenceMatcher(None, stripped, added[ai].strip()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = ai
        if best_ratio > 0.4 and best_idx >= 0:
            available_added.remove(best_idx)
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


# ---------------------------------------------------------------------------
# Anthropic API helpers
# ---------------------------------------------------------------------------

_anthropic_client: Optional[anthropic.Anthropic] = None


def _get_anthropic_client() -> anthropic.Anthropic:
    """Get or create a shared Anthropic client.  Reads ANTHROPIC_API_KEY from env."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic()
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


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output if present."""
    import re
    stripped = text.strip()
    fence_match = re.match(r"^```(?:\w*)\s*\n([\s\S]*?)```\s*$", stripped)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped


def parse_structured_explanation(raw_text: str) -> list | None:
    """Try to extract a JSON array from LLM output."""
    text = raw_text.strip()
    if not text:
        return None

    if "```" in text:
        import re
        fence_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()

    start = text.find("[")
    if start == -1:
        return None
    end = text.rfind("]")
    if end == -1 or end <= start:
        return None

    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, list):
            return None
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
    """Build a numbered user message and return (message, findings_list)."""
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/api/explain")
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


@router.post("/api/autofix")
async def autofix_finding(request: Request, body: AutofixRequest):
    """Use Anthropic API to auto-fix a single finding in a file."""
    if not body.file_content.strip():
        raise HTTPException(status_code=400, detail="Empty file content")

    if not body.finding:
        raise HTTPException(status_code=400, detail="No finding provided")

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


@router.post("/api/revalidate")
async def revalidate(request: RevalidateRequest):
    """Re-validate edited file contents against the rules engine."""
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

        for err_str in context.parsing_errors:
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


@router.post("/api/export-zip")
async def export_zip(request: ExportZipRequest):
    """Bundle fixed files into a ZIP archive and return it for download."""
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for raw_path, content in request.files.items():
            basename = raw_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            clean_name = _re_module.sub(r"^[a-f0-9-]+_", "", basename)
            zf.writestr(clean_name, content)

    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=fixed_files.zip"},
    )
