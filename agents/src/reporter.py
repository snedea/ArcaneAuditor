"""Report formatting for Arcane Auditor scan results."""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from github import Auth, Github, GithubException

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
        raise ReporterError(
            "GitHub Issues format requires repo and token -- call format_github_issues() directly"
        )
    elif format == ReportFormat.PR_COMMENT:
        raise ReporterError(
            "PR Comment format requires repo, pr_number, and token -- call format_pr_comment() directly"
        )
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


def format_github_issues(scan_result: ScanResult, repo: str, token: str) -> list[str]:
    """Create GitHub issues for scan findings.

    Creates one issue per ACTION finding and one grouped summary issue for all
    ADVICE findings. Skips duplicates by title match against existing open issues.

    Args:
        scan_result: The scan result containing findings.
        repo: The GitHub repo in "owner/name" format.
        token: A GitHub personal access token with repo scope.

    Returns:
        List of HTML URLs for created issues.

    Raises:
        ReporterError: If any GitHub API call fails.
    """
    with Github(auth=Auth.Token(token)) as gh:
        try:
            repo_obj = gh.get_repo(repo)
        except GithubException as exc:
            raise ReporterError(f"GitHub API error accessing repo {repo!r}: {exc}") from exc

        _ensure_label(repo_obj, "arcane-auditor", "0075ca")
        _ensure_label(repo_obj, "arcane-auditor:ACTION", "e11d48")
        _ensure_label(repo_obj, "arcane-auditor:ADVICE", "f59e0b")

        existing_titles = _get_existing_issue_titles(repo_obj)
        created_urls: list[str] = []

        action_findings = [f for f in scan_result.findings if f.severity == Severity.ACTION]
        advice_findings = [f for f in scan_result.findings if f.severity == Severity.ADVICE]

        for finding in action_findings:
            title = _build_action_issue_title(finding)
            if title in existing_titles:
                logger.debug("Skipping duplicate issue: %s", title)
                continue
            body = _build_action_issue_body(finding)
            try:
                issue = repo_obj.create_issue(
                    title=title,
                    body=body,
                    labels=["arcane-auditor", "arcane-auditor:ACTION"],
                )
            except GithubException as exc:
                raise ReporterError(f"GitHub API error creating issue {title!r}: {exc}") from exc
            created_urls.append(issue.html_url)
            existing_titles.add(title)

        if advice_findings:
            title = "[Arcane Auditor] ADVICE Summary"
            if title in existing_titles:
                logger.debug("Skipping duplicate advice summary issue")
            else:
                body = _build_advice_issue_body(advice_findings)
                try:
                    issue = repo_obj.create_issue(
                        title=title,
                        body=body,
                        labels=["arcane-auditor", "arcane-auditor:ADVICE"],
                    )
                except GithubException as exc:
                    raise ReporterError(f"GitHub API error creating ADVICE summary issue: {exc}") from exc
                created_urls.append(issue.html_url)

        return created_urls


def _ensure_label(repo_obj: Any, name: str, color: str) -> None:
    """Create the GitHub label if it does not already exist on the repo.

    Args:
        repo_obj: A PyGithub Repository object.
        name: The label name.
        color: The label color as a 6-character hex string (no # prefix).

    Raises:
        ReporterError: If the GitHub API returns an error other than 404.
    """
    try:
        repo_obj.get_label(name)
    except GithubException as exc:
        if exc.status == 404:
            try:
                repo_obj.create_label(name=name, color=color)
            except GithubException as create_exc:
                # 422 means the label was created by a concurrent run between our get and create -- that's fine.
                if create_exc.status != 422:
                    raise ReporterError(f"GitHub API error creating label {name!r}: {create_exc}") from create_exc
        else:
            raise ReporterError(f"GitHub API error ensuring label {name!r}: {exc}") from exc


def _get_existing_issue_titles(repo_obj: Any) -> set[str]:
    """Return titles of all open issues labelled "arcane-auditor".

    Args:
        repo_obj: A PyGithub Repository object.

    Returns:
        Set of issue title strings.

    Raises:
        ReporterError: If the GitHub API call fails.
    """
    try:
        issues = repo_obj.get_issues(state="open", labels=["arcane-auditor"])
        return {issue.title for issue in issues}
    except GithubException as exc:
        raise ReporterError(f"GitHub API error fetching existing issues: {exc}") from exc


def _build_action_issue_title(finding: Finding) -> str:
    """Build the canonical GitHub issue title for one ACTION finding.

    Args:
        finding: The ACTION finding.

    Returns:
        The issue title string.
    """
    return f"[Arcane Auditor] {finding.rule_id}: {finding.file_path}"


