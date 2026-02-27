"""Report formatting for Arcane Auditor scan results."""

from __future__ import annotations

import json
import logging
from collections import Counter

from src.models import ReportFormat, ReporterError, ScanResult

logger = logging.getLogger(__name__)


def report_findings(scan_result: ScanResult, format: ReportFormat) -> str:
    """Dispatch to the correct format function based on the format enum value.

    Args:
        scan_result: The scan result to format.
        format: The desired output format.

    Returns:
        The formatted report as a string.

    Raises:
        ReporterError: If the format is unimplemented or unrecognized.
    """
    if format == ReportFormat.JSON:
        return format_json(scan_result)
    elif format == ReportFormat.SARIF:
        raise ReporterError("SARIF format not yet implemented")
    elif format == ReportFormat.GITHUB_ISSUES:
        raise ReporterError("GitHub Issues format not yet implemented")
    elif format == ReportFormat.PR_COMMENT:
        raise ReporterError("PR Comment format not yet implemented")
    elif format == ReportFormat.SUMMARY:
        return format_summary(scan_result)

    raise ReporterError(f"Unsupported report format: {format!r}")


def format_json(scan_result: ScanResult) -> str:
    """Serialize a ScanResult to a pretty-printed JSON string.

    Args:
        scan_result: The scan result to serialize.

    Returns:
        A valid JSON string, indented with 2 spaces.
    """
    data = scan_result.model_dump(mode="json")
    return json.dumps(data, indent=2)


def format_summary(scan_result: ScanResult) -> str:
    """Produce a human-readable text summary with counts by severity, rule, and file.

    Args:
        scan_result: The scan result to summarize.

    Returns:
        A multi-line summary string.
    """
    lines: list[str] = []
    lines.append(f"Arcane Auditor -- {scan_result.repo}")
    lines.append(f"Scanned: {scan_result.timestamp.isoformat()}")
    lines.append(
        f"Total findings: {scan_result.findings_count}  "
        f"(ACTION: {scan_result.action_count}, ADVICE: {scan_result.advice_count})"
    )
    lines.append("-" * 60)

    if scan_result.findings_count == 0:
        lines.append("No findings. Application is clean.")
    else:
        lines.append("By Severity:")
        lines.append(f"  ACTION : {scan_result.action_count}")
        lines.append(f"  ADVICE : {scan_result.advice_count}")

        lines.append("By Rule:")
        rule_counts = Counter(f.rule_id for f in scan_result.findings)
        for rule_id, count in rule_counts.most_common():
            lines.append(f"  {rule_id:<50} {count}")

        lines.append("By File:")
        file_counts = Counter(f.file_path for f in scan_result.findings)
        for file_path, count in file_counts.most_common():
            lines.append(f"  {file_path:<60} {count}")

    return "\n".join(lines)
