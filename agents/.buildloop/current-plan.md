# Plan: P7.1

## Dependencies
- list: no new dependencies required (all needed packages already in pyproject.toml: typer, pydantic, pygithub)
- commands: none

## Pre-flight Verification

Before writing any code, confirm these items are NOT already present in `src/cli.py`:
- A function named `fix` decorated with `@app.command()`
- An import of `fix_findings` or `apply_fixes`

If both are already present, skip all file operations and only update IMPL_PLAN.md.

## File Operations (in execution order)

### 1. MODIFY src/cli.py
- operation: MODIFY
- reason: Add the `fix` command that wires scan -> audit -> fix -> (optional) re-audit -> (optional) create-pr pipeline

#### anchor (existing code to locate insertion points)

Import block anchor (line 14):
```python
from src.models import ConfigError, ExitCode, ReportFormat, ReporterError, RunnerError, ScanError
```

End-of-file anchor (line 138-139):
```python
    raise typer.Exit(code=int(scan_result.exit_code))
```

#### Imports to ADD

Add these two lines immediately after the existing `from src.models import ...` line (line 14):

```python
from src.fixer import apply_fixes, fix_findings
from src.models import ConfigError, ExitCode, FixerError, ReportFormat, ReporterError, RunnerError, ScanError
```

Specifically: replace the existing line 14 with the above two lines. The first line adds the fixer imports. The second line is the same as the original but with `FixerError` added to the import list (inserted alphabetically between `ExitCode` and `ReportFormat`).

#### Functions

##### Function: `_create_fix_pr`

Add this private helper function AFTER the `_error` function (after line 48) and BEFORE the `@app.command()` decorator for `scan` (line 50):

- signature: `def _create_fix_pr(repo: str, token: str, source_dir: Path, written_files: list[Path], scan_result: ScanResult, quiet: bool) -> str`
- purpose: Commit fixed files to a new branch in a GitHub repo clone and open a PR via PyGithub
- logic:
  1. Import `subprocess` at module level (add `import subprocess` to the imports block, after `import shutil` on line 6)
  2. Create branch name: `branch_name = f"arcane-auditor/fix-{int(scan_result.timestamp.timestamp())}"`
  3. Run `subprocess.run(["git", "-C", str(source_dir), "checkout", "-b", branch_name], capture_output=True, text=True, check=False)`. If returncode != 0, raise `FixerError(f"git checkout -b failed: {result.stderr.strip()}")`
  4. Run `subprocess.run(["git", "-C", str(source_dir), "add"] + [str(f) for f in written_files], capture_output=True, text=True, check=False)`. If returncode != 0, raise `FixerError(f"git add failed: {result.stderr.strip()}")`
  5. Build commit message: `commit_msg = f"fix: apply Arcane Auditor auto-fixes ({len(written_files)} files)"`. Run `subprocess.run(["git", "-C", str(source_dir), "commit", "-m", commit_msg], capture_output=True, text=True, check=False)`. If returncode != 0, raise `FixerError(f"git commit failed: {result.stderr.strip()}")`
  6. Build push URL: `push_url = f"https://x-access-token:{token}@github.com/{repo}.git"`. Run `subprocess.run(["git", "-C", str(source_dir), "push", push_url, branch_name], capture_output=True, text=True, check=False)`. If returncode != 0, raise `FixerError(f"git push failed: {result.stderr.strip()}")`
  7. Use PyGithub to create PR:
     ```python
     from github import Auth, Github, GithubException
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
     ```
  8. If not quiet, log the PR URL via `typer.echo(f"PR created: {url}", err=True)`
- calls: `_build_fix_pr_body(scan_result, written_files)`
- returns: `str` (the PR HTML URL)
- error handling: Raise `FixerError` for any subprocess or GitHub API failure. Caller catches `FixerError`.

##### Function: `_build_fix_pr_body`

Add immediately before `_create_fix_pr`:

- signature: `def _build_fix_pr_body(scan_result: ScanResult, written_files: list[Path]) -> str`
- purpose: Build markdown body for the auto-fix PR
- logic:
  1. Create `lines: list[str] = []`
  2. Append `"## Arcane Auditor Auto-Fixes"`
  3. Append empty line
  4. Append `f"Applied {len(written_files)} automatic fix(es) for {scan_result.findings_count} finding(s)."`
  5. Append empty line
  6. Append `"### Fixed Files"`
  7. Append empty line
  8. For each `f` in `written_files`: append `f"- {f}"`
  9. Append empty line
  10. Append `"### Original Findings"`
  11. Append empty line
  12. Append `"| Rule | Severity | File | Message |"`
  13. Append `"| --- | --- | --- | --- |"`
  14. For each finding `f` in `scan_result.findings`: append `f"| {f.rule_id} | {f.severity.value} | {f.file_path} | {f.message} |"`
  15. Append empty line
  16. Append `"---"`
  17. Append `"*Auto-fixed by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*"`
  18. Return `"\n".join(lines)`
- calls: none
- returns: `str`
- error handling: none

##### Function: `fix` (the Typer command)

Add AFTER the `scan` command function (after line 139, at end of file):

- signature:
```python
@app.command()
def fix(
    path: Optional[Path] = typer.Argument(None, help="Local path to scan and fix Workday Extend artifacts"),
    repo: Optional[str] = typer.Option(None, "--repo", help="GitHub repo in owner/repo format (e.g. acme/payroll)"),
    target_dir: Optional[Path] = typer.Option(None, "--target-dir", help="Write fixed files to this directory instead of modifying source"),
    create_pr: bool = typer.Option(False, "--create-pr", help="Create a GitHub PR with the fixes (requires --repo and GITHUB_TOKEN)"),
    config: Optional[str] = typer.Option(None, "--config", help="Arcane Auditor config preset name or path"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress informational messages; only errors go to stderr"),
) -> None:
```
- purpose: Orchestrate the full fix pipeline: scan -> audit -> fix -> apply -> (optional re-audit) -> (optional create PR)
- logic (numbered steps):
  1. Call `_configure_logging(quiet)`
  2. Try `agent_config = load_config(None)`. Catch `ConfigError`, call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
  3. If `config is not None`: `agent_config = agent_config.model_copy(update={"config_preset": config})`
  4. Validate mutual exclusion: if `path is None and repo is None`, call `_error("Must specify either PATH or --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
  5. If `path is not None and repo is not None`, call `_error("Cannot specify both PATH and --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
  6. If `create_pr and repo is None`, call `_error("--create-pr requires --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
  7. Extract token: `token: str = agent_config.github_token.get_secret_value() if agent_config.github_token is not None else ""`
  8. If `create_pr and not token`, call `_error("--create-pr requires a GitHub token; set GITHUB_TOKEN env var")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
  9. If `target_dir is not None and create_pr`, call `_error("Cannot specify both --target-dir and --create-pr")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
  10. Begin try block. If `path is not None`: `manifest = scan_local(path)`. Else: `assert repo is not None` then `manifest = scan_github(repo, "main", token)`. Catch `ScanError`, call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
  11. Begin try block (with `finally` for temp_dir cleanup). Call `scan_result = run_audit(manifest, agent_config)`. Catch `RunnerError`, call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`
  12. If `scan_result.exit_code == ExitCode.CLEAN`: if not quiet, `typer.echo("No findings to fix.", err=True)`. Raise `typer.Exit(code=0)`
  13. Call `fix_results = fix_findings(scan_result, manifest.root_path)`. Catch `FixerError`, call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`
  14. If `len(fix_results) == 0`: if not quiet, `typer.echo("No auto-fixable findings.", err=True)`. Raise `typer.Exit(code=int(scan_result.exit_code))`
  15. Determine output directory: `output_dir = target_dir if target_dir is not None else manifest.root_path`
  16. Call `written = apply_fixes(fix_results, output_dir)`. Catch `FixerError`, call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`
  17. If not quiet: `typer.echo(f"Applied {len(written)} fix(es).", err=True)`
  18. Determine re-audit source: `reaudit_dir = target_dir if target_dir is not None else manifest.root_path`. Call `reaudit_manifest = scan_local(reaudit_dir)`. Call `reaudit_result = run_audit(reaudit_manifest, agent_config)`. Catch `(ScanError, RunnerError)` as exc: log warning `logger.warning("Re-audit failed: %s", exc)`, set `reaudit_result = None`
  19. If `reaudit_result is not None and not quiet`: compute `before = scan_result.findings_count`, `after = reaudit_result.findings_count`. `typer.echo(f"Re-audit: {before} -> {after} findings.", err=True)`
  20. If `create_pr`:
      - `assert repo is not None` (for type narrowing)
      - Try `pr_url = _create_fix_pr(repo, token, manifest.root_path, written, scan_result, quiet)`. Catch `FixerError`, call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`
      - `typer.echo(pr_url)`
  21. In `finally` block: `if manifest.temp_dir is not None: shutil.rmtree(manifest.temp_dir, ignore_errors=True)`
  22. Determine final exit code: if `reaudit_result is not None`, use `reaudit_result.exit_code`. Else use `scan_result.exit_code`. Raise `typer.Exit(code=int(final_exit_code))`

- calls: `_configure_logging`, `load_config`, `scan_local`, `scan_github`, `run_audit`, `fix_findings`, `apply_fixes`, `_create_fix_pr`, `scan_local` (for re-audit)
- returns: None (exits via typer.Exit)
- error handling: Each stage has specific exception handling as described in the logic steps above

#### Wiring / Integration
- The `fix` command is registered on the same `app = typer.Typer(...)` instance via `@app.command()` decorator
- No changes needed to `pyproject.toml` -- the entry point `src.cli:app` already exposes all commands on the Typer app
- The `fix` command reuses the same helper functions `_configure_logging` and `_error` as the `scan` command

#### Complete import block after modification

The final import section of `src/cli.py` (lines 1-18) should be:

```python
"""Entry point for the arcane-agent CLI; wires scan -> runner -> reporter pipeline."""

from __future__ import annotations

import logging
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from github import Auth, Github, GithubException

from src.config import load_config
from src.fixer import apply_fixes, fix_findings
from src.models import ConfigError, ExitCode, FixerError, ReportFormat, ReporterError, RunnerError, ScanError, ScanResult
from src.reporter import format_github_issues, format_pr_comment, report_findings
from src.runner import run_audit
from src.scanner import scan_github, scan_local
```

Note: `ScanResult` is added to the models import (needed for type annotation in `_build_fix_pr_body`). `subprocess` is added. `from github import Auth, Github, GithubException` is added for `_create_fix_pr`.

### 2. CREATE tests/test_fix_command.py
- operation: CREATE
- reason: Unit tests for the new `fix` CLI command, following the pattern in tests/test_cli.py

#### Imports

```python
"""Tests for the fix command in src/cli module."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.models import (
    AgentConfig,
    ExitCode,
    Finding,
    FixerError,
    FixResult,
    Confidence,
    ScanManifest,
    ScanResult,
    Severity,
)
```

#### Module-level setup

```python
runner = CliRunner()
```

#### Helper functions

Reuse the same helpers from test_cli.py (duplicated here to keep tests self-contained):

- `_make_config(tmp_path: Path) -> AgentConfig`: Same as test_cli.py. Create `auditor_dir = tmp_path / "auditor"`, mkdir, write `(auditor_dir / "main.py").write_text("# stub")`, return `AgentConfig(auditor_path=auditor_dir)`.

- `_make_manifest(tmp_path: Path) -> ScanManifest`: Return `ScanManifest(root_path=tmp_path)`.

- `_make_scan_result(exit_code: ExitCode = ExitCode.ISSUES_FOUND) -> ScanResult`: Return `ScanResult(repo="test/repo", timestamp=datetime.now(UTC), findings_count=1, findings=[Finding(rule_id="ScriptVarUsageRule", severity=Severity.ACTION, message="Use let/const", file_path="app/test.script", line=1)], exit_code=exit_code)`. Note: default is ISSUES_FOUND (not CLEAN) because the fix command is interesting when there ARE findings.

- `_make_fix_results() -> list[FixResult]`: Return `[FixResult(finding=Finding(rule_id="ScriptVarUsageRule", severity=Severity.ACTION, message="Use let/const", file_path="app/test.script", line=1), original_content="var x = 1;", fixed_content="let x = 1;", confidence=Confidence.HIGH)]`.

#### Test Classes and Methods

##### Class: `TestFixArgumentValidation`

- `test_no_path_no_repo_exits_2(self, tmp_path: Path) -> None`:
  Patch `src.cli.load_config` to return `_make_config(tmp_path)`. Invoke `runner.invoke(app, ["fix"])`. Assert `result.exit_code == 2`. Assert `"Must specify either PATH or --repo"` in `result.output`.

- `test_path_and_repo_together_exits_2(self, tmp_path: Path) -> None`:
  Patch `src.cli.load_config`. Invoke `runner.invoke(app, ["fix", str(tmp_path), "--repo", "owner/repo"])`. Assert `result.exit_code == 2`. Assert `"Cannot specify both PATH and --repo"` in `result.output`.

- `test_create_pr_without_repo_exits_2(self, tmp_path: Path) -> None`:
  Patch `src.cli.load_config`. Invoke `runner.invoke(app, ["fix", str(tmp_path), "--create-pr"])`. Assert `result.exit_code == 2`. Assert `"--create-pr requires --repo"` in `result.output`.

- `test_create_pr_without_token_exits_2(self, tmp_path: Path) -> None`:
  Patch `src.cli.load_config` to return `_make_config(tmp_path)` (no token). Invoke `runner.invoke(app, ["fix", "--repo", "owner/repo", "--create-pr"])`. Assert `result.exit_code == 2`. Assert `"GITHUB_TOKEN"` in `result.output`.

- `test_target_dir_and_create_pr_exits_2(self, tmp_path: Path) -> None`:
  Create config with `github_token="fake-token"`: `AgentConfig(auditor_path=tmp_path / "auditor", github_token="fake-token")`. Create auditor stub. Patch `src.cli.load_config`. Invoke `runner.invoke(app, ["fix", "--repo", "owner/repo", "--target-dir", str(tmp_path), "--create-pr"])`. Assert `result.exit_code == 2`. Assert `"Cannot specify both --target-dir and --create-pr"` in `result.output`.

##### Class: `TestFixPipelineLocal`

- `test_clean_scan_exits_0(self, tmp_path: Path) -> None`:
  Patch `load_config`, `scan_local` returning `_make_manifest(tmp_path)`, `run_audit` returning `_make_scan_result(ExitCode.CLEAN)`. Invoke `runner.invoke(app, ["fix", str(tmp_path)])`. Assert `result.exit_code == 0`.

- `test_clean_scan_prints_no_findings(self, tmp_path: Path) -> None`:
  Same patches as above. Assert `"No findings to fix"` in `result.output`.

- `test_fix_findings_called_when_issues_found(self, tmp_path: Path) -> None`:
  Patch `load_config`, `scan_local`, `run_audit` returning `_make_scan_result(ExitCode.ISSUES_FOUND)`, `fix_findings` returning `_make_fix_results()`, `apply_fixes` returning `[Path("app/test.script")]`, and second `scan_local` + second `run_audit` (for re-audit) returning clean result. Invoke `runner.invoke(app, ["fix", str(tmp_path)])`. Assert `fix_findings` was called once with `(scan_result, tmp_path)`.

- `test_no_fixable_findings_prints_message(self, tmp_path: Path) -> None`:
  Patch `load_config`, `scan_local`, `run_audit` returning ISSUES_FOUND, `fix_findings` returning `[]`. Invoke `runner.invoke(app, ["fix", str(tmp_path)])`. Assert `"No auto-fixable findings"` in `result.output`. Assert `result.exit_code == 1`.

- `test_apply_fixes_called_with_target_dir(self, tmp_path: Path) -> None`:
  Create `target = tmp_path / "output"`. Patch all pipeline functions. Invoke `runner.invoke(app, ["fix", str(tmp_path), "--target-dir", str(target)])`. Assert `apply_fixes` was called with `(_make_fix_results(), target)`.

- `test_apply_fixes_called_with_source_dir_when_no_target(self, tmp_path: Path) -> None`:
  Patch all pipeline functions. Invoke `runner.invoke(app, ["fix", str(tmp_path)])`. Assert `apply_fixes` was called with `(_make_fix_results(), tmp_path)`.

- `test_reaudit_runs_after_fix(self, tmp_path: Path) -> None`:
  Patch `load_config`, `scan_local` (called twice -- first for initial scan, second for re-audit), `run_audit` (called twice), `fix_findings`, `apply_fixes`. Use `side_effect` lists for `scan_local` and `run_audit` to return different values on successive calls. Invoke `runner.invoke(app, ["fix", str(tmp_path)])`. Assert `run_audit` was called exactly 2 times.

##### Class: `TestFixExitCodes`

- `test_reaudit_clean_exits_0(self, tmp_path: Path) -> None`:
  Patch so initial audit returns ISSUES_FOUND, fixes are applied, re-audit returns CLEAN. Invoke. Assert `result.exit_code == 0`.

- `test_reaudit_still_issues_exits_1(self, tmp_path: Path) -> None`:
  Patch so initial audit returns ISSUES_FOUND, fixes applied, re-audit returns ISSUES_FOUND. Assert `result.exit_code == 1`.

- `test_scan_error_exits_2(self, tmp_path: Path) -> None`:
  Patch `scan_local` to raise `ScanError("not found")`. Assert `result.exit_code == 2`.

- `test_runner_error_exits_3(self, tmp_path: Path) -> None`:
  Patch `run_audit` to raise `RunnerError("crash")`. Assert `result.exit_code == 3`.

- `test_fixer_error_exits_3(self, tmp_path: Path) -> None`:
  Patch `fix_findings` to raise `FixerError("write fail")`. Assert `result.exit_code == 3`.

##### Class: `TestFixQuietFlag`

- `test_quiet_suppresses_info_messages(self, tmp_path: Path) -> None`:
  Patch full pipeline to produce fixes. Invoke with `--quiet`. Assert `"Applied"` NOT in `result.output`. Assert `"Re-audit"` NOT in `result.output`.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile src/cli.py`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_fix_command.py -v`
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m src.cli fix --help` -- expect exit 0, output contains `--create-pr`, `--target-dir`, and `PATH`

## Constraints
- Do NOT modify src/models.py -- all needed models and exceptions already exist
- Do NOT modify src/fixer.py -- the fix_findings and apply_fixes functions are already complete
- Do NOT modify src/scanner.py or src/runner.py
- Do NOT modify src/reporter.py
- Do NOT modify ARCHITECTURE.md, CLAUDE.md, or IMPL_PLAN.md
- Do NOT add new dependencies to pyproject.toml
- Do NOT modify existing tests in tests/test_cli.py
- Do NOT use `is_flag=True` for boolean Typer options -- use `typer.Option(False, "--flag-name", ...)` pattern
- The `fix` command must NOT accept `--format`, `--output`, or `--pr` flags (those are scan-only)
- The `_create_fix_pr` function must use subprocess git commands (not PyGithub) for git operations (clone is already done by scan_github, so only branch/add/commit/push are needed)
- The `_create_fix_pr` function must use PyGithub only for the `create_pull` API call
- All functions must have Google-style docstrings
- All files must start with `from __future__ import annotations`
