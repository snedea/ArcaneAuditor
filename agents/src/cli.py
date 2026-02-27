"""Entry point for the arcane-agent CLI; wires scan -> runner -> reporter pipeline."""

from __future__ import annotations

import logging
import os
import shutil
import stat
import subprocess
import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from github import Auth, Github, GithubException
from typer.core import TyperGroup

from src.config import load_config
from src.fixer import apply_fixes, fix_findings
from src.models import ConfigError, ExitCode, FixerError, ReportFormat, ReporterError, RunnerError, ScanError, ScanResult
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

class _DefaultScanGroup(TyperGroup):
    """Route bare invocations (no subcommand) to the ``scan`` command for backwards compatibility."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:  # type: ignore[override]
        if args and args[0] not in self.commands:
            args = ["scan"] + args
        elif not args:
            args = ["scan"]
        return super().parse_args(ctx, args)


app = typer.Typer(name="arcane-agent", help="Autonomous agent for Arcane Auditor deterministic code review.", cls=_DefaultScanGroup)


def _configure_logging(quiet: bool) -> None:
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def _error(msg: str) -> None:
    typer.echo(f"Error: {msg}", err=True)


def _build_fix_pr_body(scan_result: ScanResult, written_files: list[Path]) -> str:
    """Build markdown body for the auto-fix PR.

    Args:
        scan_result: The scan output containing findings.
        written_files: List of file paths that were fixed.

    Returns:
        Markdown-formatted PR body string.
    """
    lines: list[str] = []
    lines.append("## Arcane Auditor Auto-Fixes")
    lines.append("")
    lines.append(f"Applied {len(written_files)} automatic fix(es) for {scan_result.findings_count} finding(s).")
    lines.append("")
    lines.append("### Fixed Files")
    lines.append("")
    for f in written_files:
        lines.append(f"- {f}")
    lines.append("")
    lines.append("### Original Findings")
    lines.append("")
    lines.append("| Rule | Severity | File | Message |")
    lines.append("| --- | --- | --- | --- |")
    for f in scan_result.findings:
        lines.append(f"| {f.rule_id} | {f.severity.value} | {f.file_path} | {f.message} |")
    lines.append("")
    lines.append("---")
    lines.append("*Auto-fixed by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*")
    return "\n".join(lines)


def _create_fix_pr(repo: str, token: str, source_dir: Path, written_files: list[Path], scan_result: ScanResult, quiet: bool) -> str:
    """Commit fixed files to a new branch and open a PR via PyGithub.

    Args:
        repo: GitHub repo in owner/repo format.
        token: GitHub access token.
        source_dir: Root directory of the cloned repo.
        written_files: List of file paths that were fixed.
        scan_result: The scan output containing findings.
        quiet: Whether to suppress informational messages.

    Returns:
        The HTML URL of the created pull request.

    Raises:
        FixerError: If any git subprocess or GitHub API call fails.
    """
    branch_name = f"arcane-auditor/fix-{int(scan_result.timestamp.timestamp())}"

    result = subprocess.run(["git", "-C", str(source_dir), "checkout", "-b", branch_name], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise FixerError(f"git checkout -b failed: {result.stderr.strip()}")

    result = subprocess.run(["git", "-C", str(source_dir), "add"] + [str(f) for f in written_files], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise FixerError(f"git add failed: {result.stderr.strip()}")

    commit_msg = f"fix: apply Arcane Auditor auto-fixes ({len(written_files)} files)"
    result = subprocess.run(["git", "-C", str(source_dir), "commit", "-m", commit_msg], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise FixerError(f"git commit failed: {result.stderr.strip()}")

    # Avoid embedding the token in subprocess argv (visible in /proc/PID/cmdline and ps aux).
    # Write a GIT_ASKPASS helper that echoes the token so git fetches it from env, not argv.
    fd, askpass_path = tempfile.mkstemp(suffix=".py", prefix="arcane_askpass_")
    try:
        with os.fdopen(fd, "w") as askpass_f:
            askpass_f.write("#!/usr/bin/env python3\n")
            askpass_f.write(f"print({token!r})\n")
        os.chmod(askpass_path, stat.S_IRWXU)
        push_env = {**os.environ, "GIT_ASKPASS": askpass_path, "GIT_USERNAME": "x-access-token"}
        result = subprocess.run(
            ["git", "-C", str(source_dir), "push", f"https://github.com/{repo}.git", branch_name],
            capture_output=True, text=True, check=False, env=push_env,
        )
    finally:
        try:
            os.unlink(askpass_path)
        except OSError:
            pass
    if result.returncode != 0:
        raise FixerError(f"git push failed: {result.stderr.strip()}")

    with Github(auth=Auth.Token(token)) as gh:
        try:
            repo_obj = gh.get_repo(repo)
            pr_body = _build_fix_pr_body(scan_result, written_files)
            pr = repo_obj.create_pull(
                title=f"fix: Arcane Auditor auto-fixes ({len(written_files)} files)",
                body=pr_body,
                head=branch_name,
                base="main",
            )
            return pr.html_url
        except GithubException as exc:
            raise FixerError(f"GitHub API error creating PR: {exc}") from exc


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


@app.command()
def fix(
    path: Optional[Path] = typer.Argument(None, help="Local path to scan and fix Workday Extend artifacts"),
    repo: Optional[str] = typer.Option(None, "--repo", help="GitHub repo in owner/repo format (e.g. acme/payroll)"),
    target_dir: Optional[Path] = typer.Option(None, "--target-dir", help="Write fixed files to this directory instead of modifying source"),
    create_pr: bool = typer.Option(False, "--create-pr", help="Create a GitHub PR with the fixes (requires --repo and GITHUB_TOKEN)"),
    config: Optional[str] = typer.Option(None, "--config", help="Arcane Auditor config preset name or path"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress informational messages; only errors go to stderr"),
) -> None:
    """Scan, audit, fix, and optionally create a PR for Workday Extend artifacts.

    Pipeline: scan -> audit -> fix -> (optional) re-audit -> (optional) create PR.
    """
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

    if create_pr and repo is None:
        _error("--create-pr requires --repo")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    token: str = agent_config.github_token.get_secret_value() if agent_config.github_token is not None else ""

    if create_pr and not token:
        _error("--create-pr requires a GitHub token; set GITHUB_TOKEN env var")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if target_dir is not None and create_pr:
        _error("Cannot specify both --target-dir and --create-pr")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    manifest = None
    try:
        try:
            if path is not None:
                manifest = scan_local(path)
            else:
                assert repo is not None
                manifest = scan_github(repo, "main", token)
        except ScanError as exc:
            _error(str(exc))
            raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

        try:
            scan_result = run_audit(manifest, agent_config)
        except RunnerError as exc:
            _error(str(exc))
            raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))

        if scan_result.exit_code == ExitCode.CLEAN:
            if not quiet:
                typer.echo("No findings to fix.", err=True)
            raise typer.Exit(code=0)

        try:
            fix_results = fix_findings(scan_result, manifest.root_path)
        except FixerError as exc:
            _error(str(exc))
            raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))

        if len(fix_results) == 0:
            if not quiet:
                typer.echo("No auto-fixable findings.", err=True)
            raise typer.Exit(code=int(scan_result.exit_code))

        output_dir = target_dir if target_dir is not None else manifest.root_path

        try:
            written = apply_fixes(fix_results, output_dir)
        except FixerError as exc:
            _error(str(exc))
            raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))

        if not quiet:
            typer.echo(f"Applied {len(written)} fix(es).", err=True)

        reaudit_dir = target_dir if target_dir is not None else manifest.root_path
        reaudit_result = None
        try:
            reaudit_manifest = scan_local(reaudit_dir)
            reaudit_result = run_audit(reaudit_manifest, agent_config)
        except (ScanError, RunnerError) as exc:
            logger.warning("Re-audit failed: %s", exc)
            reaudit_result = None

        if reaudit_result is not None and not quiet:
            before = scan_result.findings_count
            after = reaudit_result.findings_count
            typer.echo(f"Re-audit: {before} -> {after} findings.", err=True)

        if create_pr:
            assert repo is not None
            try:
                pr_url = _create_fix_pr(repo, token, manifest.root_path, written, scan_result, quiet)
            except FixerError as exc:
                _error(str(exc))
                raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))
            typer.echo(pr_url)

        final_exit_code = reaudit_result.exit_code if reaudit_result is not None else scan_result.exit_code
        raise typer.Exit(code=int(final_exit_code))
    finally:
        if manifest is not None and manifest.temp_dir is not None:
            shutil.rmtree(manifest.temp_dir, ignore_errors=True)
