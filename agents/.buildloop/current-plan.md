# Plan: P5.1

## Context

`src/cli.py` and `tests/test_cli.py` were created in a WIP commit. Both files appear
substantially complete but the task is not checked off in IMPL_PLAN.md. This plan
describes the required final state of each file so the builder can verify correctness,
fill any gaps, and confirm the test suite passes.

## Dependencies

- list: [typer>=0.16.1, pydantic>=2.0, pygithub>=2.1.1, pyyaml>=6.0]
- commands: ["uv sync --all-extras"]

## File Operations (in execution order)

### 1. MODIFY src/cli.py

- operation: MODIFY
- reason: Verify and complete the WIP implementation of the `scan` command
- anchor: `app = typer.Typer(name="arcane-agent", help="Autonomous agent for Arcane Auditor deterministic code review.")`

#### Imports / Dependencies

```python
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
```

#### Structs / Types

```python
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
```

#### Functions

- signature: `def _configure_logging(quiet: bool) -> None`
  - purpose: Set root logging level to WARNING (quiet=True) or INFO (quiet=False)
  - logic:
    1. Set `level = logging.WARNING if quiet else logging.INFO`
    2. Call `logging.basicConfig(level=level, format="%(levelname)s: %(message)s")`
  - calls: logging.basicConfig
  - returns: None
  - error handling: none

- signature: `def _error(msg: str) -> None`
  - purpose: Write an "Error: <msg>" line to stderr via typer.echo
  - logic:
    1. Call `typer.echo(f"Error: {msg}", err=True)`
  - calls: typer.echo
  - returns: None
  - error handling: none

