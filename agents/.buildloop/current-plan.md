# Plan: P2.1

## Dependencies
- list: []
- commands: []
  (All required packages -- pydantic, pathlib -- are stdlib or already in pyproject.toml)

## File Operations (in execution order)

### 1. MODIFY src/models.py
- operation: MODIFY
- reason: Add ScanManifest model; scanner.py will import it from here
- anchor: `class ScanResult(BaseModel):`

#### Imports / Dependencies
No new imports needed. `Path` is already imported from `pathlib`.

#### Structs / Types
Insert the following class **after** the `ScanResult` class block (after line ending with `return self.exit_code == ExitCode.ISSUES_FOUND`) and **before** the `FixResult` class:

```python
class ScanManifest(BaseModel):
    """Result of scanning a local directory for Workday Extend artifacts."""

    root_path: Path
    files_by_type: dict[str, list[Path]] = Field(default_factory=dict)

    @property
    def total_count(self) -> int:
        """Total number of Extend artifact files found across all types."""
        return sum(len(paths) for paths in self.files_by_type.values())
```

Fields:
- `root_path: Path` -- the directory that was scanned (absolute or as-given)
- `files_by_type: dict[str, list[Path]]` -- maps extension string without leading dot (e.g. `"pmd"`, `"pod"`, `"script"`, `"amd"`, `"smd"`) to list of `Path` objects for matching files found under root_path; all five keys are always present even when the list is empty
- `total_count` is a `@property` computed from `files_by_type`, not a stored field, so it cannot drift from the actual data

#### Wiring / Integration
`ScanManifest` must be importable from `src.models`. No other files reference it yet.

---

### 2. CREATE src/scanner.py
- operation: CREATE
- reason: Implements scan_local() per task P2.1

#### Imports / Dependencies
```python
from __future__ import annotations

import logging
from pathlib import Path

from src.models import ScanError, ScanManifest
```

#### Constants
```python
EXTEND_EXTENSIONS: frozenset[str] = frozenset({".pmd", ".pod", ".script", ".amd", ".smd"})
```

Place this constant at module level immediately after the `logger` assignment.

#### Module-level setup
```python
logger = logging.getLogger(__name__)
```

#### Functions

