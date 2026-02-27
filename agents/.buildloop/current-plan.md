# Plan: P2.2

## Dependencies
- list: []
- commands: []
  (no new packages needed: `subprocess`, `tempfile`, and `shutil` are stdlib)

## Design Decision: Temp Dir Lifecycle

The task spec says "clean up temp dir on completion." However, the runner (P3.1) needs
`scan_manifest.root_path` to exist on disk when it invokes the auditor subprocess.
If `scan_github` cleaned up the temp dir before returning, `root_path` would be a
dangling path and `run_audit` would fail.

Resolution: `scan_github` does NOT clean up internally. Instead, `ScanManifest` gains
an optional `temp_dir: Path | None` field. When set, the caller owns the temp dir and
MUST call `shutil.rmtree(manifest.temp_dir, ignore_errors=True)` after the auditor
finishes. The runner (P3.1) will be planned with this cleanup responsibility in mind.

## File Operations (in execution order)

### 1. MODIFY src/models.py
- operation: MODIFY
- reason: ScanManifest needs `repo`, `branch`, and `temp_dir` fields to carry GitHub
  metadata and allow callers to clean up the cloned temp directory.
- anchor: `    root_path: Path`  (line 94 in ScanManifest class body)

#### Structs / Types
Replace the ScanManifest body from:
```
    root_path: Path
    files_by_type: dict[str, list[Path]] = Field(default_factory=dict)
```
with:
```
    root_path: Path
    files_by_type: dict[str, list[Path]] = Field(default_factory=dict)
    repo: str | None = None
    branch: str | None = None
    temp_dir: Path | None = None
```

All three new fields are optional with `None` default -- no callers of `scan_local` need
to change. `temp_dir` is set only when `scan_github` creates a temp directory; the caller
is responsible for cleanup via `shutil.rmtree(manifest.temp_dir, ignore_errors=True)`.

#### Wiring / Integration
- No other files reference `ScanManifest` field names by string -- the change is purely
  additive and backward-compatible.
- `test_scanner.py` tests that check `result.files_by_type == {...}` are unaffected
  because the new fields have defaults.

---

### 2. MODIFY src/scanner.py
- operation: MODIFY
- reason: Add `scan_github` function that clones a GitHub repo to a temp dir and
  delegates to `scan_local`.
- anchor: `from src.models import ScanError, ScanManifest`  (line 8)

#### Imports / Dependencies
Add these three stdlib imports directly below the existing `from pathlib import Path` line:
```python
import subprocess
import tempfile
import shutil
```
Keep the existing import block order intact (`logging`, `pathlib`, then the new ones,
then `from src.models import ...`).

Final import block in scanner.py:
```python
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from src.models import ScanError, ScanManifest
```

#### Functions

