# Plan: P6.5

## Dependencies
- list: []
- commands: []
  (All required packages already installed via pyproject.toml. No new dependencies needed.)

## File Operations (in execution order)

### 1. MODIFY tests/test_fixer.py
- operation: MODIFY
- reason: Add end-to-end re-scan tests for each fix template, a LOW confidence filter test, and a no-new-violations test. The existing file has TestFixFindings and TestApplyFixes but no tests that run Arcane Auditor after applying a fix.
- anchor: `from src.fixer import apply_fixes, fix_findings` (line 7 in existing file)

#### Imports / Dependencies
Add the following imports after the existing import block (after line 16, before the `_finding` helper):
```python
from src.models import AgentConfig, ScanManifest
from src.runner import run_audit
from fix_templates.script_fixes import RemoveConsoleLog, TemplateLiteralFix, VarToLetConst
from fix_templates.structure_fixes import (
    AddFailOnStatusCodes,
    LowerCamelCaseEndpointName,
    LowerCamelCaseWidgetId,
)
```

Also add this constant after the existing imports, before the helper functions:
```python
AUDITOR_PATH: Path = Path(__file__).parent.parent.parent
```

#### Module-level helper function
Add this helper function after the existing `_fix_result` helper (after line 53 in the existing file):

- signature: `def _make_auditor_config() -> AgentConfig:`
  - purpose: Return an AgentConfig pointing at the real parent Arcane Auditor tool.
  - logic:
    1. Return `AgentConfig(auditor_path=AUDITOR_PATH)`
  - returns: `AgentConfig`
  - error handling: None

#### New Class: TestLowConfidenceNotAutoApplied
Add after the existing `TestApplyFixes` class (after line 183).

Tests that fix_findings skips any template whose confidence is not HIGH.

**Test methods:**

- `test_low_confidence_template_is_skipped(self, tmp_path: Path) -> None:`
  - logic:
    1. Write `tmp_path / "test.script"` with content `"var x = 1;\n"`
    2. Construct `finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)`
    3. Create `mock_template = MagicMock()` with `mock_template.confidence = "LOW"` and `mock_template.match.return_value = True`
    4. Create `mock_registry = MagicMock()` with `mock_registry.find_matching.return_value = [mock_template]`
    5. `with patch("src.fixer.FixTemplateRegistry", return_value=mock_registry):`
    6. Call `result = fix_findings(_scan_result([finding]), tmp_path)`
    7. Assert `result == []`
    8. Assert `mock_template.apply.assert_not_called()`

- `test_medium_and_low_templates_both_skipped_leaving_no_results(self, tmp_path: Path) -> None:`
  - logic:
    1. Write `tmp_path / "test.script"` with content `"var x = 1;\n"`
    2. Construct `finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)`
    3. Create `mock_low = MagicMock()` with `mock_low.confidence = "LOW"` and `mock_low.match.return_value = True`
    4. Create `mock_med = MagicMock()` with `mock_med.confidence = "MEDIUM"` and `mock_med.match.return_value = True`
    5. Create `mock_registry = MagicMock()` with `mock_registry.find_matching.return_value = [mock_low, mock_med]`
    6. `with patch("src.fixer.FixTemplateRegistry", return_value=mock_registry):`
    7. Call `result = fix_findings(_scan_result([finding]), tmp_path)`
    8. Assert `result == []`
    9. Assert `mock_low.apply.assert_not_called()`
    10. Assert `mock_med.apply.assert_not_called()`

#### New Class: TestEndToEndVarToLetConst
Add after `TestLowConfidenceNotAutoApplied`.

Uses a module-scoped fixture to run Arcane Auditor before and after fix. All methods in this class consume the same fixture result.

**Module-scoped fixture** (place at module level, before the class, decorated with `@pytest.fixture(scope="module")`):

