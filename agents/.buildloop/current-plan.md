# Plan: P4.2

## Dependencies
- list: []
- commands: []
  (No new dependencies required. `json` is stdlib. All needed models are already in src/models.py.)

## File Operations (in execution order)

### 1. MODIFY src/reporter.py
- operation: MODIFY
- reason: Add `format_sarif`, two private helpers, and wire SARIF into the dispatcher

#### Imports / Dependencies
Replace the existing import line:
```
from src.models import ReportFormat, ReporterError, ScanResult
```
with:
```
from src.models import Finding, ReportFormat, ReporterError, ScanResult, Severity
```
(Add `Finding` and `Severity` to the import. All other imports at the top of the file remain unchanged.)

#### Functions

##### `format_sarif`
- signature: `def format_sarif(scan_result: ScanResult) -> str:`
- purpose: Produce a valid SARIF v2.1.0 JSON document from a ScanResult.
- logic:
  1. Call `_build_sarif_rules(scan_result.findings)` and assign the result to `rules: list[dict]`.
  2. Build `rule_index_map: dict[str, int]` by iterating `enumerate(rules)` and mapping each `rule["id"]` to its integer index `i`.
  3. Build `results: list[dict]` by calling `_build_sarif_result(f, rule_index_map)` for each `f` in `scan_result.findings`, using a list comprehension.
  4. Construct `doc: dict` with the following exact structure:
     ```python
     doc = {
         "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
         "version": "2.1.0",
         "runs": [
             {
                 "tool": {
                     "driver": {
                         "name": "Arcane Auditor",
                         "version": "1.0.0",
                         "rules": rules,
                     }
                 },
                 "results": results,
             }
         ],
     }
     ```
  5. Return `json.dumps(doc, indent=2)`.
- calls: `_build_sarif_rules(scan_result.findings)`, `_build_sarif_result(f, rule_index_map)`, `json.dumps(doc, indent=2)`
- returns: `str` -- a pretty-printed JSON string representing the SARIF document
- error handling: No explicit error handling. All inputs come from validated Pydantic models; no failure paths exist.

##### `_build_sarif_rules`
- signature: `def _build_sarif_rules(findings: list[Finding]) -> list[dict]:`
- purpose: Build a deduplicated, ordered list of SARIF rule descriptor dicts from findings.
- logic:
  1. Declare `seen: dict[str, str]` (maps rule_id to its resolved SARIF level string -- either `"error"` or `"warning"`). Initialize as empty dict.
  2. Declare `order: list[str]` to track insertion order of rule IDs. Initialize as empty list.
  3. For each `f` in `findings`:
     a. Set `level = "error"` if `f.severity == Severity.ACTION` else `level = "warning"`.
     b. If `f.rule_id` is NOT in `seen`: append `f.rule_id` to `order` and set `seen[f.rule_id] = level`.
     c. If `f.rule_id` IS in `seen` and `level == "error"`: set `seen[f.rule_id] = "error"` (escalate to error if any finding for this rule is ACTION).
  4. Build and return a list by iterating `order`: for each `rule_id` in `order`, append a dict:
     ```python
     {
         "id": rule_id,
         "name": rule_id,
         "shortDescription": {"text": rule_id},
         "defaultConfiguration": {"level": seen[rule_id]},
     }
     ```
- calls: none
- returns: `list[dict]` -- ordered list of SARIF rule descriptor dicts; empty list if `findings` is empty
- error handling: None required. Inputs are validated Finding models.

##### `_build_sarif_result`
- signature: `def _build_sarif_result(finding: Finding, rule_index_map: dict[str, int]) -> dict:`
- purpose: Build a single SARIF result dict from a Finding.
- logic:
  1. Set `level = "error"` if `finding.severity == Severity.ACTION` else `level = "warning"`.
  2. Set `start_line = max(1, finding.line)`. This ensures SARIF's requirement that startLine >= 1 is met even when Finding.line is 0 (unknown).
  3. Set `uri = finding.file_path.replace("\\", "/")`. This converts Windows backslashes to forward slashes for URI compliance; no-op on Unix paths.
  4. Construct and return:
     ```python
     {
         "ruleId": finding.rule_id,
         "ruleIndex": rule_index_map[finding.rule_id],
         "level": level,
         "message": {"text": finding.message},
         "locations": [
             {
                 "physicalLocation": {
                     "artifactLocation": {
                         "uri": uri,
                         "uriBaseId": "%SRCROOT%",
                     },
                     "region": {
                         "startLine": start_line,
                     },
                 }
             }
         ],
     }
     ```
