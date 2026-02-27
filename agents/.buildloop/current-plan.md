# Plan: P5.3

## Dependencies
- list: [] (no new packages required; pytest and typer are already in pyproject.toml dev dependencies)
- commands: [] (no install commands needed)

## File Operations (in execution order)

### 1. MODIFY tests/test_cli.py
- operation: MODIFY
- reason: Add integration tests for local fixture scan, JSON/summary format output, and --help; the test for --pr without --repo already exists

#### Pre-modification audit (BUILDER MUST CHECK BEFORE EDITING)

The following test already exists in TestArgumentValidation and MUST NOT be added again:
- `test_pr_without_repo_exits_2` at line 74

Do NOT add any test named `test_pr_without_repo_exits_2` or any test that duplicates:
- "test missing --repo when --pr given returns exit 2"

The existing module-level `runner = CliRunner()` is at line 15. Do NOT redefine it.

#### Imports / Dependencies
Add exactly one import line to the existing import block (after the current `from pathlib import Path` line, before `from unittest.mock import patch`):
```python
import json
```

#### Module-level Constants
Add the following four module-level constants immediately after the existing line `runner = CliRunner()` (line 15). Use `Path(__file__).parent` to construct all paths, not string literals or os.getcwd():

```python
FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
CLEAN_APP_FIXTURE: Path = FIXTURES_DIR / "clean_app"
DIRTY_APP_FIXTURE: Path = FIXTURES_DIR / "dirty_app"
AUDITOR_PATH: Path = Path(__file__).parent.parent.parent  # resolves to ArcaneAuditor/ containing main.py
```

#### Anchor for import insertion
The exact line to insert `import json` after is:
```
from __future__ import annotations
```
Insert `import json` immediately after that line (it must come before the other imports as stdlib comes first, but adding after `from __future__` as a new stdlib import is correct).

Actually, insert `import json` between the existing `import pytest` line and the `from typer.testing import CliRunner` line so it stays grouped with stdlib imports. The exact anchor is:
```
import pytest
from typer.testing import CliRunner
```
Insert `import json` between these two lines.

#### Anchor for constant insertion
The exact line after which to insert the constants block is:
```
runner = CliRunner()
```
Insert the four constant definitions immediately after this line, before the first blank line separating it from `_make_config`.

#### Functions

##### TestIntegrationLocalScan class
Add this class at the END of the file, after the last existing class (`TestConfigPreset`).

```python
# ---------------------------------------------------------------------------
# Integration tests -- real fixture paths, real parent tool
# ---------------------------------------------------------------------------


class TestIntegrationLocalScan:
```

Methods inside this class:

- signature: `def test_scan_clean_fixture_exits_0(self) -> None:`
  - purpose: Verify the full pipeline exits 0 when scanning the clean fixture with no findings
  - logic:
    1. Call `runner.invoke(app, [str(CLEAN_APP_FIXTURE)], env={"ARCANE_AUDITOR_PATH": str(AUDITOR_PATH)})`
    2. Assert `result.exit_code == 0`
  - returns: None (assertion-based)
  - error handling: none; let assertion fail naturally if exit code is wrong

- signature: `def test_scan_dirty_fixture_exits_1(self) -> None:`
  - purpose: Verify the full pipeline exits 1 when scanning the dirty fixture that has ACTION findings
  - logic:
    1. Call `runner.invoke(app, [str(DIRTY_APP_FIXTURE)], env={"ARCANE_AUDITOR_PATH": str(AUDITOR_PATH)})`
    2. Assert `result.exit_code == 1`
  - returns: None
  - error handling: none

- signature: `def test_scan_format_json_produces_valid_json(self) -> None:`
  - purpose: Verify that `--format json` produces stdout that parses as a JSON object
  - logic:
    1. Instantiate `local_runner = CliRunner(mix_stderr=False)` (local variable, not module-level, to get separate stdout/stderr streams so JSON is not contaminated by logging output)
    2. Call `result = local_runner.invoke(app, [str(CLEAN_APP_FIXTURE), "--format", "json", "--quiet"], env={"ARCANE_AUDITOR_PATH": str(AUDITOR_PATH)})`
    3. Assert `result.exit_code == 0`
    4. Call `parsed = json.loads(result.output)`
    5. Assert `isinstance(parsed, dict)`
  - returns: None
  - error handling: none; json.loads raises JSONDecodeError on invalid output which will fail the test