- signature: `def var_to_let_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:`
  - purpose: Create minimal violation, scan, apply VarToLetConst, overwrite file, re-scan. Return tuple of (initial_result, fixed_result, rule_id).
  - logic:
    1. `config = _make_auditor_config()`
    2. `source_dir = tmp_path_factory.mktemp("var_to_let")`
    3. `violation_file = source_dir / "test.script"`
    4. Write `violation_file` with content:
       ```
       var testCount = 0;\n{\n  "count": testCount\n}\n
       ```
       (exact string: `"var testCount = 0;\n{\n  \"count\": testCount\n}\n"`)
    5. `manifest = ScanManifest(root_path=source_dir)`
    6. `initial_result = run_audit(manifest, config)`
    7. `findings = [f for f in initial_result.findings if f.rule_id == "ScriptVarUsageRule"]`
    8. Assert `len(findings) >= 1` with message `"ScriptVarUsageRule finding not found in initial scan"`
    9. `finding = findings[0]`
    10. `content = violation_file.read_text(encoding="utf-8")`
    11. `template = VarToLetConst()`
    12. `fix_result = template.apply(finding, content)`
    13. Assert `fix_result is not None` with message `"VarToLetConst.apply() returned None"`
    14. `violation_file.write_text(fix_result.fixed_content, encoding="utf-8")`
    15. `fixed_result = run_audit(manifest, config)`
    16. Return `(initial_result, fixed_result, "ScriptVarUsageRule")`
  - returns: `tuple[ScanResult, ScanResult, str]`
  - error handling: Assertions with descriptive messages serve as test setup guards.

**Test methods** (all receive `var_to_let_results` fixture):

- `test_violation_present_in_initial_scan(self, var_to_let_results: tuple[ScanResult, ScanResult, str]) -> None:`
  - logic:
    1. `initial_result, _, rule_id = var_to_let_results`
    2. `matches = [f for f in initial_result.findings if f.rule_id == rule_id]`
    3. Assert `len(matches) >= 1`

- `test_violation_absent_after_fix(self, var_to_let_results: tuple[ScanResult, ScanResult, str]) -> None:`
  - logic:
    1. `_, fixed_result, rule_id = var_to_let_results`
    2. `matches = [f for f in fixed_result.findings if f.rule_id == rule_id]`
    3. Assert `len(matches) == 0`

- `test_fix_does_not_introduce_new_violations(self, var_to_let_results: tuple[ScanResult, ScanResult, str]) -> None:`
  - logic:
    1. `initial_result, fixed_result, _ = var_to_let_results`
    2. Assert `fixed_result.findings_count <= initial_result.findings_count`

#### New Class: TestEndToEndRemoveConsoleLog
Add after `TestEndToEndVarToLetConst`.

**Module-scoped fixture** (at module level before the class):

- signature: `def remove_console_log_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:`
  - purpose: Create minimal violation, scan, apply RemoveConsoleLog, overwrite file, re-scan.
  - logic:
    1. `config = _make_auditor_config()`
    2. `source_dir = tmp_path_factory.mktemp("remove_console_log")`
    3. `violation_file = source_dir / "test.script"`
    4. Write `violation_file` with content:
       ```
       console.log('debug');\n{\n  "result": null\n}\n
       ```
       (exact string: `"console.log('debug');\n{\n  \"result\": null\n}\n"`)
    5. `manifest = ScanManifest(root_path=source_dir)`
    6. `initial_result = run_audit(manifest, config)`
    7. `findings = [f for f in initial_result.findings if f.rule_id == "ScriptConsoleLogRule"]`
    8. Assert `len(findings) >= 1` with message `"ScriptConsoleLogRule finding not found in initial scan"`
    9. `finding = findings[0]`
    10. `content = violation_file.read_text(encoding="utf-8")`
    11. `template = RemoveConsoleLog()`
    12. `fix_result = template.apply(finding, content)`
    13. Assert `fix_result is not None` with message `"RemoveConsoleLog.apply() returned None"`
    14. `violation_file.write_text(fix_result.fixed_content, encoding="utf-8")`
    15. `fixed_result = run_audit(manifest, config)`
    16. Return `(initial_result, fixed_result, "ScriptConsoleLogRule")`
  - returns: `tuple[ScanResult, ScanResult, str]`