def _build_action_issue_body(finding: Finding) -> str:
    """Build the markdown issue body for one ACTION finding.

    Args:
        finding: The ACTION finding.

    Returns:
        The issue body as a markdown string.
    """
    lines: list[str] = [
        f"## {finding.rule_id}",
        "",
        "**Severity:** ACTION",
        f"**File:** {finding.file_path}",
        f"**Line:** {finding.line}",
        "",
        "**Message:**",
        "",
        f"> {finding.message}",
        "",
        "---",
        "",
        "*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*",
    ]
    return "\n".join(lines)


def _build_advice_issue_body(findings: list[Finding]) -> str:
    """Build the markdown issue body for the grouped ADVICE summary issue.

    Args:
        findings: List of ADVICE findings.

    Returns:
        The issue body as a markdown string.
    """
    lines: list[str] = []
    lines.append(f"## Arcane Auditor ADVICE Summary ({len(findings)} findings)")
    lines.append("These are advisory findings -- they do not require immediate action but indicate opportunities for improvement.")
    lines.append("")
    lines.append("| Rule | File | Line | Message |")
    lines.append("| --- | --- | --- | --- |")
    for f in findings:
        safe_path = f.file_path.replace("|", r"\|").replace("\n", " ")
        safe_msg = f.message.replace("|", r"\|").replace("\n", " ")
        lines.append(f"| {f.rule_id} | {safe_path} | {f.line} | {safe_msg} |")
    lines.append("")
    lines.append("---")
    lines.append("*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*")
    return "\n".join(lines)


def _build_pr_comment_body(scan_result: ScanResult) -> str:
    """Build the full markdown body for a PR comment summarizing scan results.

    Args:
        scan_result: The scan result to format.

    Returns:
        The full markdown body string for the PR comment.
    """
    lines: list[str] = []
    lines.append("## Arcane Auditor Results")
    lines.append("")
    if scan_result.findings_count == 0:
        lines.append("No findings. This application is clean.")
        lines.append("")
        lines.append("---")
        lines.append("*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*")
        return "\n".join(lines)
    action_findings: list[Finding] = [f for f in scan_result.findings if f.severity == Severity.ACTION]
    advice_findings: list[Finding] = [f for f in scan_result.findings if f.severity == Severity.ADVICE]
    lines.append(f"**{scan_result.findings_count} findings** (ACTION: {scan_result.action_count}, ADVICE: {scan_result.advice_count})")
    lines.append("")
    if action_findings:
        lines.append("### ACTION Findings")
        lines.append("")
        lines.append("| Rule | File | Line | Message |")
        lines.append("| --- | --- | --- | --- |")
        for f in action_findings:
            safe_path = f.file_path.replace("|", r"\|").replace("\n", " ")
            safe_msg = f.message.replace("|", r"\|").replace("\n", " ")
            lines.append(f"| {f.rule_id} | {safe_path} | {f.line} | {safe_msg} |")
        lines.append("")
    if advice_findings:
        lines.append("<details>")
        lines.append(f"<summary>ADVICE Findings ({len(advice_findings)})</summary>")
        lines.append("")
        lines.append("| Rule | File | Line | Message |")
        lines.append("| --- | --- | --- | --- |")
        for f in advice_findings:
            safe_path = f.file_path.replace("|", r"\|").replace("\n", " ")
            safe_msg = f.message.replace("|", r"\|").replace("\n", " ")
            lines.append(f"| {f.rule_id} | {safe_path} | {f.line} | {safe_msg} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    lines.append("---")
    lines.append("*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*")
    return "\n".join(lines)


def format_pr_comment(scan_result: ScanResult, repo: str, pr_number: int, token: str) -> str:
    """Post a single comment on a GitHub PR summarizing all findings.

    Args:
        scan_result: The scan result containing findings.
        repo: The GitHub repo in "owner/name" format.
        pr_number: The pull request number.
        token: A GitHub personal access token with repo scope.

    Returns:
        The HTML URL of the created PR comment.

    Raises:
        ReporterError: If any GitHub API call fails.
    """
    with Github(auth=Auth.Token(token)) as gh:
        try:
            repo_obj = gh.get_repo(repo)
        except GithubException as exc:
            raise ReporterError(f"GitHub API error accessing repo {repo!r}: {exc}") from exc
        try:
            pr = repo_obj.get_pull(pr_number)
        except GithubException as exc:
            raise ReporterError(f"GitHub API error accessing PR #{pr_number} in {repo!r}: {exc}") from exc
        body: str = _build_pr_comment_body(scan_result)
        try:
            comment = pr.create_issue_comment(body)
        except GithubException as exc:
            raise ReporterError(f"GitHub API error posting comment on PR #{pr_number} in {repo!r}: {exc}") from exc
        return comment.html_url
