"""Entry point for the arcane-agent CLI; wires scan -> runner -> reporter pipeline."""

from __future__ import annotations

import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from src.config import load_config
from src.models import ConfigError, ExitCode, ReportFormat, ReporterError, RunnerError, ScanError
from src.reporter import format_github_issues, format_pr_comment, report_findings
from src.runner import run_audit
from src.scanner import scan_github, scan_local

logger = logging.getLogger(__name__)


class CliFormat(str, Enum):
    JSON = "json"
    SARIF = "sarif"
    SUMMARY = "summary"
    GITHUB_ISSUES = "github-issues"
    PR_COMMENT = "pr-comment"


_FORMAT_MAP: dict[CliFormat, ReportFormat] = {
    CliFormat.JSON: ReportFormat.JSON,
    CliFormat.SARIF: ReportFormat.SARIF,
    CliFormat.SUMMARY: ReportFormat.SUMMARY,
    CliFormat.GITHUB_ISSUES: ReportFormat.GITHUB_ISSUES,
    CliFormat.PR_COMMENT: ReportFormat.PR_COMMENT,
}

app = typer.Typer(name="arcane-agent", help="Autonomous agent for Arcane Auditor deterministic code review.")


def _configure_logging(quiet: bool) -> None:
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def _error(msg: str) -> None:
    typer.echo(f"Error: {msg}", err=True)


@app.command()
def scan(
    path: Optional[Path] = typer.Argument(None, help="Local path to scan for Workday Extend artifacts"),
    repo: Optional[str] = typer.Option(None, "--repo", help="GitHub repo in owner/repo format (e.g. acme/payroll)"),
    pr: Optional[int] = typer.Option(None, "--pr", help="GitHub PR number (requires --repo)"),
    format: CliFormat = typer.Option(CliFormat.JSON, "--format", help="Output format: json, sarif, summary, github-issues, pr-comment"),
    output: Optional[Path] = typer.Option(None, "--output", help="Write output to this file path instead of stdout"),
    config: Optional[str] = typer.Option(None, "--config", help="Arcane Auditor config preset name or path (e.g. production-ready)"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress informational messages; only errors go to stderr"),
) -> None:
    _configure_logging(quiet)

    try:
        agent_config = load_config(None)
    except ConfigError as exc:
        _error(str(exc))
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if config is not None:
        agent_config = agent_config.model_copy(update={"config_preset": config})

    if path is None and repo is None:
        _error("Must specify either PATH or --repo")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if path is not None and repo is not None:
        _error("Cannot specify both PATH and --repo")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if pr is not None and repo is None:
        _error("--pr requires --repo")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if format == CliFormat.GITHUB_ISSUES and repo is None:
        _error("--format github-issues requires --repo")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if format == CliFormat.PR_COMMENT and repo is None:
        _error("--format pr-comment requires --repo")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if format == CliFormat.PR_COMMENT and pr is None:
        _error("--format pr-comment requires --pr")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    token: str = agent_config.github_token.get_secret_value() if agent_config.github_token is not None else ""

    if format in (CliFormat.GITHUB_ISSUES, CliFormat.PR_COMMENT) and not token:
        _error("GitHub token required for --format github-issues / pr-comment; set GITHUB_TOKEN env var")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    try:
        if path is not None:
            manifest = scan_local(path)
        else:
            manifest = scan_github(repo, "main", token)
    except ScanError as exc:
        _error(str(exc))
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    try:
        scan_result = run_audit(manifest, agent_config)
    except RunnerError as exc:
        _error(str(exc))
        raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))
    finally:
        if manifest.temp_dir is not None:
            shutil.rmtree(manifest.temp_dir, ignore_errors=True)

    try:
        if format == CliFormat.GITHUB_ISSUES:
            urls = format_github_issues(scan_result, repo, token)
            formatted: str = "\n".join(urls) if urls else "No issues created."
        elif format == CliFormat.PR_COMMENT:
            formatted = format_pr_comment(scan_result, repo, pr, token)
        else:
            formatted = report_findings(scan_result, _FORMAT_MAP[format])
    except ReporterError as exc:
        _error(str(exc))
        raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))

    if output is not None:
        output.write_text(formatted, encoding="utf-8")
        if not quiet:
            typer.echo(f"Output written to {output}", err=True)
    else:
        typer.echo(formatted)

    raise typer.Exit(code=int(scan_result.exit_code))