- signature: `def test_scan_format_json_output_has_required_keys(self) -> None:`
  - purpose: Verify that the JSON output from `--format json` contains all required top-level ScanResult fields
  - logic:
    1. Instantiate `local_runner = CliRunner(mix_stderr=False)`
    2. Call `result = local_runner.invoke(app, [str(CLEAN_APP_FIXTURE), "--format", "json", "--quiet"], env={"ARCANE_AUDITOR_PATH": str(AUDITOR_PATH)})`
    3. Assert `result.exit_code == 0`
    4. Call `parsed = json.loads(result.output)`
    5. Assert `parsed.keys() >= {"repo", "timestamp", "findings_count", "findings", "exit_code"}`
  - returns: None
  - error handling: none

- signature: `def test_scan_format_summary_produces_text_output(self) -> None:`
  - purpose: Verify that `--format summary` produces human-readable text containing the "Arcane Auditor" header
  - logic:
    1. Call `result = runner.invoke(app, [str(CLEAN_APP_FIXTURE), "--format", "summary", "--quiet"], env={"ARCANE_AUDITOR_PATH": str(AUDITOR_PATH)})`
    2. Assert `result.exit_code == 0`
    3. Assert `"Arcane Auditor" in result.output`
  - returns: None
  - error handling: none

- signature: `def test_scan_format_summary_contains_total_findings_line(self) -> None:`
  - purpose: Verify the summary format output contains the "Total findings:" line produced by format_summary
  - logic:
    1. Call `result = runner.invoke(app, [str(CLEAN_APP_FIXTURE), "--format", "summary", "--quiet"], env={"ARCANE_AUDITOR_PATH": str(AUDITOR_PATH)})`
    2. Assert `result.exit_code == 0`
    3. Assert `"Total findings:" in result.output`
  - returns: None
  - error handling: none

##### TestHelp class
Add this class at the END of the file, after `TestIntegrationLocalScan`.

```python
# ---------------------------------------------------------------------------
# --help flag
# ---------------------------------------------------------------------------


class TestHelp:
```

Methods inside this class:

- signature: `def test_help_exits_0(self) -> None:`
  - purpose: Verify invoking `--help` exits with code 0
  - logic:
    1. Call `result = runner.invoke(app, ["--help"])`
    2. Assert `result.exit_code == 0`
  - returns: None
  - error handling: none

- signature: `def test_help_output_contains_usage(self) -> None:`
  - purpose: Verify the --help output contains the word "Usage" (standard CLI usage header)
  - logic:
    1. Call `result = runner.invoke(app, ["--help"])`
    2. Assert `"Usage" in result.output`
  - returns: None
  - error handling: none

- signature: `def test_help_output_contains_format_option(self) -> None:`
  - purpose: Verify the --help output documents the --format option (confirms scan command options are shown)
  - logic:
    1. Call `result = runner.invoke(app, ["--help"])`
    2. Assert `"--format" in result.output`
  - returns: None
  - error handling: none

#### Wiring / Integration
- `TestIntegrationLocalScan` uses the module-level `runner = CliRunner()` and locally instantiated `CliRunner(mix_stderr=False)` -- no new module-level state
- `AUDITOR_PATH` resolves to the parent ArcaneAuditor directory the same way `AUDITOR_PATH` is defined in `test_runner.py` (line 15 there: `AUDITOR_PATH: Path = Path(__file__).parent.parent.parent`)
- The `env` kwarg passed to `runner.invoke()` patches `os.environ` for the duration of the call, so `load_config()` in `config.py` will read the patched `ARCANE_AUDITOR_PATH` value via `os.environ.get("ARCANE_AUDITOR_PATH", "")`

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no linter configured; skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_cli.py -v`
- smoke: Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_cli.py::TestIntegrationLocalScan -v` and confirm all 6 tests pass; run `uv run pytest tests/test_cli.py::TestHelp -v` and confirm all 3 pass; confirm total test count increases by 9 vs before the edit

## Constraints
- Do NOT modify `src/cli.py`, `src/models.py`, `src/runner.py`, `src/reporter.py`, `src/scanner.py`, or `src/config.py`
- Do NOT modify `CLAUDE.md`, `ARCHITECTURE.md`, or `IMPL_PLAN.md`
- Do NOT add any new package dependencies to `pyproject.toml`
- Do NOT add a test named `test_pr_without_repo_exits_2` -- it already exists at line 74 of `tests/test_cli.py` in class `TestArgumentValidation`
- Do NOT add a module-level `AUDITOR_PATH` that duplicates an existing definition -- check the file first; as of this plan the file does not yet have it
- The only file to edit is `tests/test_cli.py`
- Do NOT use `os.getcwd()` or string literals for fixture paths -- use `Path(__file__).parent` as shown
- The `CliRunner(mix_stderr=False)` instances in the JSON tests must be instantiated locally inside the test method body, not at module level, to avoid interfering with the existing module-level `runner = CliRunner()` that other test classes rely on