- signature: `def scan_github(repo: str, branch: str, token: str) -> ScanManifest:`
  - purpose: Clone a GitHub repo to a temporary directory, scan for Extend artifacts
    via `scan_local`, and return a `ScanManifest` enriched with repo metadata.
  - docstring (Google style):
    ```
    """Clone a GitHub repo and scan it for Workday Extend artifact files.

    Args:
        repo: Repository in 'owner/repo' format (e.g. 'acme/payroll-extend').
        branch: Branch name to clone (e.g. 'main').
        token: GitHub personal access token for private repos.
               Pass an empty string for public repos.

    Returns:
        A ScanManifest with root_path pointing to the cloned directory,
        files_by_type populated, and repo/branch/temp_dir fields set.
        The caller MUST call shutil.rmtree(manifest.temp_dir, ignore_errors=True)
        after the auditor has finished with root_path.

    Raises:
        ScanError: If repo format is invalid, git clone fails, or the local
                   scan raises ScanError.
    """
    ```
  - logic:
    1. Validate `repo` format: split on `/`, assert `len(parts) == 2` and both parts
       are non-empty strings. If invalid, raise `ScanError(f"Invalid repo format: '{repo}'. Expected 'owner/repo'.")`.
    2. Build `clone_url`:
       - If `token` is a non-empty, non-whitespace string:
         `clone_url = f"https://{token}@github.com/{repo}.git"`
       - Else:
         `clone_url = f"https://github.com/{repo}.git"`
    3. Create a temp directory:
       `tmp_path = Path(tempfile.mkdtemp(prefix="arcane_auditor_"))`
    4. Inside a `try` block, call `subprocess.run` with these exact arguments:
       ```python
       result = subprocess.run(
           ["git", "clone", "--depth=1", "--branch", branch, clone_url, str(tmp_path)],
           capture_output=True,
           text=True,
           check=False,
           timeout=120,
       )
       ```
    5. If `result.returncode != 0`:
       - Raise `ScanError(f"git clone failed for repo '{repo}' branch '{branch}': {result.stderr.strip()}")`.
       - Do NOT include `clone_url` in the error message (it may contain the token).
    6. Call `manifest = scan_local(tmp_path)`. Let `ScanError` propagate unmodified.
    7. Mutate the manifest to set GitHub metadata:
       ```python
       manifest.repo = repo
       manifest.branch = branch
       manifest.temp_dir = tmp_path
       ```
    8. Log at DEBUG level:
       `logger.debug("scan_github: repo=%s branch=%s total=%d tmp=%s", repo, branch, manifest.total_count, tmp_path)`
    9. Return `manifest`.
    10. In an `except Exception as exc` clause (catching anything other than `ScanError`
        that escapes steps 4-6):
        - Re-raise as `ScanError(f"Unexpected error scanning GitHub repo '{repo}': {exc}")` using `from exc`.
        - Note: This outer `except` must NOT catch `ScanError` -- use `except Exception as exc`
          and add `if isinstance(exc, ScanError): raise` as the first line inside it,
          OR use `except (subprocess.TimeoutExpired, OSError) as exc:` to be specific.

    Preferred exception structure (avoids catching ScanError):
    ```python
    try:
        result = subprocess.run(...)   # step 4
        if result.returncode != 0:     # step 5
            raise ScanError(...)
        manifest = scan_local(tmp_path)  # step 6
        manifest.repo = repo             # step 7
        manifest.branch = branch
        manifest.temp_dir = tmp_path
        logger.debug(...)               # step 8
        return manifest                 # step 9
    except ScanError:
        raise
    except subprocess.TimeoutExpired:
        raise ScanError(f"git clone timed out for repo '{repo}' after 120 seconds.")
    except OSError as exc:
        raise ScanError(f"OS error while cloning repo '{repo}': {exc}") from exc
    ```

    Note on cleanup: The `tmp_path` directory is NOT deleted inside `scan_github`.
    It is returned in `manifest.temp_dir` for the caller to remove.

  - calls:
    - `tempfile.mkdtemp(prefix="arcane_auditor_")` -> returns str, convert to Path
    - `subprocess.run(["git", "clone", "--depth=1", "--branch", branch, clone_url, str(tmp_path)], capture_output=True, text=True, check=False, timeout=120)` -> CompletedProcess
    - `scan_local(tmp_path)` -> ScanManifest (may raise ScanError)
  - returns: `ScanManifest` with `repo`, `branch`, `temp_dir` populated
  - error handling:
    - `ScanError` from invalid repo format or git clone failure: raised directly
    - `ScanError` from `scan_local`: re-raised unmodified (via `except ScanError: raise`)
    - `subprocess.TimeoutExpired`: re-raised as `ScanError`
    - `OSError` (e.g., tempfile creation failure): re-raised as `ScanError`

#### Wiring / Integration
- `scan_github` is added after `scan_local` in the file (no changes to `scan_local`).
- `EXTEND_EXTENSIONS` constant remains unchanged.
- `scan_github` is not wired into any other module in this task -- the CLI (P5.2) will
  call it. No `__all__` export list exists in scanner.py so no changes needed there.

---

### 3. MODIFY tests/test_scanner.py
- operation: MODIFY
- reason: Add a `TestScanGithub` test class covering success path, error paths,
  and metadata fields.
- anchor: `class TestScanLocal:` (line 11 -- add the new class AFTER the existing class)

#### Imports / Dependencies
Add these imports at the top of the test file, after the existing imports:
```python
import shutil
from unittest.mock import MagicMock, patch
```

Final import block for tests/test_scanner.py:
```python
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import ScanError, ScanManifest
from src.scanner import EXTEND_EXTENSIONS, scan_github, scan_local
```

#### Test Class: TestScanGithub

Append after the last line of `TestScanLocal`:

```python
class TestScanGithub:
```

Tests to implement (each as a method):

1. **test_invalid_repo_format_raises_scan_error** (no slash):
   - Call `scan_github("noslash", "main", "tok")` without mocking.
   - Assert `ScanError` is raised with message matching `"Invalid repo format"`.

2. **test_invalid_repo_empty_owner_raises_scan_error**:
   - Call `scan_github("/repo", "main", "tok")`.
   - Assert `ScanError` is raised with message matching `"Invalid repo format"`.

3. **test_invalid_repo_empty_name_raises_scan_error**:
   - Call `scan_github("owner/", "main", "tok")`.
   - Assert `ScanError` is raised with message matching `"Invalid repo format"`.

4. **test_git_clone_failure_raises_scan_error** (mock subprocess):
   - Use `@patch("src.scanner.subprocess.run")` decorator.
   - Configure mock to return `MagicMock(returncode=128, stderr="fatal: repo not found")`.
   - Call `scan_github("owner/repo", "main", "tok")`.
   - Assert `ScanError` is raised with message matching `"git clone failed"`.
   - Assert message does NOT contain the token `"tok"`.

