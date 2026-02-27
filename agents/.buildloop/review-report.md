# Review Report — P2.2

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -m py_compile src/scanner.py` — syntax ok)
- Tests: PASS (19/19 passed — 9 TestScanLocal + 10 TestScanGithub)
- Lint: PASS (`uv run ruff check src/scanner.py` — all checks passed)
- Docker: SKIPPED (no Docker files changed in this task)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "src/scanner.py",
      "line": 96,
      "issue": "tempfile.mkstemp() is called at line 96 and tempfile.mkdtemp() at line 105, both BEFORE the try: block that starts at line 106. The except OSError handler at line 127 can only catch OSErrors raised inside the try block. If /tmp is full, /tmp permissions are wrong, or any other OS-level failure occurs in mkstemp or mkdtemp, the exception propagates as a raw OSError -- not ScanError. Any caller that follows the documented contract (catching ScanError for all failure modes) will experience an unhandled exception and crash. The plan's error-handling spec says 'OSError -> ScanError' but the current try-block placement only covers the subprocess.run call, not the tempfile allocation calls.",
      "category": "crash"
    }
  ],
  "low": [
    {
      "file": "src/scanner.py",
      "line": 99,
      "issue": "The GIT_ASKPASS script ignores its $1 argument (the prompt string from git) and always echoes $GIT_TOKEN regardless of whether git is asking for a username or password. The correct pattern checks $1: return 'x-access-token' for a Username prompt and the token for a Password prompt. The current behavior works for GitHub PAT auth in practice (GitHub validates the password/token and ignores the username), but is non-standard and could fail with stricter host configurations or future git versions that validate the username more strictly.",
      "category": "inconsistency"
    },
    {
      "file": "src/scanner.py",
      "line": 95,
      "issue": "token.strip() is evaluated for the truthy check at line 95, but the original unstripped token value is written to env[\"GIT_TOKEN\"] at line 103. A token with leading or trailing whitespace would pass the truthy check but include the whitespace when passed to git via the askpass script, likely causing auth failure.",
      "category": "inconsistency"
    },
    {
      "file": "tests/test_scanner.py",
      "line": 99,
      "issue": "Three failure-path tests (test_git_clone_failure_raises_scan_error at line 99, test_git_clone_timeout_raises_scan_error at line 106, test_scan_local_error_propagates_as_scan_error at line 164) do not mock tempfile.mkdtemp. Each test run creates a real directory in /tmp via mkdtemp that is never removed (ScanError is raised before a manifest is returned, so the caller has no temp_dir to clean up). This is consistent with the documented design limitation but pollutes /tmp across test runs.",
      "category": "resource-leak"
    }
  ],
  "validated": [
    "All 19 tests pass: 9 TestScanLocal and all 10 TestScanGithub tests specified in the plan are present and passing",
    "Token never appears in the git clone URL (clone_url uses plain https://github.com/{repo}.git) or in the ScanError message on clone failure",
    "GIT_TERMINAL_PROMPT=0 is set in env to prevent git from hanging on interactive credential prompts",
    "GIT_ASKPASS temp script is cleaned up unconditionally in the finally block (line 129-131) on all code paths",
    "ScanManifest.repo, .branch, and .temp_dir are all set before returning the manifest (lines 118-120)",
    "ScanManifest is mutable in Pydantic v2 (no frozen=True in models.py), so direct attribute assignment at lines 118-120 is valid",
    "subprocess.run uses capture_output=True, text=True, check=False, timeout=120 matching the project convention in CLAUDE.md",
    "P2.2 is correctly marked [x] in IMPL_PLAN.md line 14",
    "No new imports or dependencies added beyond stdlib (os, stat, subprocess, tempfile, pathlib) -- pyproject.toml unchanged",
    "scan_local ScanError propagates unchanged via except ScanError: raise (line 123-124)",
    "subprocess.TimeoutExpired is converted to ScanError with 'timed out' in the message (line 125-126)"
  ]
}
```