- calls: none
- returns: `dict` -- a single SARIF result object
- error handling: None. `rule_index_map[finding.rule_id]` will always succeed because `_build_sarif_rules` was called on the same findings list; every rule_id present in findings is present in the map.

#### Wiring / Integration
In `report_findings`, replace the existing line:
```
        raise ReporterError("SARIF format not yet implemented")
```
(which is at line 30, inside the `elif format == ReportFormat.SARIF:` branch) with:
```
        return format_sarif(scan_result)
```

Place `format_sarif` in the file after the existing `format_summary` function (after line 89).
Place `_build_sarif_rules` immediately after `format_sarif`.
Place `_build_sarif_result` immediately after `_build_sarif_rules`.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.reporter import format_sarif, report_findings; print('import ok')"`
- lint: (no linter configured; skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q`
- smoke:
  1. Run: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
import json
from datetime import datetime, UTC
from src.models import Finding, ScanResult, Severity, ExitCode
from src.reporter import format_sarif

result = ScanResult(
    repo='test-repo',
    timestamp=datetime.now(UTC),
    findings_count=2,
    findings=[
        Finding(rule_id='ScriptVarUsageRule', severity=Severity.ADVICE, message='Use let or const', file_path='app.pmd', line=5),
        Finding(rule_id='HardcodedWorkdayAPIRule', severity=Severity.ACTION, message='Do not hardcode API URL', file_path='service.pod', line=12),
    ],
    exit_code=ExitCode.ISSUES_FOUND,
)
out = format_sarif(result)
doc = json.loads(out)
assert doc['version'] == '2.1.0'
assert len(doc['runs']) == 1
run = doc['runs'][0]
assert run['tool']['driver']['name'] == 'Arcane Auditor'
assert len(run['tool']['driver']['rules']) == 2
assert len(run['results']) == 2
assert run['results'][0]['level'] == 'warning'
assert run['results'][1]['level'] == 'error'
assert run['results'][0]['locations'][0]['physicalLocation']['region']['startLine'] == 5
assert run['results'][1]['ruleIndex'] == 1
print('smoke: PASS')
"`
  2. Verify output is `smoke: PASS` with no exceptions.
  3. Also verify with zero findings:
  Run: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
import json
from datetime import datetime, UTC
from src.models import ScanResult, ExitCode
from src.reporter import format_sarif

result = ScanResult(repo='clean', timestamp=datetime.now(UTC), findings_count=0, findings=[], exit_code=ExitCode.CLEAN)
doc = json.loads(format_sarif(result))
assert doc['runs'][0]['results'] == []
assert doc['runs'][0]['tool']['driver']['rules'] == []
print('empty smoke: PASS')
"`

## Constraints
- Do NOT add any new dependencies to pyproject.toml. All needed imports (`json`, `Finding`, `Severity`) are already available.
- Do NOT modify src/models.py. The existing models are sufficient.
- Do NOT create a test file. P4.5 covers test_reporter.py.
- Do NOT modify IMPL_PLAN.md, CLAUDE.md, or ARCHITECTURE.md.
- Do NOT use `urllib.parse.quote` on file URIs -- the `replace("\\", "/")` backslash conversion is the only path transformation needed. Arcane Auditor finding paths are simple relative paths and do not contain characters requiring percent-encoding.
- The `_build_sarif_rules` and `_build_sarif_result` functions are private helpers (underscore prefix). They must not be exported or referenced outside reporter.py.
- `ruleIndex` in each result must be the integer index of the rule in the `rules` array. Use the `rule_index_map` dict for this. Do not recompute by scanning the list.
- `startLine` must always be an integer >= 1. Use `max(1, finding.line)` unconditionally.
