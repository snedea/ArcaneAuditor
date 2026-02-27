# Plan: P2.4

## Dependencies
- list: []
- commands: []
  (No new dependencies. pytest is already in dev group; all imports are stdlib + existing project modules.)

## Pre-flight: Assess Existing Coverage

`tests/test_scanner.py` already exists with substantial `TestScanLocal` and `TestScanGithub` coverage.
The following P2.4 requirements are ALREADY covered by existing tests -- do NOT rewrite or duplicate them:

| Existing test | Covers |
|---|---|
| `test_empty_directory_returns_zero_total` | empty directory graceful handling |
| `test_flat_directory_finds_all_extension_types` | all 5 extension types found (via tmp_path) |
| `test_non_extend_files_are_ignored` | .md and .json ignored (via tmp_path) |
| `test_multiple_files_per_type` | correct count returned |

The following requirements are NOT yet covered and must be added:
1. `scan_local` against the real `tests/fixtures/clean_app/` directory -- exact file counts
2. `scan_local` against the real `tests/fixtures/dirty_app/` directory -- exact file counts
3. `.js` files explicitly ignored (task description names .js specifically)
4. `.py` files explicitly ignored (task description names .py specifically)

## File Operations (in execution order)

### 1. MODIFY tests/test_scanner.py
- operation: MODIFY
- reason: Add 4 missing tests: fixture-based scan tests for both clean_app and dirty_app, and explicit .js/.py exclusion tests
- anchor: `    def test_extend_extensions_constant_contains_all_types(self) -> None:`
  (This is the last method in `TestScanLocal`. New tests are appended after it, before the `TestScanGithub` class.)

#### Imports / Dependencies
No new imports needed. `Path` is already imported. `pytest` is already imported.

#### Fixture Path Constants
Add two module-level constants immediately after the existing imports block (after line 12, before `class TestScanLocal`):

```python
FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
CLEAN_APP_FIXTURE: Path = FIXTURES_DIR / "clean_app"
DIRTY_APP_FIXTURE: Path = FIXTURES_DIR / "dirty_app"
```

Rationale: using `Path(__file__).parent` ensures paths resolve correctly regardless of which directory pytest is invoked from.

#### Functions

- signature: `def test_clean_app_fixture_has_expected_artifact_counts(self) -> None:`
  - purpose: Verify scan_local on the real clean_app fixture returns exactly 3 files across pmd/pod/script with zero amd/smd
  - logic:
    1. Call `scan_local(CLEAN_APP_FIXTURE)` and assign to `result`
    2. Assert `result.total_count == 3`
    3. Assert `len(result.files_by_type["pmd"]) == 1`
    4. Assert `len(result.files_by_type["pod"]) == 1`
    5. Assert `len(result.files_by_type["script"]) == 1`
    6. Assert `len(result.files_by_type["amd"]) == 0`
    7. Assert `len(result.files_by_type["smd"]) == 0`
  - calls: `scan_local(CLEAN_APP_FIXTURE)`
  - returns: `None`
  - error handling: none -- if the fixture doesn't exist, the test will raise ScanError and fail with a clear message

- signature: `def test_clean_app_fixture_paths_are_absolute(self) -> None:`
  - purpose: Verify that paths in files_by_type are Path objects pointing to real files
  - logic:
    1. Call `scan_local(CLEAN_APP_FIXTURE)` and assign to `result`
    2. For each path in `result.files_by_type["pmd"]`: assert `p.is_file()` is True
    3. For each path in `result.files_by_type["pod"]`: assert `p.is_file()` is True
    4. For each path in `result.files_by_type["script"]`: assert `p.is_file()` is True
  - calls: `scan_local(CLEAN_APP_FIXTURE)`
  - returns: `None`
  - error handling: none

- signature: `def test_dirty_app_fixture_has_expected_artifact_counts(self) -> None:`
  - purpose: Verify scan_local on the real dirty_app fixture returns exactly 3 files across pmd/pod/script
  - logic:
    1. Call `scan_local(DIRTY_APP_FIXTURE)` and assign to `result`
    2. Assert `result.total_count == 3`
    3. Assert `len(result.files_by_type["pmd"]) == 1`
    4. Assert `len(result.files_by_type["pod"]) == 1`
    5. Assert `len(result.files_by_type["script"]) == 1`
    6. Assert `len(result.files_by_type["amd"]) == 0`
    7. Assert `len(result.files_by_type["smd"]) == 0`
  - calls: `scan_local(DIRTY_APP_FIXTURE)`
  - returns: `None`
  - error handling: none

