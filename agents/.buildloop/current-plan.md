# Plan: P5.1

## Dependencies
- list: [no new dependencies -- typer>=0.16.1 already in pyproject.toml]
- commands: []

## File Operations (in execution order)

### 1. CREATE src/cli.py
- operation: CREATE
- reason: Entry point for the arcane-agent CLI; wires scan -> runner -> reporter pipeline behind a Typer `scan` command

#### Imports / Dependencies
- `from __future__ import annotations`
- `import logging`
- `import shutil`
- `import sys`
- `from enum import Enum`
- `from pathlib import Path`
- `from typing import Optional`
- `import typer`
- `from src.config import load_config`
- `from src.models import AgentConfig, ConfigError, ExitCode, ReportFormat, ReporterError, RunnerError, ScanError`
- `from src.reporter import format_github_issues, format_pr_comment, report_findings`
- `from src.runner import run_audit`
- `from src.scanner import scan_github, scan_local`

#### Structs / Types

Module-level logger:
```python
logger = logging.getLogger(__name__)
```

CliFormat enum (maps CLI-facing hyphenated values to be used as Typer choices):
```python
class CliFormat(str, Enum):
    JSON = "json"
    SARIF = "sarif"
    SUMMARY = "summary"
    GITHUB_ISSUES = "github-issues"
    PR_COMMENT = "pr-comment"
```

Mapping dict from CliFormat to ReportFormat (module-level constant):
```python
_FORMAT_MAP: dict[CliFormat, ReportFormat] = {
    CliFormat.JSON: ReportFormat.JSON,
    CliFormat.SARIF: ReportFormat.SARIF,
    CliFormat.SUMMARY: ReportFormat.SUMMARY,
    CliFormat.GITHUB_ISSUES: ReportFormat.GITHUB_ISSUES,
    CliFormat.PR_COMMENT: ReportFormat.PR_COMMENT,
}
```

Typer app instance (module-level):
```python
app = typer.Typer(name="arcane-agent", help="Autonomous agent for Arcane Auditor deterministic code review.")
```

#### Functions

- signature: `def _configure_logging(quiet: bool) -> None`
  - purpose: Set up root logger level; WARNING if quiet, INFO otherwise
  - logic:
    1. Compute `level = logging.WARNING if quiet else logging.INFO`
    2. Call `logging.basicConfig(level=level, format="%(levelname)s: %(message)s")`
  - calls: `logging.basicConfig`
  - returns: `None`
  - error handling: none

- signature: `def _error(msg: str) -> None`
  - purpose: Print an error message to stderr unconditionally
  - logic:
    1. Call `typer.echo(f"Error: {msg}", err=True)`
  - calls: `typer.echo`
  - returns: `None`
  - error handling: none

