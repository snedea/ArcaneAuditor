"""Report formatting for Arcane Auditor scan results."""

from __future__ import annotations

import json
import logging
from collections import Counter

from src.models import Finding, ReportFormat, ReporterError, ScanResult, Severity

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
        return format_sarif(scan_result)
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


def format_sarif(scan_result: ScanResult) -> str:
    """Produce a valid SARIF v2.1.0 JSON document from a ScanResult.

    Args:
        scan_result: The scan result to convert.

    Returns:
        A pretty-printed JSON string representing the SARIF document.
    """
    rules = _build_sarif_rules(scan_result.findings)
    rule_index_map: dict[str, int] = {rule["id"]: i for i, rule in enumerate(rules)}
    results = [_build_sarif_result(f, rule_index_map) for f in scan_result.findings]
    doc = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Arcane Auditor",
                        "version": "1.0.0",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(doc, indent=2)


def _build_sarif_rules(findings: list[Finding]) -> list[dict]:
    """Build a deduplicated, ordered list of SARIF rule descriptor dicts from findings.

    Args:
        findings: List of findings to extract rules from.

    Returns:
        Ordered list of SARIF rule descriptor dicts.
    """
    seen: dict[str, str] = {}
    order: list[str] = []
    for f in findings:
        level = "error" if f.severity == Severity.ACTION else "warning"
        if f.rule_id not in seen:
            order.append(f.rule_id)
            seen[f.rule_id] = level
        elif level == "error":
            seen[f.rule_id] = "error"
    return [
        {
            "id": rule_id,
            "name": rule_id,
            "shortDescription": {"text": rule_id},
            "defaultConfiguration": {"level": seen[rule_id]},
        }
        for rule_id in order
    ]


def _build_sarif_result(finding: Finding, rule_index_map: dict[str, int]) -> dict:
    """Build a single SARIF result dict from a Finding.

    Args:
        finding: The finding to convert.
        rule_index_map: Mapping of rule IDs to their index in the rules array.

    Returns:
        A single SARIF result object.
    """
    level = "error" if finding.severity == Severity.ACTION else "warning"
    start_line = max(1, finding.line)
    uri = finding.file_path.replace("\\", "/")
    return {
        "ruleId": finding.rule_id,
        "ruleIndex": rule_index_map[finding.rule_id],
        "level": level,
        "message": {"text": finding.message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": uri,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": start_line,
                    },
                }
            }
        ],
    }
