# Plan: P7.2

## Dependencies
- list: [] (no new packages -- PyGithub, Pydantic, Typer already in pyproject.toml)
- commands: [] (no install commands needed)

## File Operations (in execution order)

### 1. MODIFY src/models.py
- operation: MODIFY
- reason: Add WatchState Pydantic model for tracking seen PRs, and WatchError exception class

#### anchor (insert new model after FixResult class, before the Custom Exceptions section):
```python
class FixResult(BaseModel):
```
and
```python
# --- Custom Exceptions ---
```

#### Imports / Dependencies
No new imports needed. All required imports (BaseModel, Field, Path, datetime) are already present.

#### Structs / Types

```python
class SeenPR(BaseModel):
    """Record of a PR that has already been processed."""
    model_config = ConfigDict(frozen=True)
    pr_number: int
    comment_url: str
    processed_at: datetime
```

```python
class WatchState(BaseModel):
    """Persistent state for the watch command, tracking which PRs have been processed."""
    repo: str
    seen_prs: dict[int, SeenPR] = Field(default_factory=dict)

    def has_seen(self, pr_number: int) -> bool:
        """Check whether a PR number has already been processed."""
        return pr_number in self.seen_prs

    def mark_seen(self, pr_number: int, comment_url: str) -> None:
        """Record a PR as processed."""
        self.seen_prs[pr_number] = SeenPR(
            pr_number=pr_number,
            comment_url=comment_url,
            processed_at=datetime.now(UTC),
        )
```

Add `WatchError` exception after `ConfigError`:

```python
class WatchError(ArcaneAgentError):
    """Raised when the watch polling loop encounters a fatal error."""
```

#### Functions
- No standalone functions in this file change. Methods are defined inline in the model classes above.

#### Wiring / Integration
- `WatchState`, `SeenPR`, and `WatchError` will be imported by `cli.py`

---

### 2. MODIFY src/cli.py
- operation: MODIFY
- reason: Add the `watch` command, helper functions for state file I/O, PR listing, single-PR processing, and the polling loop with SIGINT handling

#### anchor (add imports alongside existing model imports at line 21):
```python
from src.models import ConfigError, ExitCode, FixerError, ReportFormat, ReporterError, RunnerError, ScanError, ScanResult
```

#### anchor (new command goes after the `fix` function, at end of file after line 382)

#### Imports / Dependencies
Add to existing imports at top of file:

```python
import json
import signal
import time
from typing import Any
```

Update the `src.models` import line to include `WatchError`, `WatchState`, `SeenPR`:
```python
from src.models import ConfigError, ExitCode, FixerError, ReportFormat, ReporterError, RunnerError, ScanError, ScanResult, SeenPR, WatchError, WatchState
```

#### Functions

All four helper functions are module-level, defined between the `fix` command and the new `watch` command.

- signature: `def _load_watch_state(state_file: Path, repo: str) -> WatchState`
  - purpose: Load persisted watch state from a JSON file, or return a fresh WatchState if the file does not exist or is corrupt
  - logic:
    1. If `state_file.exists()` is False, return `WatchState(repo=repo)`
    2. Read `state_file.read_text(encoding="utf-8")` into variable `raw`
    3. Call `WatchState.model_validate_json(raw)` inside a try/except block catching `ValueError` and `json.JSONDecodeError`
    4. If the loaded state's `repo` field does not match the `repo` argument, log a warning ("State file repo mismatch: expected {repo}, got {state.repo}. Starting fresh.") and return `WatchState(repo=repo)`
    5. Return the loaded `WatchState`
    6. On exception in step 3, log a warning ("Corrupt state file {state_file}, starting fresh: {exc}") and return `WatchState(repo=repo)`
  - calls: `WatchState.model_validate_json(raw)`, `logger.warning()`
  - returns: `WatchState`
  - error handling: Catches `ValueError` and `json.JSONDecodeError` from Pydantic parse, returns fresh state