**Test methods** (same three-test pattern as TestEndToEndVarToLetConst):
- `test_violation_present_in_initial_scan(self, remove_console_log_results: ...) -> None:` - same logic pattern
- `test_violation_absent_after_fix(self, remove_console_log_results: ...) -> None:` - same logic pattern
- `test_fix_does_not_introduce_new_violations(self, remove_console_log_results: ...) -> None:` - same logic pattern

#### New Class: TestEndToEndTemplateLiteralFix
Add after `TestEndToEndRemoveConsoleLog`.

**Module-scoped fixture** (at module level before the class):

- signature: `def template_literal_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:`
  - purpose: Create minimal pmd violation, scan, apply TemplateLiteralFix, overwrite file, re-scan.
  - logic:
    1. `config = _make_auditor_config()`
    2. `source_dir = tmp_path_factory.mktemp("template_literal")`
    3. `violation_file = source_dir / "test.pmd"`
    4. Write `violation_file` with content (a valid pmd JSON string, exactly):
       ```json
       {
         "id": "testPage",
         "securityDomains": ["Everyone"],
         "script": "<% const greeting = 'Hello ' + name; %>"
       }
       ```
       Note: in Python, write this as:
       ```python
       '{\n  "id": "testPage",\n  "securityDomains": ["Everyone"],\n  "script": "<% const greeting = \'Hello \' + name; %>"\n}\n'
       ```
       Or use a triple-quoted string. Keep the single quotes inside the script field as-is.
    5. `manifest = ScanManifest(root_path=source_dir)`
    6. `initial_result = run_audit(manifest, config)`
    7. `findings = [f for f in initial_result.findings if f.rule_id == "ScriptStringConcatRule"]`
    8. Assert `len(findings) >= 1` with message `"ScriptStringConcatRule finding not found in initial scan"`
    9. `finding = findings[0]`
    10. `content = violation_file.read_text(encoding="utf-8")`
    11. `template = TemplateLiteralFix()`
    12. `fix_result = template.apply(finding, content)`
    13. Assert `fix_result is not None` with message `"TemplateLiteralFix.apply() returned None"`
    14. `violation_file.write_text(fix_result.fixed_content, encoding="utf-8")`
    15. `fixed_result = run_audit(manifest, config)`
    16. Return `(initial_result, fixed_result, "ScriptStringConcatRule")`
  - returns: `tuple[ScanResult, ScanResult, str]`

**Test methods**: same three-test pattern.

#### New Class: TestEndToEndLowerCamelCaseWidgetId
Add after `TestEndToEndTemplateLiteralFix`.

**Module-scoped fixture** (at module level before the class):

- signature: `def widget_id_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:`
  - purpose: Create pmd with PascalCase widget id, scan, apply LowerCamelCaseWidgetId, overwrite, re-scan.
  - logic:
    1. `config = _make_auditor_config()`
    2. `source_dir = tmp_path_factory.mktemp("widget_id")`
    3. `violation_file = source_dir / "test.pmd"`
    4. Write `violation_file` with content (valid pmd JSON):
       ```json
       {
         "id": "testPage",
         "securityDomains": ["Everyone"],
         "presentation": {
           "body": {
             "type": "section",
             "id": "MyWidget",
             "children": []
           }
         }
       }
       ```
    5. `manifest = ScanManifest(root_path=source_dir)`
    6. `initial_result = run_audit(manifest, config)`
    7. `findings = [f for f in initial_result.findings if f.rule_id == "WidgetIdLowerCamelCaseRule"]`
    8. Assert `len(findings) >= 1` with message `"WidgetIdLowerCamelCaseRule finding not found in initial scan"`
    9. `finding = findings[0]`
    10. `content = violation_file.read_text(encoding="utf-8")`
    11. `template = LowerCamelCaseWidgetId()`
    12. `fix_result = template.apply(finding, content)`
    13. Assert `fix_result is not None` with message `"LowerCamelCaseWidgetId.apply() returned None"`
    14. `violation_file.write_text(fix_result.fixed_content, encoding="utf-8")`
    15. `fixed_result = run_audit(manifest, config)`
    16. Return `(initial_result, fixed_result, "WidgetIdLowerCamelCaseRule")`
  - returns: `tuple[ScanResult, ScanResult, str]`

