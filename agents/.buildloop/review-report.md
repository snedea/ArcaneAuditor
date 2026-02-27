# Review Report — P7.1

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`python -m py_compile` on all changed files)
- Tests: PASS (329/329 passed; 28 tests in test_fix_command.py, 35 in test_cli.py)
- Lint: PASS (`ruff check src/cli.py` -- no issues)
- Docker: SKIPPED (no compose files changed)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "src/cli.py",
      "line": "85-86",
      "issue": "PR body lists absolute temp dir paths for fixed files instead of repo-relative paths. `written_files` comes from `apply_fixes(fix_results, manifest.root_path)` where `manifest.root_path` is a temp clone dir like `/tmp/arcane_auditor_XXXXX`. `apply_fixes` returns `dest = target_dir / candidate` (absolute). These absolute paths are rendered verbatim in the PR body under '### Fixed Files'. Every `--create-pr` run produces a PR body with meaningless temp paths (e.g. `/tmp/arcane_auditor_abc/app/test.script`) instead of repo-relative paths (`app/test.script`). No test checks the PR body content -- `TestCreateFixPrFunction::test_happy_path_returns_pr_url` only asserts the return URL.",
      "category": "logic"
    },
    {
      "file": "src/cli.py",
      "line": "138",
      "issue": "GitHub token embedded as cleartext in the GIT_ASKPASS temp Python script: `askpass_f.write(f'print({token!r})\\n')`. The token value is written directly into the file content. `scan_github` (scanner.py:98-103) uses the safer pattern: the shell script reads `$GIT_TOKEN` from the subprocess environment -- the token never appears in the file. The `_create_fix_pr` implementation is inconsistent with the established project pattern and leaves the token value as a string literal on disk for the lifetime of the push.",
      "category": "security"
    },
    {
      "file": "src/cli.py",
      "line": "153-165",
      "issue": "`except GithubException` inside `_create_fix_pr` does not cover `requests.*` exceptions that PyGithub propagates on network failures (e.g. `requests.exceptions.ConnectionError`, `requests.exceptions.Timeout`). These escape as unhandled exceptions, propagate past the `except FixerError` guard in `fix()` at line 370, and cause a crash traceback instead of a clean `FixerError` error message and exit code 3.",
      "category": "error-handling"
    }
  ],
  "low": [
    {
      "file": ".buildloop/current-plan.md",
      "line": "4-32",
      "issue": "Plan claims '18/18 tests passed' and lists TestFixArgumentValidation as '5 tests (lines 82-121)'. Actual test_fix_command.py has 28 tests: TestFixArgumentValidation has 6 tests (6th at line 125-130), plus TestFixCreatePr (3 tests, lines 363-418) and TestCreateFixPrFunction (6 tests, lines 426-504) are not mentioned in the plan at all. The test count discrepancy is purely documentation -- all 28 tests pass.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "All 329 tests pass including 28 tests in test_fix_command.py and 35 in test_cli.py",
    "All changed Python files compile cleanly (py_compile)",
    "ruff reports no lint errors on src/cli.py",
    "fix command registered at cli.py:259 with correct Typer bool option pattern (typer.Option(False, '--create-pr')) -- no is_flag=True misuse",
    "Mutual exclusion guards enforced: --target-dir + --create-pr (line 301), --repo without output destination (line 305), --create-pr without --repo (line 291), --create-pr without token (line 297)",
    "Temp clone cleanup in outer finally block (cli.py:379-381) is exception-safe and fires on typer.Exit propagation",
    "GIT_ASKPASS temp file is cleaned up in its own finally block (cli.py:145-149) even on push failure",
    "Re-audit failure is non-fatal: falls back to original scan exit code (cli.py:377)",
    "assert repo is not None narrowing added before scan_github call (cli.py:315) -- correct pattern vs pre-existing scan command"
  ]
}
```