- signature: `def scan_local(path: Path) -> ScanManifest:`
  - purpose: Walk a directory tree recursively and collect all Workday Extend artifact files by extension
  - logic:
    1. Check `path.exists()`. If False, raise `ScanError(f"Path does not exist: {path}")`.
    2. Check `path.is_dir()`. If False, raise `ScanError(f"Path is not a directory: {path}")`.
    3. Initialize `files_by_type: dict[str, list[Path]]` with all five extension keys pre-populated: `{"pmd": [], "pod": [], "script": [], "amd": [], "smd": []}`.
    4. Iterate over every item yielded by `path.rglob("*")`.
    5. For each `item` in the rglob result: call `item.is_file()`. If False, skip (it's a directory entry).
    6. Check `item.suffix` against `EXTEND_EXTENSIONS`. If `item.suffix` is not in `EXTEND_EXTENSIONS`, skip.
    7. Compute `ext_key = item.suffix[1:]` (strips the leading dot, e.g. `".pmd"` becomes `"pmd"`).
    8. Append `item` to `files_by_type[ext_key]`.
    9. After the loop, call `logger.debug("scan_local: root=%s total=%d", path, sum(len(v) for v in files_by_type.values()))`.
    10. Construct and return `ScanManifest(root_path=path, files_by_type=files_by_type)`.
  - calls: `path.exists()`, `path.is_dir()`, `path.rglob("*")`, `item.is_file()`, `ScanManifest(...)`, `logger.debug(...)`
  - returns: `ScanManifest` instance
  - error handling: Raise `ScanError` (imported from `src.models`) for non-existent path and for path that is a file rather than a directory. Do NOT catch exceptions from `path.rglob()` -- let OS errors propagate naturally as they indicate a genuine filesystem problem outside the scanner's control.

#### Docstring (Google style, on the function)
```
"""Walk a directory tree and collect all Workday Extend artifact files by extension.

Args:
    path: Root directory to scan. Must exist and be a directory.

Returns:
    A ScanManifest with root_path, files_by_type keyed by extension (without dot),
    and a computed total_count.

Raises:
    ScanError: If path does not exist or is not a directory.
"""
```

#### Module docstring (top of file, after the future import)
```
"""Find Workday Extend artifact files in a local directory tree."""
```

#### Wiring / Integration
`scanner.py` imports only from `src.models`. No other modules import from `scanner.py` yet (runner.py is a future task).

---

### 3. CREATE tests/test_scanner.py
- operation: CREATE
- reason: Test coverage for scan_local() per project convention (every module gets a test file)

#### Imports / Dependencies
```python
from __future__ import annotations

from pathlib import Path

import pytest

from src.models import ScanError, ScanManifest
from src.scanner import EXTEND_EXTENSIONS, scan_local
```

#### Test cases (all use `tmp_path: Path` pytest fixture -- no pre-created fixture files needed)

**Class `TestScanLocal`:**

1. `test_nonexistent_path_raises_scan_error(tmp_path)`:
   - Call `scan_local(tmp_path / "does_not_exist")`.
   - Assert `pytest.raises(ScanError)` with match `"does not exist"`.

2. `test_file_path_raises_scan_error(tmp_path)`:
   - Create `f = tmp_path / "file.pmd"` and write any text to it.
   - Call `scan_local(f)`.
   - Assert `pytest.raises(ScanError)` with match `"not a directory"`.

3. `test_empty_directory_returns_zero_total(tmp_path)`:
   - Call `result = scan_local(tmp_path)`.
   - Assert `result.total_count == 0`.
   - Assert `result.root_path == tmp_path`.
   - Assert `result.files_by_type == {"pmd": [], "pod": [], "script": [], "amd": [], "smd": []}`.

4. `test_flat_directory_finds_all_extension_types(tmp_path)`:
   - Create one file per extension in `tmp_path`:
     `(tmp_path / "a.pmd").write_text("x")`, `(tmp_path / "b.pod").write_text("x")`,
     `(tmp_path / "c.script").write_text("x")`, `(tmp_path / "d.amd").write_text("x")`,
     `(tmp_path / "e.smd").write_text("x")`.
   - Call `result = scan_local(tmp_path)`.
   - Assert `result.total_count == 5`.
   - Assert `len(result.files_by_type["pmd"]) == 1`.
   - Assert `len(result.files_by_type["pod"]) == 1`.
   - Assert `len(result.files_by_type["script"]) == 1`.
   - Assert `len(result.files_by_type["amd"]) == 1`.
   - Assert `len(result.files_by_type["smd"]) == 1`.

5. `test_nested_directories_are_traversed(tmp_path)`:
   - Create `sub = tmp_path / "level1" / "level2"` and call `sub.mkdir(parents=True)`.
   - Create `(tmp_path / "top.pmd").write_text("x")`.
   - Create `(sub / "deep.pmd").write_text("x")`.
   - Call `result = scan_local(tmp_path)`.
   - Assert `result.total_count == 2`.
   - Assert `len(result.files_by_type["pmd"]) == 2`.

6. `test_non_extend_files_are_ignored(tmp_path)`:
   - Create `(tmp_path / "readme.md").write_text("x")` and `(tmp_path / "config.json").write_text("{}")`.
   - Create `(tmp_path / "app.pmd").write_text("x")`.
   - Call `result = scan_local(tmp_path)`.
   - Assert `result.total_count == 1`.
   - Assert `len(result.files_by_type["pmd"]) == 1`.

7. `test_returns_scan_manifest_instance(tmp_path)`:
   - Call `result = scan_local(tmp_path)`.
   - Assert `isinstance(result, ScanManifest)`.

8. `test_multiple_files_per_type(tmp_path)`:
   - Create three `.pmd` files: `(tmp_path / "a.pmd").write_text("x")`, `(tmp_path / "b.pmd").write_text("x")`, `(tmp_path / "c.pmd").write_text("x")`.
   - Call `result = scan_local(tmp_path)`.
   - Assert `result.total_count == 3`.
   - Assert `len(result.files_by_type["pmd"]) == 3`.

9. `test_extend_extensions_constant_contains_all_types()`:
   - Assert `".pmd" in EXTEND_EXTENSIONS`.
   - Assert `".pod" in EXTEND_EXTENSIONS`.
   - Assert `".script" in EXTEND_EXTENSIONS`.
   - Assert `".amd" in EXTEND_EXTENSIONS`.
   - Assert `".smd" in EXTEND_EXTENSIONS`.
   - Assert `len(EXTEND_EXTENSIONS) == 5`.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.scanner import scan_local; print('import ok')"`
- lint: (no linter configured in pyproject.toml -- skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_scanner.py -v`
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from pathlib import Path; from src.scanner import scan_local; m = scan_local(Path('src')); print(m.total_count, m.files_by_type)"`

## Constraints
- Do NOT add any new entries to `pyproject.toml` -- no new dependencies are needed
- Do NOT modify `src/config.py`, `tests/test_models.py`, or `tests/test_config.py`
- Do NOT create fixture files in `tests/fixtures/` -- all scanner tests use `tmp_path` (pytest built-in)
- Do NOT use `os.walk()` -- use `Path.rglob("*")` exclusively
- Do NOT store `total_count` as a field on ScanManifest -- it must be a `@property` to prevent drift
- Do NOT catch broad exceptions in `scan_local` -- only raise `ScanError` for the two validated preconditions
- The `files_by_type` dict in `scan_local` must pre-populate all five keys before the rglob loop so callers can always access `result.files_by_type["pmd"]` without a KeyError, even when no files of that type were found