- signature: `def test_js_files_are_ignored(self, tmp_path: Path) -> None:`
  - purpose: Verify .js files are not collected (task description explicitly names .js as a non-Extend type to test)
  - logic:
    1. Write `(tmp_path / "app.js").write_text("console.log('hello')")`
    2. Write `(tmp_path / "utils.js").write_text("function foo() {}")`
    3. Write `(tmp_path / "valid.pmd").write_text("x")` -- one Extend file so total_count tests for exact value
    4. Call `scan_local(tmp_path)` and assign to `result`
    5. Assert `result.total_count == 1`
    6. Assert `len(result.files_by_type["pmd"]) == 1`
    7. Verify no .js path appears in any files_by_type list: `assert not any(p.suffix == ".js" for paths in result.files_by_type.values() for p in paths)`
  - calls: `scan_local(tmp_path)`
  - returns: `None`
  - error handling: none

- signature: `def test_py_files_are_ignored(self, tmp_path: Path) -> None:`
  - purpose: Verify .py files are not collected (task description explicitly names .py as a non-Extend type to test)
  - logic:
    1. Write `(tmp_path / "scanner.py").write_text("import os")`
    2. Write `(tmp_path / "models.py").write_text("class Foo: pass")`
    3. Write `(tmp_path / "valid.script").write_text("const x = 1;")` -- one Extend file
    4. Call `scan_local(tmp_path)` and assign to `result`
    5. Assert `result.total_count == 1`
    6. Assert `len(result.files_by_type["script"]) == 1`
    7. Verify no .py path appears in any files_by_type list: `assert not any(p.suffix == ".py" for paths in result.files_by_type.values() for p in paths)`
  - calls: `scan_local(tmp_path)`
  - returns: `None`
  - error handling: none

#### Wiring / Integration
All 6 new methods are added to the `TestScanLocal` class, after the existing `test_extend_extensions_constant_contains_all_types` method and before the closing of the class (before `class TestScanGithub:`).

The two module-level constants (`FIXTURES_DIR`, `CLEAN_APP_FIXTURE`, `DIRTY_APP_FIXTURE`) are inserted after the existing import block (after line 12: `from src.scanner import EXTEND_EXTENSIONS, scan_github, scan_local`) and before line 14: `class TestScanLocal:`.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no linter configured in pyproject.toml -- skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_scanner.py -v`
- smoke: Confirm the output shows all pre-existing tests still pass and the 6 new tests appear as PASSED. Expected new test names:
  - `TestScanLocal::test_clean_app_fixture_has_expected_artifact_counts`
  - `TestScanLocal::test_clean_app_fixture_paths_are_absolute`
  - `TestScanLocal::test_dirty_app_fixture_has_expected_artifact_counts`
  - `TestScanLocal::test_js_files_are_ignored`
  - `TestScanLocal::test_py_files_are_ignored`

## Constraints
- Do NOT modify `TestScanGithub` -- those tests are complete and unrelated to P2.4
- Do NOT rewrite or remove existing `TestScanLocal` tests -- they already pass
- Do NOT modify `src/scanner.py` -- it is correct as-is; this task is tests only
- Do NOT modify `src/models.py`
- Do NOT add any new pip dependencies
- Do NOT create conftest.py -- fixture paths are module-level constants in the test file itself, which is simpler and sufficient
- The 6th test (`test_clean_app_fixture_paths_are_absolute`) is a bonus correctness test; include it -- it costs nothing and catches a real class of bug (returning strings instead of Path objects)
- Fixture count assertions (total_count == 3) are derived from the actual fixture contents:
  - clean_app: minimalPage.pmd, minimalPod.pod, utils.script (3 files, no .amd or .smd)
  - dirty_app: dirtyPage.pmd, dirtyPod.pod, helpers.script (3 files, no .amd or .smd)
  If the fixture directory contents ever change, these assertions must be updated to match