- signature: `def _save_watch_state(state: WatchState, state_file: Path) -> None`
  - purpose: Atomically persist watch state to disk as JSON
  - logic:
    1. Serialize state: `data = state.model_dump_json(indent=2)`
    2. Write to a temp file in the same directory: `tmp = state_file.with_suffix(".tmp")`
    3. `tmp.write_text(data, encoding="utf-8")`
    4. `tmp.replace(state_file)` (atomic rename on POSIX)
  - calls: `state.model_dump_json()`, `Path.write_text()`, `Path.replace()`
  - returns: None
  - error handling: Let OSError propagate (caller handles)

- signature: `def _list_open_prs(repo: str, token: str) -> list[tuple[int, str]]`
  - purpose: Fetch all open PRs from GitHub and return a list of (pr_number, head_branch) tuples
  - logic:
    1. Create GitHub client: `with Github(auth=Auth.Token(token)) as gh:`
    2. `repo_obj = gh.get_repo(repo)`
    3. `pulls = repo_obj.get_pulls(state="open", sort="created", direction="desc")`
    4. Build result list: `[(pr.number, pr.head.ref) for pr in pulls]`
    5. Return the list
  - calls: `Github()`, `gh.get_repo()`, `repo_obj.get_pulls()`
  - returns: `list[tuple[int, str]]`
  - error handling: Catch `GithubException`, re-raise as `WatchError(f"GitHub API error listing PRs for {repo!r}: {exc}")`

- signature: `def _process_single_pr(repo: str, pr_number: int, head_branch: str, token: str, agent_config: AgentConfig, quiet: bool) -> str`
  - purpose: Clone the PR head branch, run the audit, post a PR comment, and return the comment URL
  - logic:
    1. Log info: `logger.info("Processing PR #%d (branch: %s)", pr_number, head_branch)`
    2. Call `manifest = scan_github(repo, head_branch, token)`
    3. Wrap remaining logic in try/finally to clean up `manifest.temp_dir`
    4. In try: call `scan_result = run_audit(manifest, agent_config)`
    5. Call `comment_url = format_pr_comment(scan_result, repo, pr_number, token)`
    6. Return `comment_url`
    7. In finally: `if manifest.temp_dir is not None: shutil.rmtree(manifest.temp_dir, ignore_errors=True)`
  - calls: `scan_github()`, `run_audit()`, `format_pr_comment()`, `shutil.rmtree()`
  - returns: `str` (the comment HTML URL)
  - error handling: Let `ScanError`, `RunnerError`, `ReporterError` propagate to caller. The finally block always cleans up the temp dir.

Then the Typer command itself:

- signature: `@app.command()\ndef watch(repo: str = typer.Option(..., "--repo", help="GitHub repo in owner/repo format (e.g. acme/payroll)"), interval: int = typer.Option(300, "--interval", help="Polling interval in seconds"), state_file: Path = typer.Option(Path(".arcane-watch-state.json"), "--state-file", help="Path to the JSON state file for tracking seen PRs"), config: Optional[str] = typer.Option(None, "--config", help="Arcane Auditor config preset name or path"), quiet: bool = typer.Option(False, "--quiet", help="Suppress informational messages; only errors go to stderr")) -> None`
  - purpose: Poll a GitHub repo for new PRs, audit each one, and post a PR comment with findings
  - logic:
    1. Call `_configure_logging(quiet)`
    2. Load config: try `agent_config = load_config(None)`, catch `ConfigError` -> `_error(str(exc))` then `raise typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    3. If `config is not None`: `agent_config = agent_config.model_copy(update={"config_preset": config})`
    4. Extract token: `token = agent_config.github_token.get_secret_value() if agent_config.github_token is not None else ""`
    5. Validate token: if not token, call `_error("watch requires a GitHub token; set GITHUB_TOKEN env var")` then `raise typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    6. Validate interval: if `interval < 1`, call `_error("--interval must be >= 1")` then `raise typer.Exit(code=int(ExitCode.USAGE_ERROR))`
    7. Set up shutdown flag: `shutdown_requested = False`
    8. Define inner function `def _handle_sigint(signum: int, frame: Any) -> None:` that sets `nonlocal shutdown_requested = True` and logs `logger.warning("Shutdown requested, finishing current cycle...")`
    9. Store previous handler: `previous_handler = signal.getsignal(signal.SIGINT)`
    10. Install signal handler: `signal.signal(signal.SIGINT, _handle_sigint)`
    11. Load state: `state = _load_watch_state(state_file, repo)`
    12. If not quiet: `typer.echo(f"Watching {repo} for new PRs (interval: {interval}s, state: {state_file})", err=True)`
    13. Begin `try:` block wrapping the main loop
    14. `while not shutdown_requested:`
        a. Try `open_prs = _list_open_prs(repo, token)`, catch `WatchError` as exc -> `_error(str(exc))`, then if `shutdown_requested` break, else sleep and continue
        b. Filter: `new_prs = [(num, branch) for num, branch in open_prs if not state.has_seen(num)]`
        c. If `new_prs` and not quiet: `typer.echo(f"Found {len(new_prs)} new PR(s): {', '.join(f'#{n}' for n, _ in new_prs)}", err=True)`
        d. For each `(pr_number, head_branch)` in `new_prs`:
            i. If `shutdown_requested`: break out of inner loop
            ii. Try: `comment_url = _process_single_pr(repo, pr_number, head_branch, token, agent_config, quiet)`
            iii. Call `state.mark_seen(pr_number, comment_url)`
            iv. Call `_save_watch_state(state, state_file)`
            v. If not quiet: `typer.echo(f"PR #{pr_number}: {comment_url}", err=True)`
            vi. Except `(ScanError, RunnerError, ReporterError)` as exc: log warning `logger.warning("Failed to process PR #%d: %s", pr_number, exc)` and continue to next PR (do NOT mark as seen)
        e. If `shutdown_requested`: break
        f. Sleep in 1-second increments to remain responsive to SIGINT: `for _ in range(interval): if shutdown_requested: break; time.sleep(1)`
    15. After loop exits (either `shutdown_requested` or exception):
    16. `finally:` block: `signal.signal(signal.SIGINT, previous_handler)`
    17. If not quiet: `typer.echo("Watch stopped.", err=True)`
    18. `raise typer.Exit(code=0)`
  - calls: `_configure_logging()`, `load_config()`, `_load_watch_state()`, `_list_open_prs()`, `_process_single_pr()`, `_save_watch_state()`, `_error()`, `signal.signal()`, `time.sleep()`
  - returns: None (exits via `typer.Exit`)
  - error handling: WatchError from PR listing is caught and logged (non-fatal, continues polling). ScanError/RunnerError/ReporterError from individual PR processing is caught and logged (non-fatal, skips that PR). ConfigError during startup is fatal (exit 2). Missing token is fatal (exit 2).

#### Wiring / Integration
- The `watch` command is registered on the existing `app` Typer instance via `@app.command()` decorator, same as `scan` and `fix`
- The `_DefaultScanGroup.parse_args` only routes unknown subcommands to `scan` -- `watch` is a known command and will be routed correctly
- The command reuses `scan_github` from `src.scanner`, `run_audit` from `src.runner`, `format_pr_comment` from `src.reporter`, and `load_config` from `src.config` -- no changes needed to those modules

---

### 3. CREATE tests/test_watch_command.py
- operation: CREATE
- reason: Test the watch command's argument validation, state file I/O, PR listing, single-PR processing, and the polling loop

#### Imports / Dependencies
```python
from __future__ import annotations

import json
import signal
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from typer.testing import CliRunner

from src.cli import _list_open_prs, _load_watch_state, _process_single_pr, _save_watch_state, app
from src.models import (
    AgentConfig,
    ExitCode,
    Finding,
    ReporterError,
    RunnerError,
    ScanError,
    ScanManifest,
    ScanResult,
    SeenPR,
    Severity,
    WatchError,
    WatchState,
)
```

#### Structs / Types
```python
runner = CliRunner()
```

#### Functions -- Helper factories

