# Review Report — P5.1

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`py_compile` clean; `from src.cli import app` succeeds)
- Tests: PASS (168 passed, 0 failures across full suite)
- Lint: PASS (`ruff check src/cli.py src/__main__.py` -- all checks passed)
- Docker: SKIPPED (no compose files changed in this task)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "src/cli.py",
      "line": 105,
      "issue": "Type contract violation: `repo` is `Optional[str]` at the call site but `scan_github(repo: str, ...)` declares `str`. The validation guards at lines 71-77 prevent None from reaching here at runtime, but mypy strict mode flags this as an error. Per CLAUDE.md: 'Type hints everywhere -- no exceptions.' A future refactor that reorders or removes the guards would silently pass None into the function.",
      "category": "api-contract"
    },
    {
      "file": "src/cli.py",
      "line": 121,
      "issue": "Type contract violation (same root cause): `repo: Optional[str]` passed to `format_github_issues(scan_result, repo: str, token: str)`. Validated non-None by line 83-85 guard, but the type annotation at the call site is wrong. Same issue at line 124 where `repo: Optional[str]` and `pr: Optional[int]` are passed to `format_pr_comment(..., repo: str, pr_number: int, ...)`. Three call sites, same mismatch.",
      "category": "api-contract"
    }
  ],
  "low": [
    {
      "file": "src/__main__.py",
      "line": 1,
      "issue": "Incorrect docstring: says 'Allow running the CLI via `python -m src.cli`.' This file enables `python -m src` (Python invokes src/__main__.py). `python -m src.cli` is a different invocation that runs cli.py directly as __main__.",
      "category": "inconsistency"
    },
    {
      "file": "src/cli.py",
      "line": 139,
      "issue": "Missing `if __name__ == '__main__': app()` guard. The plan's smoke test (`uv run python -m src.cli --help`) silently exits with no output because cli.py never calls app() when run as __main__. Primary invocation paths (`uv run arcane-agent`, `python -m src`) are unaffected.",
      "category": "inconsistency"
    },
    {
      "file": "src/cli.py",
      "line": 34,
      "issue": "_FORMAT_MAP contains dead entries for CliFormat.GITHUB_ISSUES and CliFormat.PR_COMMENT. The `else` branch that calls `_FORMAT_MAP[format]` is only reached when format is not GITHUB_ISSUES and not PR_COMMENT (handled by the if/elif above). The dead entries imply to a reader that those formats could pass through to report_findings(), which would raise ReporterError.",
      "category": "inconsistency"
    },
    {
      "file": "tests/test_cli.py",
      "line": 1,
      "issue": "No tests for the --repo GitHub scanning pipeline: no mocked scan_github call, no mocked format_github_issues or format_pr_comment invocations, and no verification that shutil.rmtree is called in the finally block. The cleanup contract for temp_dir is untested.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "All 168 tests pass including all 26 new test_cli.py tests",
    "Import chain (cli -> config, models, reporter, runner, scanner) resolves cleanly",
    "All 6 argument validation guards emit correct error messages and exit code 2",
    "Exit codes 0/1/2/3 propagate correctly through the pipeline",
    "_configure_logging sets WARNING level when quiet=True, INFO otherwise",
    "_error() always writes to stderr via typer.echo(err=True) regardless of --quiet",
    "--quiet suppresses 'Output written to' message but not errors",
    "--config preset correctly applied via model_copy before run_audit is called",
    "manifest.temp_dir cleanup via shutil.rmtree is in the finally block of the audit phase",
    "Token is extracted via get_secret_value() and empty-string-as-None coercion is handled by AgentConfig validator",
    "CliFormat enum values use hyphenated strings (github-issues, pr-comment) matching CLI requirement",
    "scan_github hardcoded to branch='main' per task constraint",
    "sys import correctly omitted (not needed -- typer.Exit handles process exit)"
  ]
}
```