**Test methods**: same three-test pattern.

#### New Class: TestEndToEndLowerCamelCaseEndpointName
Add after `TestEndToEndLowerCamelCaseWidgetId`.

**Module-scoped fixture** (at module level before the class):

- signature: `def endpoint_name_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:`
  - purpose: Create pod with PascalCase endpoint name, scan, apply LowerCamelCaseEndpointName, overwrite, re-scan.
  - logic:
    1. `config = _make_auditor_config()`
    2. `source_dir = tmp_path_factory.mktemp("endpoint_name")`
    3. `violation_file = source_dir / "test.pod"`
    4. Write `violation_file` with content (valid pod JSON):
       ```json
       {
         "podId": "testPod",
         "seed": {
           "endPoints": [
             {
               "name": "GetHrData",
               "url": "https://example.com/api",
               "failOnStatusCodes": [{"code": 400}, {"code": 403}]
             }
           ]
         }
       }
       ```
       Note: include `failOnStatusCodes` so EndpointFailOnStatusCodesRule does NOT also fire on this fixture, keeping the violation count isolated to the rule under test.
    5. `manifest = ScanManifest(root_path=source_dir)`
    6. `initial_result = run_audit(manifest, config)`
    7. `findings = [f for f in initial_result.findings if f.rule_id == "EndpointNameLowerCamelCaseRule"]`
    8. Assert `len(findings) >= 1` with message `"EndpointNameLowerCamelCaseRule finding not found in initial scan"`
    9. `finding = findings[0]`
    10. `content = violation_file.read_text(encoding="utf-8")`
    11. `template = LowerCamelCaseEndpointName()`
    12. `fix_result = template.apply(finding, content)`
    13. Assert `fix_result is not None` with message `"LowerCamelCaseEndpointName.apply() returned None"`
    14. `violation_file.write_text(fix_result.fixed_content, encoding="utf-8")`
    15. `fixed_result = run_audit(manifest, config)`
    16. Return `(initial_result, fixed_result, "EndpointNameLowerCamelCaseRule")`
  - returns: `tuple[ScanResult, ScanResult, str]`

**Test methods**: same three-test pattern.

#### New Class: TestEndToEndAddFailOnStatusCodes
Add after `TestEndToEndLowerCamelCaseEndpointName`.

**Module-scoped fixture** (at module level before the class):

- signature: `def fail_on_status_codes_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:`
  - purpose: Create pod with endpoint missing failOnStatusCodes, scan, apply AddFailOnStatusCodes, overwrite, re-scan.
  - logic:
    1. `config = _make_auditor_config()`
    2. `source_dir = tmp_path_factory.mktemp("fail_on_status_codes")`
    3. `violation_file = source_dir / "test.pod"`
    4. Write `violation_file` with content (valid pod JSON):
       ```json
       {
         "podId": "testPod",
         "seed": {
           "endPoints": [
             {
               "name": "testEndpoint",
               "url": "https://example.com/api"
             }
           ]
         }
       }
       ```
    5. `manifest = ScanManifest(root_path=source_dir)`
    6. `initial_result = run_audit(manifest, config)`
    7. `findings = [f for f in initial_result.findings if f.rule_id == "EndpointFailOnStatusCodesRule"]`
    8. Assert `len(findings) >= 1` with message `"EndpointFailOnStatusCodesRule finding not found in initial scan"`
    9. `finding = findings[0]`
    10. `content = violation_file.read_text(encoding="utf-8")`
    11. `template = AddFailOnStatusCodes()`
    12. `fix_result = template.apply(finding, content)`
    13. Assert `fix_result is not None` with message `"AddFailOnStatusCodes.apply() returned None"`
    14. `violation_file.write_text(fix_result.fixed_content, encoding="utf-8")`
    15. `fixed_result = run_audit(manifest, config)`
    16. Return `(initial_result, fixed_result, "EndpointFailOnStatusCodesRule")`
  - returns: `tuple[ScanResult, ScanResult, str]`