- signature: `def _make_config(tmp_path: Path) -> AgentConfig`
  - purpose: Return an AgentConfig with a valid auditor_path stub and a fake GitHub token
  - logic:
    1. `auditor_dir = tmp_path / "auditor"`
    2. `auditor_dir.mkdir()`
    3. `(auditor_dir / "main.py").write_text("# stub")`
    4. Return `AgentConfig(auditor_path=auditor_dir, github_token="ghp_fake_test_token")`
  - returns: `AgentConfig`

- signature: `def _make_scan_result(exit_code: ExitCode = ExitCode.ISSUES_FOUND) -> ScanResult`
  - purpose: Return a ScanResult with one finding for use in mocked pipelines
  - logic: Return `ScanResult(repo="test/repo", timestamp=datetime.now(UTC), findings_count=1, findings=[Finding(rule_id="ScriptVarUsageRule", severity=Severity.ACTION, message="Use let/const", file_path="app/test.script", line=1)], exit_code=exit_code)`
  - returns: `ScanResult`

#### Functions -- WatchState model tests

- signature: `def test_watch_state_fresh() -> None`
  - purpose: Verify a fresh WatchState has empty seen_prs
  - logic:
    1. `state = WatchState(repo="owner/repo")`
    2. Assert `state.seen_prs == {}`
    3. Assert `state.has_seen(1) is False`

- signature: `def test_watch_state_mark_and_check() -> None`
  - purpose: Verify mark_seen and has_seen work correctly
  - logic:
    1. `state = WatchState(repo="owner/repo")`
    2. `state.mark_seen(42, "https://github.com/owner/repo/pull/42#comment-1")`
    3. Assert `state.has_seen(42) is True`
    4. Assert `state.has_seen(43) is False`
    5. Assert `state.seen_prs[42].pr_number == 42`
    6. Assert `state.seen_prs[42].comment_url == "https://github.com/owner/repo/pull/42#comment-1"`

- signature: `def test_watch_state_roundtrip() -> None`
  - purpose: Verify WatchState serializes to JSON and deserializes back identically
  - logic:
    1. Create state, mark PR 10 as seen
    2. `raw = state.model_dump_json(indent=2)`
    3. `loaded = WatchState.model_validate_json(raw)`
    4. Assert `loaded.repo == state.repo`
    5. Assert `loaded.has_seen(10) is True`

#### Functions -- _load_watch_state tests

- signature: `def test_load_watch_state_no_file(tmp_path: Path) -> None`
  - purpose: Verify loading from nonexistent file returns fresh state
  - logic:
    1. `state = _load_watch_state(tmp_path / "missing.json", "owner/repo")`
    2. Assert `state.repo == "owner/repo"`
    3. Assert `state.seen_prs == {}`

- signature: `def test_load_watch_state_valid_file(tmp_path: Path) -> None`
  - purpose: Verify loading from a valid JSON file restores state
  - logic:
    1. Create a WatchState, mark PR 5 as seen
    2. Write `state.model_dump_json()` to `tmp_path / "state.json"`
    3. `loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")`
    4. Assert `loaded.has_seen(5) is True`

- signature: `def test_load_watch_state_corrupt_file(tmp_path: Path) -> None`
  - purpose: Verify loading from a corrupt file returns fresh state
  - logic:
    1. Write `"not valid json {{{" ` to `tmp_path / "state.json"`
    2. `loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")`
    3. Assert `loaded.repo == "owner/repo"`
    4. Assert `loaded.seen_prs == {}`

- signature: `def test_load_watch_state_repo_mismatch(tmp_path: Path) -> None`
  - purpose: Verify loading a state file for a different repo returns fresh state
  - logic:
    1. Create `WatchState(repo="other/repo")`, mark PR 1 seen
    2. Write to `tmp_path / "state.json"`
    3. `loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")`
    4. Assert `loaded.repo == "owner/repo"`
    5. Assert `loaded.seen_prs == {}`

#### Functions -- _save_watch_state tests

- signature: `def test_save_watch_state(tmp_path: Path) -> None`
  - purpose: Verify state is written as valid JSON and can be reloaded
  - logic:
    1. Create WatchState, mark PR 7 seen
    2. `_save_watch_state(state, tmp_path / "state.json")`
    3. Assert `(tmp_path / "state.json").exists()`
    4. `loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")`
    5. Assert `loaded.has_seen(7) is True`

