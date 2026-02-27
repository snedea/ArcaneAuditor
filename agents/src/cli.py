"""Entry point for the arcane-agent CLI; wires scan -> runner -> reporter pipeline."""

from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import typer
from github import Auth, Github, GithubException
from typer.core import TyperGroup

from src.config import load_config
from src.fixer import apply_fixes, fix_findings
from src.models import AgentConfig, ConfigError, ExitCode, FixerError, ReportFormat, ReporterError, RunnerError, ScanError, ScanResult, WatchError, WatchState
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
                base=repo_obj.default_branch,
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

    if repo is not None and not create_pr and target_dir is None:
        _error("--repo requires --create-pr or --target-dir; fixes would be lost when the temp clone is removed")
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


def _load_watch_state(state_file: Path, repo: str) -> WatchState:
    """Load persisted watch state from disk, or return a fresh state on any error.

    Args:
        state_file: Path to the JSON state file.
        repo: GitHub repo in owner/repo format. Used to detect stale state files.

    Returns:
        Existing WatchState if the file is valid and matches repo, otherwise a fresh
        WatchState with an empty seen_prs dict.
    """
    if not state_file.exists():
        return WatchState(repo=repo)
    raw = state_file.read_text(encoding="utf-8")
    try:
        state = WatchState.model_validate_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("Corrupt state file %s, starting fresh: %s", state_file, exc)
        return WatchState(repo=repo)
    if state.repo != repo:
        logger.warning("State file repo mismatch: expected %s, got %s. Starting fresh.", repo, state.repo)
        return WatchState(repo=repo)
    return state


def _save_watch_state(state: WatchState, state_file: Path) -> None:
    """Atomically write watch state to disk using a .tmp-then-replace strategy.

    Args:
        state: Current WatchState to persist.
        state_file: Destination path for the JSON state file.

    Raises:
        OSError: If the write or rename fails (disk full, permissions, etc.).
    """
    data = state.model_dump_json(indent=2)
    tmp = state_file.with_suffix(".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(state_file)


def _list_open_prs(repo: str, token: str) -> list[tuple[int, str]]:
    """Fetch the list of open PRs for a GitHub repo.

    Args:
        repo: GitHub repo in owner/repo format.
        token: GitHub personal access token or app token.

    Returns:
        List of (pr_number, head_branch) tuples, ordered newest-first.

    Raises:
        WatchError: If the GitHub API call fails for any reason.
    """
    try:
        with Github(auth=Auth.Token(token)) as gh:
            repo_obj = gh.get_repo(repo)
            pulls = repo_obj.get_pulls(state="open", sort="created", direction="desc")
            return [(pr.number, pr.head.ref) for pr in pulls]
    except GithubException as exc:
        raise WatchError(f"GitHub API error listing PRs for {repo!r}: {exc}") from exc


def _process_single_pr(repo: str, pr_number: int, head_branch: str, token: str, agent_config: AgentConfig, quiet: bool) -> str:
    """Clone the PR branch, run the audit, and post a PR comment with the results.

    Args:
        repo: GitHub repo in owner/repo format.
        pr_number: Pull request number to process.
        head_branch: Branch name for the PR head (used for checkout).
        token: GitHub personal access token or app token.
        agent_config: Resolved agent configuration (auditor path, etc.).
        quiet: If True, suppress informational echo output.

    Returns:
        URL of the posted PR comment.

    Raises:
        ScanError: If cloning or scanning the repo fails.
        RunnerError: If the audit subprocess fails unexpectedly.
        ReporterError: If posting the GitHub comment fails.
    """
    logger.info("Processing PR #%d (branch: %s)", pr_number, head_branch)
    manifest = scan_github(repo, head_branch, token)
    try:
        scan_result = run_audit(manifest, agent_config)
        comment_url = format_pr_comment(scan_result, repo, pr_number, token)
        return comment_url
    finally:
        if manifest.temp_dir is not None:
            shutil.rmtree(manifest.temp_dir, ignore_errors=True)


@app.command()
def watch(
    repo: str = typer.Option(..., "--repo", help="GitHub repo in owner/repo format (e.g. acme/payroll)"),
    interval: int = typer.Option(300, "--interval", help="Polling interval in seconds"),
    state_file: Path = typer.Option(Path(".arcane-watch-state.json"), "--state-file", help="Path to the JSON state file for tracking seen PRs"),
    config: Optional[str] = typer.Option(None, "--config", help="Arcane Auditor config preset name or path"),
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

    token = agent_config.github_token.get_secret_value() if agent_config.github_token is not None else ""

    if not token:
        _error("watch requires a GitHub token; set GITHUB_TOKEN env var")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    if interval < 1:
        _error("--interval must be >= 1")
        raise typer.Exit(code=int(ExitCode.USAGE_ERROR))

    shutdown_requested = False

    def _handle_sigint(signum: int, frame: Any) -> None:
        nonlocal shutdown_requested
        shutdown_requested = True
        logger.warning("Shutdown requested, finishing current cycle...")

    previous_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, _handle_sigint)

    state = _load_watch_state(state_file, repo)

    if not quiet:
        typer.echo(f"Watching {repo} for new PRs (interval: {interval}s, state: {state_file})", err=True)

    try:
        while not shutdown_requested:
            try:
                open_prs = _list_open_prs(repo, token)
            except WatchError as exc:
                _error(str(exc))
                if shutdown_requested:
                    break
                for _ in range(interval):
                    if shutdown_requested:
                        break
                    time.sleep(1)
                continue

            new_prs = [(num, branch) for num, branch in open_prs if not state.has_seen(num)]

            if new_prs and not quiet:
                typer.echo(f"Found {len(new_prs)} new PR(s): {', '.join(f'#{n}' for n, _ in new_prs)}", err=True)

            for pr_number, head_branch in new_prs:
                if shutdown_requested:
                    break
                try:
                    comment_url = _process_single_pr(repo, pr_number, head_branch, token, agent_config, quiet)
                    state.mark_seen(pr_number, comment_url)
                    try:
                        _save_watch_state(state, state_file)
                    except OSError as exc:
                        logger.warning("Could not save state file %s: %s", state_file, exc)
                    if not quiet:
                        typer.echo(f"PR #{pr_number}: {comment_url}", err=True)
                except (ScanError, RunnerError, ReporterError) as exc:
                    logger.warning("Failed to process PR #%d: %s", pr_number, exc)
                    continue

            if shutdown_requested:
                break

            for _ in range(interval):
                if shutdown_requested:
                    break
                time.sleep(1)
    finally:
        signal.signal(signal.SIGINT, previous_handler)

    if not quiet:
        typer.echo("Watch stopped.", err=True)

    raise typer.Exit(code=0)
