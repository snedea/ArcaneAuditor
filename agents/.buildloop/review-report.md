# Review Report — P7.2

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -c "from src.cli import app; print('OK')"` exited 0)
- Tests: PASS (346 passed, 0 failed — all new tests + full regression suite)
- Lint: PASS (ruff reported no issues on changed files)
- Docker: SKIPPED (no compose files changed)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "agents/src/cli.py",
      "line": 441,
      "issue": "_list_open_prs only catches GithubException, but PyGithub raises requests.exceptions.ConnectionError, requests.exceptions.Timeout, and socket.timeout for network-level failures. These are not subclasses of GithubException (confirmed: GithubException MRO is GithubException -> Exception -> BaseException). They propagate uncaught through _list_open_prs, then uncaught through the watch loop's `except WatchError` clause (lines 528-536), crashing the daemon on any transient network error instead of logging a warning and retrying after the interval.",
      "category": "error-handling"
    }
  ],
  "low": [],
  "validated": [
    "All 17 new tests in tests/test_watch_command.py pass",
    "Full 346-test regression suite passes with no failures",
    "src/models.py: SeenPR (frozen=True) and WatchState models are correctly defined; mark_seen mutates the dict in-place (not the frozen SeenPR), which is valid",
    "WatchState dict[int, SeenPR] roundtrip through model_dump_json/model_validate_json correctly coerces string JSON keys back to int",
    "src/cli.py: _load_watch_state correctly handles missing file, corrupt JSON, and repo mismatch — all three return a fresh WatchState",
    "_save_watch_state uses atomic .tmp-then-rename pattern as specified",
    "watch command restores previous SIGINT handler in finally block regardless of how the loop exits",
    "Shutdown flag is set-only (no sys.exit in handler); loop checks flag at every break point before sleep, between PRs, and at top of while",
    "Failed PR processing (ScanError/RunnerError/ReporterError) is caught, logged, and skipped without marking the PR as seen — loop continues to next PR",
    "WatchError from _list_open_prs is caught, logged, and causes a retry-after-interval rather than a crash — but only for GithubException-derived errors (see medium finding)",
    "_DefaultScanGroup.parse_args correctly routes 'watch' as a known command without prepending 'scan'",
    "State save wrapped in OSError catch (lines 549-552) to prevent disk-full from crashing the loop",
    "_process_single_pr uses try/finally to clean up manifest.temp_dir even when run_audit or format_pr_comment raises",
    "watch --help shows all five options (--repo, --interval, --state-file, --config, --quiet) as specified"
  ]
}
```

## Detail on Medium Finding

`requests.exceptions.ConnectionError` and related exceptions are raised by PyGithub for network-level failures (DNS resolution failure, TCP connection refused, read timeout). They are not subclasses of `GithubException`:

```
GithubException MRO: GithubException -> Exception
ConnectionError MRO: ConnectionError -> RequestException -> OSError -> Exception
```

In `_list_open_prs` (line 441), only `GithubException` is caught:

```python
except GithubException as exc:
    raise WatchError(f"GitHub API error listing PRs for {repo!r}: {exc}") from exc
```

In the watch loop (lines 526-536), only `WatchError` is caught:

```python
try:
    open_prs = _list_open_prs(repo, token)
except WatchError as exc:
    ...
```

A `requests.exceptions.ConnectionError` from a transient network blip bypasses both catch clauses, propagates to the outer `try/finally` (line 524/566), restores the signal handler, and then exits the process with an unhandled exception traceback. For a daemon intended to run continuously (cron, GitHub Actions, foundry loop), this means any network hiccup terminates the process entirely rather than waiting `interval` seconds and retrying.
