# Plan: P3.3

## Dependencies
- list: []
- commands: []
  (All dependencies already present: pytest, pydantic, subprocess in stdlib, unittest.mock in stdlib)

## Pre-step: Verify expected/dirty_app.json ordering against real tool output

Before writing the test file, the builder MUST run the parent tool against the dirty_app fixture and capture its actual JSON output. The known-patterns record shows that a previous builder wrote expected/dirty_app.json with findings starting with ScriptMagicNumberRule, but the actual tool output starts with ScriptConsoleLogRule. The current file at tests/fixtures/expected/dirty_app.json still starts with ScriptMagicNumberRule, which is the guessed (wrong) order.

**Run this command from `/Users/name/homelab/ArcaneAuditor/` (the parent tool's directory):**
```
cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/dirty_app --format json --quiet
```

Capture the full JSON output. Extract the `findings` array. Compare it against `agents/tests/fixtures/expected/dirty_app.json`.

If the ordering differs, overwrite `tests/fixtures/expected/dirty_app.json` with the actual tool output (pretty-printed, 2-space indent). The file format must be:
```json
{
  "exit_code": 1,
  "findings": [ ... actual output in tool order ... ]
}
```

Also run against clean_app to confirm it still exits 0 with zero findings:
```
cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/clean_app --format json --quiet
```

Verify exit code is 0 and the JSON has `"findings": []`.

NOTE: Even if expected/dirty_app.json is updated, the tests in test_runner.py must use **order-independent** assertions (set membership checks on rule_id and file_path), NOT ordered list comparison. This prevents the same class of failure from occurring again.

## File Operations (in execution order)

### 1. CREATE tests/test_runner.py
- operation: CREATE
- reason: P3.3 requires tests for run_audit covering clean_app (exit 0), dirty_app (exit 1, specific findings), timeout, and invalid path (exit 2/RunnerError)

#### Imports / Dependencies
```python
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import AgentConfig, ExitCode, RunnerError, ScanManifest, ScanResult, Severity
from src.runner import run_audit
```

#### Module-level constants
```python
FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
CLEAN_APP_FIXTURE: Path = FIXTURES_DIR / "clean_app"
DIRTY_APP_FIXTURE: Path = FIXTURES_DIR / "dirty_app"
# Path(__file__) is agents/tests/test_runner.py
# .parent       is agents/tests/
# .parent.parent is agents/
# .parent.parent.parent is ArcaneAuditor/ (the parent tool root with main.py)
AUDITOR_PATH: Path = Path(__file__).parent.parent.parent
```

#### Module-level fixtures

```python
@pytest.fixture(scope="module")
def clean_config() -> AgentConfig:
    """AgentConfig pointing at the real parent Arcane Auditor tool."""
    return AgentConfig(auditor_path=AUDITOR_PATH)
```
- purpose: Shared AgentConfig for all integration tests; avoids repeating the constructor
- logic:
  1. Instantiate AgentConfig with auditor_path=AUDITOR_PATH and all other fields at their defaults
  2. Note: validate_config() is NOT called here (that's load_config's job); AgentConfig.__init__ has no path-existence check
  3. Return the instance
- returns: `AgentConfig`
- error handling: None; will fail at fixture collection time if AgentConfig constructor raises (it won't with a valid Path)

```python
@pytest.fixture(scope="module")
def clean_result(clean_config: AgentConfig) -> ScanResult:
    """Run real parent tool against clean_app fixture once per module."""
    manifest = ScanManifest(root_path=CLEAN_APP_FIXTURE)
    return run_audit(manifest, clean_config)
```
- purpose: Integration test fixture; runs the real parent tool exactly once for all clean_app tests
- logic:
  1. Create ScanManifest with root_path=CLEAN_APP_FIXTURE and all other fields at defaults
  2. Call run_audit(manifest, clean_config) and return the result
- returns: `ScanResult`
- error handling: None; if run_audit raises, the test is marked as an error (desired behavior)

```python
@pytest.fixture(scope="module")
def dirty_result(clean_config: AgentConfig) -> ScanResult:
    """Run real parent tool against dirty_app fixture once per module."""
    manifest = ScanManifest(root_path=DIRTY_APP_FIXTURE)
    return run_audit(manifest, clean_config)
```
- purpose: Integration test fixture; runs the real parent tool exactly once for all dirty_app tests
- logic:
  1. Create ScanManifest with root_path=DIRTY_APP_FIXTURE and all other fields at defaults
  2. Call run_audit(manifest, clean_config) and return the result
- returns: `ScanResult`
- error handling: None; if run_audit raises, the test is marked as an error (desired behavior)

#### Class: TestRunAuditCleanApp

Class signature: `class TestRunAuditCleanApp:`

All methods receive `clean_result: ScanResult` as a fixture parameter.

**test_returns_scan_result_instance**
- signature: `def test_returns_scan_result_instance(self, clean_result: ScanResult) -> None:`
- purpose: Verify run_audit returns a ScanResult for clean_app
- logic:
  1. Assert `isinstance(clean_result, ScanResult)` is True

**test_exit_code_is_clean**
- signature: `def test_exit_code_is_clean(self, clean_result: ScanResult) -> None:`
- purpose: Verify clean_app produces exit code 0
- logic:
  1. Assert `clean_result.exit_code == ExitCode.CLEAN`

**test_findings_count_is_zero**
- signature: `def test_findings_count_is_zero(self, clean_result: ScanResult) -> None:`
- purpose: Verify findings_count field is 0 for clean_app
- logic:
  1. Assert `clean_result.findings_count == 0`

**test_findings_list_is_empty**
- signature: `def test_findings_list_is_empty(self, clean_result: ScanResult) -> None:`
- purpose: Verify findings list is empty for clean_app
- logic:
  1. Assert `clean_result.findings == []`

**test_has_issues_is_false**
- signature: `def test_has_issues_is_false(self, clean_result: ScanResult) -> None:`
- purpose: Verify the has_issues property returns False for clean_app
- logic:
  1. Assert `clean_result.has_issues is False`

**test_repo_field_matches_path**
- signature: `def test_repo_field_matches_path(self, clean_result: ScanResult) -> None:`
- purpose: Verify repo field is set to the path string when no repo name is in the manifest
- logic:
  1. Assert `str(CLEAN_APP_FIXTURE) in clean_result.repo`
  (runner.py:74 sets repo = str(scan_manifest.root_path) when manifest.repo is None)

#### Class: TestRunAuditDirtyApp

Class signature: `class TestRunAuditDirtyApp:`

All methods receive `dirty_result: ScanResult` as a fixture parameter.

**test_returns_scan_result_instance**
- signature: `def test_returns_scan_result_instance(self, dirty_result: ScanResult) -> None:`
- purpose: Verify run_audit returns a ScanResult for dirty_app
- logic:
  1. Assert `isinstance(dirty_result, ScanResult)` is True

**test_exit_code_is_issues_found**
- signature: `def test_exit_code_is_issues_found(self, dirty_result: ScanResult) -> None:`
- purpose: Verify dirty_app produces exit code 1
- logic:
  1. Assert `dirty_result.exit_code == ExitCode.ISSUES_FOUND`

**test_has_issues_is_true**
- signature: `def test_has_issues_is_true(self, dirty_result: ScanResult) -> None:`
- purpose: Verify the has_issues property returns True for dirty_app
- logic:
  1. Assert `dirty_result.has_issues is True`

**test_findings_count_matches_findings_list_length**
- signature: `def test_findings_count_matches_findings_list_length(self, dirty_result: ScanResult) -> None:`
- purpose: Verify findings_count field equals len(findings)
- logic:
  1. Assert `dirty_result.findings_count == len(dirty_result.findings)`

**test_findings_count_is_eleven**
- signature: `def test_findings_count_is_eleven(self, dirty_result: ScanResult) -> None:`
- purpose: Verify exactly 11 findings are returned
  (from expected/dirty_app.json: 2x ScriptMagicNumberRule + 2x ScriptVarUsageRule + ScriptDeadCodeRule + ScriptConsoleLogRule + ScriptStringConcatRule + EndpointFailOnStatusCodesRule + EndpointBaseUrlTypeRule + HardcodedWorkdayAPIRule + WidgetIdRequiredRule = 11)
- logic:
  1. Assert `dirty_result.findings_count == 11`  # dirtyPage.pmd + dirtyPod.pod + helpers.script

**test_contains_script_console_log_finding**
- signature: `def test_contains_script_console_log_finding(self, dirty_result: ScanResult) -> None:`
- purpose: Verify ScriptConsoleLogRule ACTION finding is present in dirty_app results
- logic:
  1. Create `rule_ids = {f.rule_id for f in dirty_result.findings}`
  2. Assert `"ScriptConsoleLogRule" in rule_ids`

**test_script_console_log_finding_is_action_severity**
- signature: `def test_script_console_log_finding_is_action_severity(self, dirty_result: ScanResult) -> None:`
- purpose: Verify ScriptConsoleLogRule finding has ACTION severity
- logic:
  1. Filter: `matches = [f for f in dirty_result.findings if f.rule_id == "ScriptConsoleLogRule"]`
  2. Assert `len(matches) == 1`
  3. Assert `matches[0].severity == Severity.ACTION`
  4. Assert `matches[0].file_path == "dirtyPage.pmd"`

**test_contains_endpoint_fail_on_status_codes_finding**
- signature: `def test_contains_endpoint_fail_on_status_codes_finding(self, dirty_result: ScanResult) -> None:`
- purpose: Verify EndpointFailOnStatusCodesRule ACTION finding is present
- logic:
  1. Filter: `matches = [f for f in dirty_result.findings if f.rule_id == "EndpointFailOnStatusCodesRule"]`
  2. Assert `len(matches) == 1`
  3. Assert `matches[0].severity == Severity.ACTION`
  4. Assert `matches[0].file_path == "dirtyPod.pod"`

**test_contains_hardcoded_workday_api_finding**
- signature: `def test_contains_hardcoded_workday_api_finding(self, dirty_result: ScanResult) -> None:`
- purpose: Verify HardcodedWorkdayAPIRule ACTION finding is present
- logic:
  1. Filter: `matches = [f for f in dirty_result.findings if f.rule_id == "HardcodedWorkdayAPIRule"]`
  2. Assert `len(matches) == 1`
  3. Assert `matches[0].severity == Severity.ACTION`
  4. Assert `matches[0].file_path == "dirtyPod.pod"`

**test_contains_widget_id_required_finding**
- signature: `def test_contains_widget_id_required_finding(self, dirty_result: ScanResult) -> None:`
- purpose: Verify WidgetIdRequiredRule ACTION finding is present
- logic:
  1. Filter: `matches = [f for f in dirty_result.findings if f.rule_id == "WidgetIdRequiredRule"]`
  2. Assert `len(matches) == 1`
  3. Assert `matches[0].severity == Severity.ACTION`
  4. Assert `matches[0].file_path == "dirtyPage.pmd"`

**test_action_findings_count_is_four**
- signature: `def test_action_findings_count_is_four(self, dirty_result: ScanResult) -> None:`
- purpose: Verify exactly 4 ACTION-severity findings
  (ScriptConsoleLogRule + EndpointFailOnStatusCodesRule + HardcodedWorkdayAPIRule + WidgetIdRequiredRule = 4)
- logic:
  1. Assert `dirty_result.action_count == 4`

**test_advice_findings_count_is_seven**
- signature: `def test_advice_findings_count_is_seven(self, dirty_result: ScanResult) -> None:`
- purpose: Verify exactly 7 ADVICE-severity findings
  (2x ScriptMagicNumberRule + 2x ScriptVarUsageRule + ScriptDeadCodeRule + ScriptStringConcatRule + EndpointBaseUrlTypeRule = 7)
- logic:
  1. Assert `dirty_result.advice_count == 7`

**test_var_usage_findings_in_correct_files**
- signature: `def test_var_usage_findings_in_correct_files(self, dirty_result: ScanResult) -> None:`
- purpose: Verify ScriptVarUsageRule findings appear in both dirtyPage.pmd and helpers.script
- logic:
  1. Filter: `matches = [f for f in dirty_result.findings if f.rule_id == "ScriptVarUsageRule"]`
  2. Assert `len(matches) == 2`
  3. Create: `file_paths = {f.file_path for f in matches}`
  4. Assert `"dirtyPage.pmd" in file_paths`
  5. Assert `"helpers.script" in file_paths`

**test_script_dead_code_finding_in_helpers**
- signature: `def test_script_dead_code_finding_in_helpers(self, dirty_result: ScanResult) -> None:`
- purpose: Verify ScriptDeadCodeRule finding is in helpers.script
- logic:
  1. Filter: `matches = [f for f in dirty_result.findings if f.rule_id == "ScriptDeadCodeRule"]`
  2. Assert `len(matches) == 1`
  3. Assert `matches[0].file_path == "helpers.script"`

#### Class: TestRunAuditTimeout

Class signature: `class TestRunAuditTimeout:`

**test_timeout_raises_runner_error**
- signature: `def test_timeout_raises_runner_error(self) -> None:`
- purpose: Verify subprocess.TimeoutExpired is caught and re-raised as RunnerError
- logic:
  1. Build manifest: `manifest = ScanManifest(root_path=CLEAN_APP_FIXTURE)`
  2. Build config: `config = AgentConfig(auditor_path=AUDITOR_PATH)`
  3. Use `with patch("src.runner.subprocess.run") as mock_run:`
  4. Set: `mock_run.side_effect = subprocess.TimeoutExpired(cmd="uv", timeout=300)`
  5. Use `with pytest.raises(RunnerError, match="timed out"):`
  6. Call `run_audit(manifest, config)` inside that context manager
- error handling: pytest.raises catches RunnerError; match="timed out" validates the message (runner.py:43 raises RunnerError with "timed out after 300 seconds")
- returns: `None`

**test_timeout_error_message_includes_path**
- signature: `def test_timeout_error_message_includes_path(self) -> None:`
- purpose: Verify the RunnerError message includes the path that timed out
- logic:
  1. Build manifest: `manifest = ScanManifest(root_path=CLEAN_APP_FIXTURE)`
  2. Build config: `config = AgentConfig(auditor_path=AUDITOR_PATH)`
  3. Use `with patch("src.runner.subprocess.run") as mock_run:`
  4. Set: `mock_run.side_effect = subprocess.TimeoutExpired(cmd="uv", timeout=300)`
  5. Use `with pytest.raises(RunnerError) as exc_info:`
  6. Call `run_audit(manifest, config)` inside that context manager
  7. Assert `str(CLEAN_APP_FIXTURE) in str(exc_info.value)`
- returns: `None`

#### Class: TestRunAuditInvalidPath

Class signature: `class TestRunAuditInvalidPath:`

**test_exit_code_2_raises_runner_error**
- signature: `def test_exit_code_2_raises_runner_error(self) -> None:`
- purpose: Verify that when parent tool exits 2 (usage error), RunnerError is raised
- logic:
  1. Build manifest: `manifest = ScanManifest(root_path=Path("/nonexistent/fake/path"))`
  2. Build config: `config = AgentConfig(auditor_path=AUDITOR_PATH)`
  3. Use `with patch("src.runner.subprocess.run") as mock_run:`
  4. Set: `mock_run.return_value = MagicMock(returncode=2, stdout="Error: path not found", stderr="")`
  5. Use `with pytest.raises(RunnerError, match="usage error"):`
  6. Call `run_audit(manifest, config)` inside that context manager
  (runner.py:53-57 raises RunnerError with "usage error (exit 2)" when returncode==2)
- returns: `None`

**test_exit_code_2_error_message_includes_path**
- signature: `def test_exit_code_2_error_message_includes_path(self) -> None:`
- purpose: Verify the RunnerError message includes the invalid path for debugging
- logic:
  1. Build manifest: `manifest = ScanManifest(root_path=Path("/nonexistent/fake/path"))`
  2. Build config: `config = AgentConfig(auditor_path=AUDITOR_PATH)`
  3. Use `with patch("src.runner.subprocess.run") as mock_run:`
  4. Set: `mock_run.return_value = MagicMock(returncode=2, stdout="Error: path not found", stderr="")`
  5. Use `with pytest.raises(RunnerError) as exc_info:`
  6. Call `run_audit(manifest, config)` inside that context manager
  7. Assert `"/nonexistent/fake/path" in str(exc_info.value)`
  (runner.py:54 includes `scan_manifest.root_path` in the error string)
- returns: `None`

**test_exit_code_2_with_stderr_message**
- signature: `def test_exit_code_2_with_stderr_message(self) -> None:`
- purpose: Verify the RunnerError message includes the tool's stderr output
- logic:
  1. Build manifest: `manifest = ScanManifest(root_path=Path("/nonexistent/fake/path"))`
  2. Build config: `config = AgentConfig(auditor_path=AUDITOR_PATH)`
  3. Use `with patch("src.runner.subprocess.run") as mock_run:`
  4. Set: `mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="usage: main.py [OPTIONS]")`
  5. Use `with pytest.raises(RunnerError) as exc_info:`
  6. Call `run_audit(manifest, config)` inside that context manager
  7. Assert `"usage: main.py [OPTIONS]" in str(exc_info.value)`
  (runner.py:55-56: error includes `stdout.strip() or stderr.strip()`, so stderr appears when stdout is empty)
- returns: `None`

#### Wiring / Integration
- `tests/test_runner.py` imports `run_audit` from `src.runner` directly
- `AgentConfig(auditor_path=AUDITOR_PATH)` is used without calling `load_config()` or `validate_config()`, bypassing the path-existence check (intentional for unit tests)
- Module-scoped fixtures `clean_result` and `dirty_result` invoke the real parent tool; they are NOT mocked
- Timeout and invalid-path tests use `patch("src.runner.subprocess.run")` to mock at the module where subprocess is used (per unittest.mock best practices: patch the name in the module under test, not in stdlib)

### 2. MODIFY tests/fixtures/expected/dirty_app.json (conditional)
- operation: MODIFY (only if tool output order differs from current file)
- reason: Current file starts with ScriptMagicNumberRule but actual tool output reportedly starts with ScriptConsoleLogRule; must match actual output for correctness
- anchor: `"rule_id": "ScriptMagicNumberRule"` (line 5 of current file -- the first finding's rule_id)

If the tool output order differs from the current file:
1. Overwrite the entire file with the actual tool output
2. Format: pretty-printed JSON with 2-space indentation
3. Top-level keys must be `exit_code` and `findings` only (matching current structure)
4. The findings array must be in the exact order returned by the tool

If the tool output order matches the current file exactly (all 11 findings in same order with same content), leave the file unchanged.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no linter configured in pyproject.toml; skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_runner.py -v`
- smoke: Run `uv run pytest tests/test_runner.py -v` and verify:
  - `TestRunAuditCleanApp`: all 6 tests pass
  - `TestRunAuditDirtyApp`: all 11 tests pass
  - `TestRunAuditTimeout`: both tests pass
  - `TestRunAuditInvalidPath`: all 3 tests pass
  - Total: 22 tests, 0 failures, 0 errors
  - Run time should be under 60 seconds (module-scoped fixtures invoke the real tool only twice)

## Constraints
- Do NOT modify `src/runner.py` -- tests must validate the existing implementation, not adjust it to pass tests
- Do NOT modify `src/models.py`
- Do NOT modify `IMPL_PLAN.md`, `CLAUDE.md`, or `ARCHITECTURE.md`
- Do NOT add new dependencies to `pyproject.toml` -- all needed modules are in stdlib or already installed
- Do NOT use ordered list comparison for findings assertions -- always use set membership (`{f.rule_id for f in result.findings}`) or filtered lists; never assert on `result.findings[0].rule_id` or compare the full `result.findings` list against an ordered expected list
- Do NOT define any helper function more than once in the file -- check before adding any new helper
- Do NOT use `Path("tests/fixtures/...")` or relative string paths -- always use `Path(__file__).parent / "..."` so tests work regardless of invocation directory
- `clean_result` and `dirty_result` fixtures MUST have `scope="module"` -- the parent tool is slow and must not be invoked per-test
- Mock patch target MUST be `"src.runner.subprocess.run"`, NOT `"subprocess.run"` -- patch where it is used
