# Plan: P7.2 -- Already Complete

## Status: ALREADY IMPLEMENTED

Task P7.2 ("Add `watch` command to cli.py") is fully implemented and tested. No build work is required.

## Evidence

### Implementation (all in `src/cli.py`)
- `watch` command: Typer command at line 480 with options `--repo`, `--interval` (default 300), `--state-file`, `--config`, `--quiet`
- `_load_watch_state()`: line 387 -- loads persisted JSON state, handles missing/corrupt/repo-mismatch cases
- `_save_watch_state()`: line 412 -- atomic write via .tmp-then-replace
- `_list_open_prs()`: line 428 -- fetches open PRs via PyGithub, returns `list[tuple[int, str]]`
- `_process_single_pr()`: line 450 -- clones PR branch, runs audit, posts PR comment, cleans up temp dir
- Graceful SIGINT shutdown: lines 509-517 -- sets `shutdown_requested` flag via signal handler, checked at every loop boundary
- 1-second sleep loop for interruptible interval: lines 562-565

### Models (all in `src/models.py`)
- `SeenPR`: line 123 -- frozen Pydantic model with pr_number, comment_url, processed_at
- `WatchState`: line 131 -- repo, seen_prs dict, has_seen(), mark_seen() methods
- `WatchError`: line 201 -- custom exception for watch failures

### Tests (`tests/test_watch_command.py`) -- 17 tests, all passing
- WatchState unit tests: fresh state, mark_seen/has_seen, JSON roundtrip
- _load_watch_state: missing file, valid file, corrupt file, repo mismatch
- _save_watch_state: write and reload
- _list_open_prs: success case, GitHub API error
- _process_single_pr: success, ScanError propagation
- watch CLI: missing token (exit 2), invalid interval (exit 2), processes new PR and skips seen, continues on error, graceful shutdown message

## Verification

- build: `uv sync` (already passing)
- lint: N/A (no changes)
- test: `uv run pytest tests/test_watch_command.py -v` (17 passed in 0.15s)
- smoke: `uv run python -m src.cli watch --help` (should show --repo, --interval, --state-file, --config, --quiet options)

## Constraints

- Do NOT modify any files
- Do NOT create any new files
- Mark this task as complete with zero code changes