- signature: `def scan(path: Optional[Path], repo: Optional[str], pr: Optional[int], format: CliFormat, output: Optional[Path], config: Optional[str], quiet: bool) -> None`
  - purpose: Typer command that orchestrates the full scan -> audit -> report pipeline
  - Typer decorators for all parameters:
    - `path`: `typer.Argument(None, help="Local path to scan for Workday Extend artifacts")`
    - `repo`: `typer.Option(None, "--repo", help="GitHub repo in owner/repo format (e.g. acme/payroll)")`
    - `pr`: `typer.Option(None, "--pr", help="GitHub PR number (requires --repo)")`
    - `format`: `typer.Option(CliFormat.JSON, "--format", help="Output format: json, sarif, summary, github-issues, pr-comment")`
    - `output`: `typer.Option(None, "--output", help="Write output to this file path instead of stdout")`
    - `config`: `typer.Option(None, "--config", help="Arcane Auditor config preset name or path (e.g. production-ready)")`
    - `quiet`: `typer.Option(False, "--quiet", help="Suppress informational messages; only errors go to stderr")`
  - logic:
    1. Call `_configure_logging(quiet)`
    2. Call `load_config(None)` in a try block; on `ConfigError`: call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    3. If `config is not None`: call `agent_config.model_copy(update={"config_preset": config})` and reassign to `agent_config`
    4. If `path is None and repo is None`: call `_error("Must specify either PATH or --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    5. If `path is not None and repo is not None`: call `_error("Cannot specify both PATH and --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    6. If `pr is not None and repo is None`: call `_error("--pr requires --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    7. If `format == CliFormat.GITHUB_ISSUES and repo is None`: call `_error("--format github-issues requires --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    8. If `format == CliFormat.PR_COMMENT and repo is None`: call `_error("--format pr-comment requires --repo")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    9. If `format == CliFormat.PR_COMMENT and pr is None`: call `_error("--format pr-comment requires --pr")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    10. Extract token: `token = agent_config.github_token.get_secret_value() if agent_config.github_token is not None else ""`
    11. If `format in (CliFormat.GITHUB_ISSUES, CliFormat.PR_COMMENT) and not token`: call `_error("GitHub token required for --format github-issues / pr-comment; set GITHUB_TOKEN env var")`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    12. In a try block: if `path is not None`, call `scan_local(path)` -> `manifest`; else call `scan_github(repo, "main", token)` -> `manifest`. On `ScanError`: call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    13. In a try/finally block: call `run_audit(manifest, agent_config)` -> `scan_result`. On `RunnerError`: call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`. In `finally`: if `manifest.temp_dir is not None`, call `shutil.rmtree(manifest.temp_dir, ignore_errors=True)`
    14. In a try block:
        - If `format == CliFormat.GITHUB_ISSUES`: call `format_github_issues(scan_result, repo, token)` -> `urls`; set `formatted = "\n".join(urls) if urls else "No issues created."`
        - Elif `format == CliFormat.PR_COMMENT`: call `format_pr_comment(scan_result, repo, pr, token)` -> `formatted`
        - Else: call `report_findings(scan_result, _FORMAT_MAP[format])` -> `formatted`
        - On `ReporterError`: call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`
    15. If `output is not None`: call `output.write_text(formatted, encoding="utf-8")`; if not `quiet`, call `typer.echo(f"Output written to {output}", err=True)`. Else: call `typer.echo(formatted)`
    16. Raise `typer.Exit(code=int(scan_result.exit_code))`
  - calls: _configure_logging, load_config, scan_local, scan_github, run_audit, format_github_issues, format_pr_comment, report_findings, shutil.rmtree, typer.echo, typer.Exit
  - returns: None (Typer exits via typer.Exit)
  - error handling: ConfigError -> exit 2, ScanError -> exit 2, RunnerError -> exit 3, ReporterError -> exit 3

#### Wiring / Integration

- `app = typer.Typer(name="arcane-agent", ...)` is defined at module level
- `scan` is registered on `app` via `@app.command()`
- `src/__main__.py` already imports `app` from `src.cli` and calls `app()` -- no changes needed there
- `pyproject.toml` already has `arcane-agent = "src.cli:app"` as a script entry point -- no changes needed

### 2. MODIFY tests/test_cli.py

- operation: MODIFY
- reason: Verify the WIP test implementation covers all required cases from IMPL_PLAN P5.3
- anchor: `runner = CliRunner()`

#### Imports / Dependencies

```python
from __future__ import annotations
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
import pytest
from typer.testing import CliRunner
from src.cli import app
from src.models import AgentConfig, ExitCode, ScanManifest, ScanResult
```

#### Required test classes and methods

The following test classes and methods MUST be present. Verify each exists in the file.
If any are missing, add them using the mock helpers `_make_config`, `_make_scan_result`,
and `_make_manifest` already defined in the file.

**Helper functions (module-level):**
- `_make_config(tmp_path: Path) -> AgentConfig` -- creates a temp dir with stub main.py, returns AgentConfig with auditor_path pointing to it
- `_make_scan_result(exit_code: ExitCode = ExitCode.CLEAN) -> ScanResult` -- returns minimal clean ScanResult
- `_make_manifest(tmp_path: Path) -> ScanManifest` -- returns ScanManifest with root_path=tmp_path

**class TestArgumentValidation:**
- `test_no_path_no_repo_exits_2` -- invoke `app []`, expect exit_code == 2
- `test_no_path_no_repo_prints_error` -- invoke `app []`, expect "Must specify either PATH or --repo" in output
- `test_path_and_repo_together_exits_2` -- invoke with both path and --repo, expect exit_code == 2
- `test_path_and_repo_together_prints_error` -- expect "Cannot specify both PATH and --repo" in output
- `test_pr_without_repo_exits_2` -- invoke with path + --pr 42, expect exit_code == 2
- `test_pr_without_repo_prints_error` -- expect "--pr requires --repo" in output
- `test_github_issues_format_without_repo_exits_2` -- invoke with path + --format github-issues, expect exit_code == 2
- `test_pr_comment_format_without_repo_exits_2` -- invoke with path + --format pr-comment, expect exit_code == 2
- `test_pr_comment_format_without_pr_exits_2` -- invoke with --repo + --format pr-comment (no --pr), expect exit_code == 2
- `test_pr_comment_format_without_pr_prints_error` -- expect "--format pr-comment requires --pr" in output
- `test_github_issues_without_token_exits_2` -- invoke with --repo + --format github-issues + no token, expect exit_code == 2
- `test_github_issues_without_token_prints_error` -- expect "GITHUB_TOKEN" in output

**class TestConfigError:**
- `test_config_error_exits_2` -- patch load_config to raise ConfigError, expect exit_code == 2
- `test_config_error_message_emitted` -- expect ConfigError message text in output

**class TestPipelineLocalPath:**
- `test_scan_local_called_with_path` -- patch scan_local, verify it is called with the supplied Path
- `test_run_audit_called_with_manifest_and_config` -- verify run_audit called with manifest + config
- `test_report_findings_called_for_json_format` -- verify report_findings is called for default json format
- `test_output_written_to_file` -- pass --output to a tmp file, verify file exists with correct content

**class TestExitCodePropagation:**
- `test_exit_code_clean_is_0` -- scan_result.exit_code == CLEAN -> process exit 0
- `test_exit_code_issues_found_is_1` -- scan_result.exit_code == ISSUES_FOUND -> process exit 1
- `test_scan_error_exits_2` -- ScanError -> exit 2
- `test_runner_error_exits_3` -- RunnerError -> exit 3
- `test_reporter_error_exits_3` -- ReporterError raised by report_findings -> exit 3

**class TestQuietFlag:**
- `test_quiet_suppresses_output_written_message` -- --quiet prevents "Output written to" from appearing
- `test_without_quiet_output_written_message_present` -- without --quiet, "Output written to" appears

**class TestConfigPreset:**
- `test_config_preset_applied_to_agent_config` -- verify --config "production-ready" causes run_audit to receive agent_config.config_preset == "production-ready"

#### Wiring / Integration

- All tests use `typer.testing.CliRunner` (NOT pytest's capsys or subprocess)
- All tests patch `src.cli.load_config` to avoid real filesystem validation
- All tests patch `src.cli.scan_local` or `src.cli.scan_github` to avoid real network/disk calls
- All tests patch `src.cli.run_audit` to avoid invoking the actual Arcane Auditor subprocess
- GitHub format tests patch `src.cli.format_github_issues` or `src.cli.format_pr_comment` to avoid real GitHub API calls

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "import ast, sys; ast.parse(open('src/cli.py').read()); ast.parse(open('tests/test_cli.py').read()); print('syntax OK')"`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_cli.py -v`
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m src --help 2>&1 | grep -q "scan" && echo "scan command registered OK"`

## Constraints

- Do NOT modify src/models.py, src/runner.py, src/scanner.py, src/reporter.py, or src/config.py
- Do NOT modify pyproject.toml or src/__main__.py
- Do NOT add new dependencies beyond those already in pyproject.toml
- Do NOT add a `fix` or `watch` command -- those belong to P7.1 and P7.2
- Do NOT use print() anywhere in src/cli.py -- use typer.echo() for user output and logging module for debug/info
- The `scan` command must call `shutil.rmtree(manifest.temp_dir, ignore_errors=True)` in a `finally` block to clean up GitHub clones even if run_audit raises
- The `--format` default must be `CliFormat.JSON` (not `summary` or any other value)
- The `--quiet` flag must use `typer.Option(False, "--quiet", ...)` -- NOT `is_flag=True` (Typer handles booleans natively)
- All test patches must target `src.cli.<name>` (the imported name in cli.py), NOT the source module path