#### Functions -- _list_open_prs tests

- signature: `def test_list_open_prs_success() -> None`
  - purpose: Verify _list_open_prs returns (number, branch) tuples from GitHub API
  - logic:
    1. Create mock PR objects: `mock_pr1 = MagicMock()`, `mock_pr1.number = 1`, `mock_pr1.head.ref = "feature-a"`; same for mock_pr2 with number=2, head.ref="feature-b"
    2. Patch `src.cli.Github` as mock_github_cls
    3. Set up: `mock_gh = MagicMock()`, `mock_github_cls.return_value.__enter__ = MagicMock(return_value=mock_gh)`, `mock_github_cls.return_value.__exit__ = MagicMock(return_value=False)`
    4. `mock_gh.get_repo.return_value.get_pulls.return_value = [mock_pr1, mock_pr2]`
    5. Call `result = _list_open_prs("owner/repo", "fake-token")`
    6. Assert `result == [(1, "feature-a"), (2, "feature-b")]`

- signature: `def test_list_open_prs_github_error() -> None`
  - purpose: Verify GithubException is wrapped in WatchError
  - logic:
    1. Patch `src.cli.Github` so `get_repo` raises `GithubException(500, "error", {})`
    2. With `pytest.raises(WatchError)`: call `_list_open_prs("owner/repo", "fake-token")`

#### Functions -- _process_single_pr tests

- signature: `def test_process_single_pr_success(tmp_path: Path) -> None`
  - purpose: Verify the full scan -> audit -> comment pipeline for a single PR
  - logic:
    1. Create `agent_config = _make_config(tmp_path)`
    2. Patch `src.cli.scan_github` to return `ScanManifest(root_path=tmp_path, temp_dir=tmp_path / "clone")`; create that dir
    3. Patch `src.cli.run_audit` to return `_make_scan_result()`
    4. Patch `src.cli.format_pr_comment` to return `"https://github.com/owner/repo/pull/1#comment-1"`
    5. Call `url = _process_single_pr("owner/repo", 1, "feature-a", "fake-token", agent_config, False)`
    6. Assert `url == "https://github.com/owner/repo/pull/1#comment-1"`
    7. Assert `scan_github` called with `("owner/repo", "feature-a", "fake-token")`
    8. Assert `format_pr_comment` called with `(scan_result, "owner/repo", 1, "fake-token")`

- signature: `def test_process_single_pr_scan_error_cleans_up(tmp_path: Path) -> None`
  - purpose: Verify temp dir is cleaned up even when scan_github raises
  - logic:
    1. Patch `src.cli.scan_github` to raise `ScanError("clone failed")`
    2. With `pytest.raises(ScanError)`: call `_process_single_pr(...)`

#### Functions -- CLI argument validation tests

- signature: `def test_watch_missing_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None`
  - purpose: Verify watch exits with code 2 when GITHUB_TOKEN is not set
  - logic:
    1. `monkeypatch.delenv("GITHUB_TOKEN", raising=False)`
    2. Patch `src.cli.load_config` to return `AgentConfig(auditor_path=tmp_path)`
    3. `result = runner.invoke(app, ["watch", "--repo", "owner/repo"])`
    4. Assert `result.exit_code == 2`
    5. Assert `"GitHub token"` in `result.output` or `result.stderr` (Typer writes to output in CliRunner)

- signature: `def test_watch_invalid_interval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None`
  - purpose: Verify watch exits with code 2 when interval < 1
  - logic:
    1. Patch `src.cli.load_config` to return `_make_config(tmp_path)`
    2. `result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "0"])`
    3. Assert `result.exit_code == 2`
    4. Assert `"--interval must be >= 1"` in result output

#### Functions -- Polling loop integration test