5. **test_git_clone_timeout_raises_scan_error**:
   - Use `@patch("src.scanner.subprocess.run")`.
   - Configure mock `side_effect = subprocess.TimeoutExpired(cmd="git", timeout=120)`.
   - Import `subprocess` in the test file for this.
   - Call `scan_github("owner/repo", "main", "tok")`.
   - Assert `ScanError` is raised with message matching `"timed out"`.

6. **test_successful_clone_returns_manifest** (tmp_path fixture + mock subprocess):
   - Use `@patch("src.scanner.subprocess.run")` and `@patch("src.scanner.scan_local")`.
   - Configure subprocess mock: `MagicMock(returncode=0, stderr="")`.
   - Configure scan_local mock: return a real `ScanManifest(root_path=tmp_path, files_by_type={"pmd": [], "pod": [], "script": [], "amd": [], "smd": []})`.
   - Call `manifest = scan_github("owner/repo", "main", "mytoken")`.
   - Assert `manifest.repo == "owner/repo"`.
   - Assert `manifest.branch == "main"`.
   - Assert `manifest.temp_dir is not None`.
   - Assert `isinstance(manifest, ScanManifest)`.
   - Clean up: `shutil.rmtree(manifest.temp_dir, ignore_errors=True)`.

7. **test_token_injected_into_clone_url**:
   - Use `@patch("src.scanner.subprocess.run")` and `@patch("src.scanner.scan_local")`.
   - Configure subprocess mock: `MagicMock(returncode=0)`.
   - Configure scan_local mock: return minimal `ScanManifest(root_path=tmp_path)`.
   - Call `scan_github("owner/repo", "main", "mytoken123")`.
   - Capture `subprocess.run.call_args` and inspect `args[0]` (the command list).
   - Assert `"https://mytoken123@github.com/owner/repo.git"` is in the command list.
   - Clean up temp_dir via `shutil.rmtree`.

8. **test_empty_token_uses_unauthenticated_url**:
   - Same as above but pass `token=""`.
   - Assert clone URL in command does NOT contain `@`.
   - Assert `"https://github.com/owner/repo.git"` is in the command list.
   - Clean up temp_dir.

9. **test_temp_dir_set_on_manifest_and_exists_after_call**:
   - Use `@patch("src.scanner.subprocess.run")` and `@patch("src.scanner.scan_local")`.
   - Configure mocks for success.
   - Call `manifest = scan_github("owner/repo", "main", "")`.
   - Assert `manifest.temp_dir is not None`.
   - Assert `manifest.temp_dir.exists()` is True (temp dir NOT cleaned up by scan_github).
   - Clean up: `shutil.rmtree(manifest.temp_dir, ignore_errors=True)`.

10. **test_scan_local_error_propagates_as_scan_error**:
    - Use `@patch("src.scanner.subprocess.run")` and `@patch("src.scanner.scan_local")`.
    - Configure subprocess mock for success.
    - Configure scan_local mock `side_effect = ScanError("no Extend files")`.
    - Call `scan_github("owner/repo", "main", "")`.
    - Assert `ScanError` is raised with message `"no Extend files"`.
    - Note: temp dir may be left behind in this case (caller never gets manifest).
      This is acceptable for the current task scope; the OS will clean it up.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.scanner import scan_github; print('import ok')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run ruff check src/scanner.py src/models.py tests/test_scanner.py` (skip if ruff not in pyproject.toml)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_scanner.py -v`
- smoke:
  1. Run `uv run python -c "from src.models import ScanManifest; m = ScanManifest(root_path=__import__('pathlib').Path('.')); print(m.repo, m.branch, m.temp_dir)"` and expect `None None None`.
  2. Run `uv run pytest tests/test_scanner.py::TestScanGithub -v` and expect all 10 tests to pass.
  3. Run `uv run pytest tests/test_scanner.py -v` and expect the full test suite (all TestScanLocal + TestScanGithub tests) to pass.

## Constraints
- Do NOT modify `IMPL_PLAN.md`, `CLAUDE.md`, or `ARCHITECTURE.md`.
- Do NOT add any new third-party packages -- only use stdlib (`subprocess`, `tempfile`, `shutil`).
- Do NOT modify `scan_local` -- only add `scan_github` after it.
- Do NOT include the `clone_url` (which may contain the token) in any log message or error string.
- Do NOT use `PyGithub` for the clone operation -- only `subprocess` + `git`.
- Do NOT clean up the temp directory inside `scan_github` -- leave it in `manifest.temp_dir` for the caller.
- Do NOT use `check=True` on the subprocess call -- parse returncode explicitly.
- Do NOT add `from __future__ import annotations` -- it is already line 1 of scanner.py.
- Preserve the existing `model_config = ConfigDict(frozen=True)` on `Finding` -- do NOT add frozen to `ScanManifest`.
- The `ScanManifest` changes must be backward-compatible: all three new fields (`repo`, `branch`, `temp_dir`) must default to `None` so existing `scan_local` callers and existing tests are unaffected.
