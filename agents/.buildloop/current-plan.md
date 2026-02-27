# Plan: P2.2

## Status
Implementation is ALREADY COMPLETE in scanner.py and test_scanner.py (WIP commit 08b8200).
Builder's job: run the tests to verify they pass, then mark P2.2 done in IMPL_PLAN.md.
No new code needs to be written.

## Dependencies
- list: []
- commands: []

## File Operations (in execution order)

### 1. VERIFY src/scanner.py
- operation: VERIFY (no changes expected)
- reason: scan_github was added in the WIP commit; verify the implementation is correct before marking done
- anchor: `def scan_github(repo: str, branch: str, token: str) -> ScanManifest:`

#### Functions
- signature: `scan_github(repo: str, branch: str, token: str) -> ScanManifest`
  - purpose: Clone a GitHub repo to a temp directory, delegate to scan_local, return ScanManifest with repo metadata
  - logic:
    1. Split `repo` on `/`. If `len(parts) != 2` or either part is empty, raise `ScanError(f"Invalid repo format: '{repo}'. Expected 'owner/repo'.")`
    2. Set `clone_url = f"https://github.com/{repo}.git"` (never embed token in URL -- token visible in ps aux)
    3. Copy `os.environ` to `env`. Set `env["GIT_TERMINAL_PROMPT"] = "0"` to prevent git from hanging on interactive prompt.
    4. If `token` is truthy (non-empty after strip): create a temp shell script via `tempfile.mkstemp` that `echo`s the token. chmod it to `stat.S_IRWXU`. Set `env["GIT_ASKPASS"] = str(askpass_path)`. This keeps the token out of argv.
    5. Create temp clone dir via `tempfile.mkdtemp(prefix="arcane_auditor_")`. Assign to `tmp_path = Path(...)`.
    6. Inside a try block: call `subprocess.run(["git", "clone", "--depth=1", "--branch", branch, clone_url, str(tmp_path)], capture_output=True, text=True, check=False, timeout=120, env=env)`.
    7. If `result.returncode != 0`: raise `ScanError(f"git clone failed for repo '{repo}' branch '{branch}': {result.stderr.strip()}")`. Token must NOT appear in this message.
    8. Call `manifest = scan_local(tmp_path)`.
    9. Set `manifest.repo = repo`, `manifest.branch = branch`, `manifest.temp_dir = tmp_path`.
    10. Log at DEBUG: `"scan_github: repo=%s branch=%s total=%d tmp=%s"`.
    11. Return `manifest`.
    12. In except blocks: re-raise `ScanError` as-is; convert `subprocess.TimeoutExpired` to `ScanError("git clone timed out for repo '{repo}' after 120 seconds.")`; convert `OSError` to `ScanError(f"OS error while cloning repo '{repo}': {exc}")`.
    13. In `finally` block: if `askpass_path is not None`, call `askpass_path.unlink(missing_ok=True)` to remove the temp credential script.
  - calls: `scan_local(tmp_path)`, `subprocess.run(...)`, `tempfile.mkstemp(...)`, `tempfile.mkdtemp(...)`
  - returns: `ScanManifest` with `root_path`, `files_by_type`, `repo`, `branch`, `temp_dir` all populated
  - error handling:
    - Invalid repo format -> `ScanError`
    - git clone nonzero exit -> `ScanError` (stderr included, token excluded)
    - `subprocess.TimeoutExpired` -> `ScanError` with "timed out" in message
    - `OSError` -> `ScanError`
    - `ScanError` from `scan_local` -> re-raised unchanged
    - NOTE: temp_dir is NOT removed by this function on error or success. The caller (runner or CLI) is responsible for calling `shutil.rmtree(manifest.temp_dir, ignore_errors=True)` after the runner has finished reading from `root_path`. This is intentional: the runner needs the cloned files to be present when it invokes the auditor subprocess.

#### Design Note on Cleanup
The task spec says "Clean up temp dir on completion." This means the orchestration layer (CLI/runner) cleans up after the full audit pipeline completes -- NOT inside scan_github. Cleaning up inside scan_github before returning would delete the files the runner needs. The docstring in scanner.py explicitly documents this contract. No change is needed.

### 2. VERIFY tests/test_scanner.py
- operation: VERIFY (no changes expected)
- reason: TestScanGithub was added in the WIP commit; confirm coverage matches the implementation contract
- anchor: `class TestScanGithub:`

Confirm these 8 tests exist and match the implementation:
1. `test_invalid_repo_format_raises_scan_error` -- "noslash" -> ScanError("Invalid repo format")
2. `test_invalid_repo_empty_owner_raises_scan_error` -- "/repo" -> ScanError
3. `test_invalid_repo_empty_name_raises_scan_error` -- "owner/" -> ScanError
4. `test_git_clone_failure_raises_scan_error` -- returncode=128, assert "tok" NOT in error message
5. `test_git_clone_timeout_raises_scan_error` -- TimeoutExpired side effect -> ScanError("timed out")
6. `test_successful_clone_returns_manifest` -- returncode=0, assert manifest.repo/branch/temp_dir set
7. `test_token_passed_via_askpass_not_in_url` -- token not in argv, clone_url has no @, GIT_ASKPASS in env
8. `test_empty_token_uses_unauthenticated_url` -- empty token, no @ in github.com URL in argv
9. `test_temp_dir_set_on_manifest_and_exists_after_call` -- temp_dir is not None and exists after return
10. `test_scan_local_error_propagates_as_scan_error` -- scan_local raises ScanError, it propagates

All 10 tests listed above should be present. Count them in the file. If any are missing, add them.

### 3. MODIFY IMPL_PLAN.md
- operation: MODIFY
- reason: Mark P2.2 as complete now that implementation and tests are verified
- anchor: `- [ ] P2.2: Add scan_github(repo: str, branch: str, token: str) to scanner.py`

#### Change
Replace the exact line:
```
- [ ] P2.2: Add scan_github(repo: str, branch: str, token: str) to scanner.py -- clone a GitHub repo to a temp directory using subprocess git clone (not pygithub), then delegate to scan_local. Clean up temp dir on completion. Return ScanManifest with repo metadata
```
With:
```
- [x] P2.2: Add scan_github(repo: str, branch: str, token: str) to scanner.py -- clone a GitHub repo to a temp directory using subprocess git clone (not pygithub), then delegate to scan_local. Clean up temp dir on completion. Return ScanManifest with repo metadata
```

## Verification
- build: `uv run python -c "from src.scanner import scan_github, scan_local; print('imports ok')"` (expect: "imports ok")
- lint: `uv run python -m py_compile src/scanner.py && echo 'syntax ok'`
- test: `uv run pytest tests/test_scanner.py -v`
- smoke: Confirm all 10 tests in TestScanGithub pass. The TestScanLocal tests must also still pass (no regressions). Expected output contains "10 passed" for TestScanGithub tests.

## Constraints
- Do NOT modify src/models.py -- ScanManifest already has repo, branch, temp_dir fields
- Do NOT add any new dependencies to pyproject.toml -- scan_github uses only stdlib (os, stat, subprocess, tempfile, pathlib)
- Do NOT add shutil import to scanner.py -- shutil.rmtree is the caller's responsibility, not the scanner's
- Do NOT change the cleanup design -- temp_dir must persist after scan_github returns so the runner can use the files
- Do NOT modify any file other than IMPL_PLAN.md (and only the checkbox change)
- Do NOT rewrite the existing implementation -- only verify it matches the spec above