- signature: `def test_watch_processes_new_pr_and_skips_seen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None`
  - purpose: Verify the watch loop processes unseen PRs, posts comments, saves state, and skips seen PRs on next cycle
  - logic:
    1. Create state_file at `tmp_path / "state.json"`
    2. Create a call_count variable in a list `[0]` to track how many times `_list_open_prs` is called
    3. Patch `src.cli.load_config` to return `_make_config(tmp_path)`
    4. Patch `src.cli._list_open_prs` to return `[(1, "feature-a")]` and increment call_count. On the 2nd call, trigger shutdown by calling `signal.raise_signal(signal.SIGINT)` then return `[(1, "feature-a")]` again
    5. Patch `src.cli._process_single_pr` to return `"https://comment-url"`
    6. Patch `src.cli.time.sleep` to be a no-op (so the test does not actually sleep)
    7. `result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "1", "--state-file", str(state_file)])`
    8. Assert `result.exit_code == 0`
    9. Assert `_process_single_pr` was called exactly once (PR #1 processed on first cycle, skipped on second because it was marked seen)
    10. Assert state_file exists and contains PR 1

- signature: `def test_watch_continues_on_pr_processing_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None`
  - purpose: Verify the watch loop logs errors for individual PR failures but continues processing remaining PRs
  - logic:
    1. Patch `src.cli.load_config` to return `_make_config(tmp_path)`
    2. Patch `src.cli._list_open_prs`: first call returns `[(1, "feat-a"), (2, "feat-b")]`, second call triggers shutdown
    3. Patch `src.cli._process_single_pr` with a side_effect: first call raises `RunnerError("audit failed")`, second call returns `"https://comment-url"`
    4. Patch `src.cli.time.sleep` to no-op
    5. `result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "1", "--state-file", str(tmp_path / "state.json")])`
    6. Assert `result.exit_code == 0`
    7. Load state file: assert PR 1 is NOT in seen_prs (failed), PR 2 IS in seen_prs (succeeded)

- signature: `def test_watch_graceful_shutdown_message(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None`
  - purpose: Verify "Watch stopped." is printed on graceful shutdown
  - logic:
    1. Patch `src.cli.load_config` to return `_make_config(tmp_path)`
    2. Patch `src.cli._list_open_prs`: immediately trigger shutdown via `signal.raise_signal(signal.SIGINT)`, return `[]`
    3. Patch `src.cli.time.sleep` to no-op
    4. `result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "1", "--state-file", str(tmp_path / "state.json")])`
    5. Assert `result.exit_code == 0`
    6. Assert `"Watch stopped."` in result.output

#### Wiring / Integration
- This test file imports directly from `src.cli` and `src.models`
- All GitHub API calls are mocked via `unittest.mock.patch`
- All subprocess/filesystem calls are mocked
- Signal handling in tests uses `signal.raise_signal(signal.SIGINT)` to simulate Ctrl+C
- Tests use `tmp_path` pytest fixture for state files

---

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.cli import app; print('OK')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile src/models.py && uv run python -m py_compile src/cli.py`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_watch_command.py -v`
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m src.cli watch --help` (should show --repo, --interval, --state-file, --config, --quiet options)
- regression: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -v --tb=short` (all existing tests must still pass)

## Constraints
- Do NOT modify src/scanner.py, src/runner.py, src/reporter.py, src/fixer.py, or src/config.py
- Do NOT modify ARCHITECTURE.md, CLAUDE.md, or IMPL_PLAN.md
- Do NOT add new dependencies to pyproject.toml (everything needed is already available)
- Do NOT use asyncio or threading -- the watch loop is synchronous with time.sleep
- Do NOT use `print()` -- use `typer.echo()` for user output and `logger` for debug/info/warning
- The signal handler must NOT call sys.exit() or raise SystemExit -- it only sets a flag. The main loop checks the flag and exits cleanly
- State file writes must be atomic (write to .tmp then rename) to avoid corruption if SIGINT arrives during write
- Individual PR processing failures must NOT crash the loop -- catch and log, then continue to next PR
- The `_DefaultScanGroup` class on line 45 must NOT be modified -- it already handles routing correctly for known subcommands
- Use `from __future__ import annotations` as the first import in the new test file (matching project convention)