- signature: `@app.command()\ndef scan(path: Optional[Path], repo: Optional[str], pr: Optional[int], format: CliFormat, output: Optional[Path], config: Optional[str], quiet: bool) -> None`
  - purpose: Main CLI command -- validates args, runs scan/audit/report pipeline, writes output, exits with appropriate code
  - Typer parameter declarations (exact, use these as-is):
    ```python
    path: Optional[Path] = typer.Argument(None, help="Local path to scan for Workday Extend artifacts"),
    repo: Optional[str] = typer.Option(None, "--repo", help="GitHub repo in owner/repo format (e.g. acme/payroll)"),
    pr: Optional[int] = typer.Option(None, "--pr", help="GitHub PR number (requires --repo)"),
    format: CliFormat = typer.Option(CliFormat.JSON, "--format", help="Output format: json, sarif, summary, github-issues, pr-comment"),
    output: Optional[Path] = typer.Option(None, "--output", help="Write output to this file path instead of stdout"),
    config: Optional[str] = typer.Option(None, "--config", help="Arcane Auditor config preset name or path (e.g. production-ready)"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress informational messages; only errors go to stderr"),
    ```
  - logic:
    1. Call `_configure_logging(quiet)`.
    2. Call `agent_config = load_config(None)` wrapped in `try/except ConfigError as exc`. On `ConfigError`, call `_error(str(exc))` and `raise typer.Exit(code=int(ExitCode.USAGE_ERROR))`.
    3. If `config is not None`, replace `agent_config` with `agent_config.model_copy(update={"config_preset": config})`.
    4. **Argument validation** -- check all four conditions in order, printing error and raising `typer.Exit(code=int(ExitCode.USAGE_ERROR))` for each:
       - If `path is None and repo is None`: call `_error("Must specify either PATH or --repo")`, raise exit 2.
       - If `path is not None and repo is not None`: call `_error("Cannot specify both PATH and --repo")`, raise exit 2.
       - If `pr is not None and repo is None`: call `_error("--pr requires --repo")`, raise exit 2.
       - If `format == CliFormat.GITHUB_ISSUES and repo is None`: call `_error("--format github-issues requires --repo")`, raise exit 2.
       - If `format == CliFormat.PR_COMMENT and repo is None`: call `_error("--format pr-comment requires --repo")`, raise exit 2.
       - If `format == CliFormat.PR_COMMENT and pr is None`: call `_error("--format pr-comment requires --pr")`, raise exit 2.
    5. Extract token: `token: str = agent_config.github_token.get_secret_value() if agent_config.github_token is not None else ""`.
    6. If `format in (CliFormat.GITHUB_ISSUES, CliFormat.PR_COMMENT) and not token`: call `_error("GitHub token required for --format github-issues / pr-comment; set GITHUB_TOKEN env var")`, raise exit 2.
    7. **Scan phase** -- call the appropriate scanner inside `try/except ScanError as exc`:
       - If `path is not None`: call `manifest = scan_local(path)`.
       - Else: call `manifest = scan_github(repo, "main", token)`.
       - On `ScanError`: call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.USAGE_ERROR))`.
    8. **Audit phase** -- inside `try/except RunnerError as exc` with a `finally` block:
       - In `try`: call `scan_result = run_audit(manifest, agent_config)`.
       - On `RunnerError`: call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`.
       - In `finally`: if `manifest.temp_dir is not None`, call `shutil.rmtree(manifest.temp_dir, ignore_errors=True)`.
    9. **Report phase** -- inside `try/except ReporterError as exc`:
       - If `format == CliFormat.GITHUB_ISSUES`: call `urls = format_github_issues(scan_result, repo, token)`, then set `formatted: str = "\n".join(urls) if urls else "No issues created."`.
       - Elif `format == CliFormat.PR_COMMENT`: call `formatted = format_pr_comment(scan_result, repo, pr, token)`.
       - Else: call `formatted = report_findings(scan_result, _FORMAT_MAP[format])`.
       - On `ReporterError`: call `_error(str(exc))`, raise `typer.Exit(code=int(ExitCode.RUNTIME_ERROR))`.
    10. **Write output**:
        - If `output is not None`: call `output.write_text(formatted, encoding="utf-8")`. Then if `not quiet`, call `typer.echo(f"Output written to {output}", err=True)`.
        - Else: call `typer.echo(formatted)`.
    11. **Exit**: call `raise typer.Exit(code=int(scan_result.exit_code))`.
  - calls: `_configure_logging`, `load_config`, `agent_config.model_copy`, `_error`, `scan_local`, `scan_github`, `run_audit`, `shutil.rmtree`, `format_github_issues`, `format_pr_comment`, `report_findings`, `typer.echo`, `typer.Exit`
  - returns: `None` (exits via `typer.Exit`)
  - error handling: `ConfigError` -> exit 2, `ScanError` -> exit 2, `RunnerError` -> exit 3, `ReporterError` -> exit 3

#### Wiring / Integration
- `pyproject.toml` line 15 already declares `arcane-agent = "src.cli:app"` -- no change needed
- `src/cli.py` imports from `src.config`, `src.models`, `src.reporter`, `src.runner`, `src.scanner` -- all exist
- `app` is the Typer application instance referenced by the entry point

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.cli import app; print('import ok')"`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q`
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m src.cli --help` -- expect Typer usage output showing `scan` command; then `uv run python -m src.cli scan --help` -- expect usage showing `PATH`, `--repo`, `--pr`, `--format`, `--output`, `--config`, `--quiet`

## Constraints
- Do NOT modify `src/models.py`, `src/config.py`, `src/runner.py`, `src/reporter.py`, `src/scanner.py`
- Do NOT modify `pyproject.toml` -- `arcane-agent = "src.cli:app"` is already correct
- Do NOT add new dependencies beyond what is in pyproject.toml
- Do NOT implement a `fix` or `watch` command -- those are Phase 6/7 tasks
- The `--format` choices presented to the user must be `json`, `sarif`, `summary`, `github-issues`, `pr-comment` (hyphenated, not underscored)
- Branch for `scan_github` is hardcoded to `"main"` -- do NOT add a `--branch` option (not in scope for P5.1)
- Temp dir cleanup for `scan_github` results must happen in the `finally` block of the audit phase, not in a separate cleanup step
- Errors must always print to stderr via `typer.echo(..., err=True)` regardless of `--quiet`
- `--quiet` only suppresses the "Output written to ..." informational message, not errors
- Use `logging` module for debug/info logging, never `print()`