**Test methods**: same three-test pattern.

#### Wiring / Integration
- The six module-scoped fixtures (`var_to_let_results`, `remove_console_log_results`, `template_literal_results`, `widget_id_results`, `endpoint_name_results`, `fail_on_status_codes_results`) are defined at module level in `tests/test_fixer.py`.
- Each is consumed by its corresponding `TestEndToEnd*` class via pytest fixture injection.
- Each `TestEndToEnd*` class has exactly three test methods: `test_violation_present_in_initial_scan`, `test_violation_absent_after_fix`, `test_fix_does_not_introduce_new_violations`.
- Fixtures use `tmp_path_factory` (not `tmp_path`) because they are module-scoped.
- The `_make_auditor_config()` helper is called inside each fixture (not injected as a fixture itself) to keep setup self-contained.

#### Complete structure of additions to test_fixer.py (in order):

1. **After line 16** (after the existing import block): add 6 new import lines + `AUDITOR_PATH` constant
2. **After the existing `_fix_result` helper** (after line 53): add `_make_auditor_config()` helper
3. **After the existing `TestApplyFixes` class** (after line 183): add in order:
   - `TestLowConfidenceNotAutoApplied` class
   - `var_to_let_results` fixture
   - `TestEndToEndVarToLetConst` class
   - `remove_console_log_results` fixture
   - `TestEndToEndRemoveConsoleLog` class
   - `template_literal_results` fixture
   - `TestEndToEndTemplateLiteralFix` class
   - `widget_id_results` fixture
   - `TestEndToEndLowerCamelCaseWidgetId` class
   - `endpoint_name_results` fixture
   - `TestEndToEndLowerCamelCaseEndpointName` class
   - `fail_on_status_codes_results` fixture
   - `TestEndToEndAddFailOnStatusCodes` class

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no lint command configured; skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_fixer.py -v`
- smoke: After running tests, confirm output shows all TestEndToEnd* tests pass and none skip. The end-to-end tests will be slow (12 Arcane Auditor subprocess invocations) but must all pass.

## Constraints
- Do NOT modify any file other than `tests/test_fixer.py`.
- Do NOT add any new Python package dependencies.
- Do NOT modify the existing `TestFixFindings` or `TestApplyFixes` classes or their tests.
- Do NOT hardcode line numbers or message strings that come from Arcane Auditor output. Use the actual finding returned by `run_audit` to feed into `template.apply()`.
- All fixtures MUST use `tmp_path_factory` (not `tmp_path`) because they have `scope="module"`.
- Each module-scoped fixture MUST write the fixed content back to the same `violation_file` path (overwriting), then call `run_audit` on the same `manifest` (same `source_dir`). Do NOT create a separate "fixed" directory.
- The fixture MUST contain the two assertions (`assert len(findings) >= 1` and `assert fix_result is not None`) as test-setup guards. If these fail, the fixture raises AssertionError and all three dependent tests are ERROR (not FAIL) — this is acceptable and expected for setup failures.
- The `_make_auditor_config()` helper MUST be called inside the fixture function body, not injected as a pytest fixture, to avoid fixture-scope incompatibilities.
- All new test method signatures MUST include explicit return type `-> None`.
- All new code MUST include `from __future__ import annotations` — this is already at line 1 of the existing file, so no action needed.
- The violation file for `TestEndToEndLowerCamelCaseEndpointName` MUST include `failOnStatusCodes` pre-populated on the endpoint to prevent `EndpointFailOnStatusCodesRule` from also firing and interfering with the finding count assertions.
- Assert `fix_result is not None` BEFORE accessing `fix_result.fixed_content` in every fixture (per Known Pattern #1).
