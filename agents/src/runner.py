"""Invoke the parent Arcane Auditor tool as a subprocess and parse its JSON output."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from pydantic import ValidationError

from src.models import AgentConfig, ExitCode, Finding, RunnerError, ScanManifest, ScanResult

logger = logging.getLogger(__name__)


def run_audit(scan_manifest: ScanManifest, config: AgentConfig) -> ScanResult:
    """Invoke Arcane Auditor on the manifest's root_path, parse JSON output, return ScanResult.

    Args:
        scan_manifest: The scan manifest describing what to audit.
        config: Agent configuration including the auditor path.

    Returns:
        A ScanResult with parsed findings.

    Raises:
        RunnerError: If the subprocess fails, times out, or produces unparseable output.
    """
    auditor_path = config.auditor_path.resolve()
    cmd: list[str] = [
        "uv", "run", "main.py", "review-app",
        str(scan_manifest.root_path), "--format", "json", "--quiet",
    ]
    logger.debug("run_audit: path=%s auditor=%s", scan_manifest.root_path, auditor_path)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=300, cwd=auditor_path,
        )
    except subprocess.TimeoutExpired:
        raise RunnerError(
            f"Arcane Auditor timed out after 300 seconds for path: {scan_manifest.root_path}"
        )
    except OSError as exc:
        raise RunnerError(f"Failed to invoke Arcane Auditor subprocess: {exc}") from exc

    logger.debug(
        "run_audit: returncode=%d stdout_len=%d stderr_len=%d",
        result.returncode, len(result.stdout), len(result.stderr),
    )

    if result.returncode == ExitCode.USAGE_ERROR:
        raise RunnerError(
            f"Arcane Auditor usage error (exit 2) for path '{scan_manifest.root_path}': "
            f"{(result.stdout.strip() or result.stderr.strip())[:500]}"
        )

    if result.returncode == ExitCode.RUNTIME_ERROR:
        raise RunnerError(
            f"Arcane Auditor runtime error (exit 3) for path '{scan_manifest.root_path}': "
            f"{(result.stderr.strip() or result.stdout.strip())[:500]}"
        )

    if result.returncode not in (ExitCode.CLEAN, ExitCode.ISSUES_FOUND):
        raise RunnerError(
            f"Arcane Auditor returned unexpected exit code {result.returncode} "
            f"for path '{scan_manifest.root_path}'"
        )

    data = _parse_json_output(result.stdout, scan_manifest.root_path)
    findings = _build_findings(data, scan_manifest.root_path)
    exit_code = ExitCode(result.returncode)
    repo = scan_manifest.repo if scan_manifest.repo is not None else str(scan_manifest.root_path)

    return ScanResult(repo=repo, findings_count=len(findings), findings=findings, exit_code=exit_code)


def _parse_json_output(stdout: str, path: Path) -> dict:
    """Extract and parse the JSON object from noisy stdout.

    Args:
        stdout: Raw stdout from the Arcane Auditor subprocess.
        path: The path being scanned, used for error messages.

    Returns:
        The parsed JSON object as a dict.

    Raises:
        RunnerError: If no JSON is found or parsing fails.
    """
    idx = stdout.find("{")
    if idx == -1:
        raise RunnerError(
            f"No JSON found in Arcane Auditor stdout for path '{path}'. "
            f"stdout snippet: {stdout[:300]!r}"
        )

    decoder = json.JSONDecoder()
    try:
        data, _ = decoder.raw_decode(stdout, idx)
    except json.JSONDecodeError as exc:
        raise RunnerError(
            f"Failed to parse Arcane Auditor JSON output for path '{path}': {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise RunnerError(f"Arcane Auditor JSON output is not an object for path '{path}'")

    return data


def _build_findings(data: dict, path: Path) -> list[Finding]:
    """Validate and construct Finding models from the parsed JSON data.

    Args:
        data: Parsed JSON dict from Arcane Auditor output.
        path: The path being scanned, used for error messages.

    Returns:
        A list of validated Finding instances.

    Raises:
        RunnerError: If the findings key is invalid or a Finding fails validation.
    """
    raw_findings = data.get("findings", [])
    if not isinstance(raw_findings, list):
        raise RunnerError(
            f"'findings' key in Arcane Auditor output is not a list for path '{path}'"
        )

    findings: list[Finding] = []
    try:
        for item in raw_findings:
            findings.append(Finding.model_validate(item))
    except ValidationError as exc:
        raise RunnerError(
            f"Failed to validate Finding from Arcane Auditor output for path '{path}': {exc}"
        ) from exc

    return findings
