# Plan: P4.1

## Context

`src/reporter.py` was started in a WIP commit (`fb29f51`). The file already exists with a
complete implementation. The builder must:
1. Read the existing file and verify it matches this spec exactly.
2. If any function body, signature, import, or docstring differs from this spec, correct it.
3. If the file already matches, make no changes.

Note: `tests/test_reporter.py` is NOT part of P4.1 -- it is covered by P4.5.

## Dependencies

- list: [] (no new packages required -- json, logging, collections are stdlib; pydantic and
  src.models are already present)
- commands: [] (no install commands needed)

## File Operations (in execution order)

### 1. MODIFY src/reporter.py

- operation: MODIFY
- reason: WIP commit may have incomplete or incorrect implementation; verify and finalize
- anchor: `"""Report formatting for Arcane Auditor scan results."""`

#### Imports / Dependencies

```python
from __future__ import annotations

import json
import logging
from collections import Counter

from src.models import ReportFormat, ReporterError, ScanResult
```

No other imports. Do not add any imports beyond the six lines above.

#### Module-level Setup

Immediately after imports, declare the module logger:

```python
logger = logging.getLogger(__name__)
```

#### Functions

- signature: `def report_findings(scan_result: ScanResult, format: ReportFormat) -> str:`
  - purpose: Dispatch to the correct format function based on the format enum value.
  - logic:
    1. If `format == ReportFormat.JSON`, call `format_json(scan_result)` and return its result.
    2. Elif `format == ReportFormat.SARIF`, raise `ReporterError("SARIF format not yet implemented")`.
    3. Elif `format == ReportFormat.GITHUB_ISSUES`, raise `ReporterError("GitHub Issues format not yet implemented")`.
    4. Elif `format == ReportFormat.PR_COMMENT`, raise `ReporterError("PR Comment format not yet implemented")`.
    5. Elif `format == ReportFormat.SUMMARY`, call `format_summary(scan_result)` and return its result.
    6. After all elif branches (none matched), raise `ReporterError(f"Unsupported report format: {format!r}")`.
  - calls: `format_json(scan_result)`, `format_summary(scan_result)`
  - returns: `str` -- the formatted report
  - error handling: Raise `ReporterError` for unimplemented or unrecognized formats. Do NOT use a bare `else` before the final raise -- the final raise is unconditional after all elif branches.
  - docstring (Google style):
    ```
    Dispatch to the correct format function based on the format enum value.

    Args:
        scan_result: The scan result to format.
        format: The desired output format.

    Returns:
        The formatted report as a string.

    Raises:
        ReporterError: If the format is unimplemented or unrecognized.
    ```

- signature: `def format_json(scan_result: ScanResult) -> str:`
  - purpose: Serialize a ScanResult to a pretty-printed JSON string.
  - logic:
    1. Call `scan_result.model_dump(mode="json")` and assign the result to `data`.
    2. Call `json.dumps(data, indent=2)` and return the result.
  - calls: `scan_result.model_dump(mode="json")`, `json.dumps(data, indent=2)`
  - returns: `str` -- a valid JSON string indented with 2 spaces
  - error handling: None. Let Pydantic and json raise naturally if the model is invalid.
  - docstring (Google style):
    ```
    Serialize a ScanResult to a pretty-printed JSON string.

    Args:
        scan_result: The scan result to serialize.

    Returns:
        A valid JSON string, indented with 2 spaces.
    ```

- signature: `def format_summary(scan_result: ScanResult) -> str:`
  - purpose: Produce a human-readable text summary with counts by severity, rule, and file.
  - logic:
    1. Declare `lines: list[str] = []`.
    2. Append `f"Arcane Auditor -- {scan_result.repo}"` to `lines`.
    3. Append `f"Scanned: {scan_result.timestamp.isoformat()}"` to `lines`.
    4. Append a combined findings count line:
       `f"Total findings: {scan_result.findings_count}  (ACTION: {scan_result.action_count}, ADVICE: {scan_result.advice_count})"`.
       Note: two spaces between the total count and the opening parenthesis.
    5. Append `"-" * 60` to `lines` (a 60-dash separator).
    6. If `scan_result.findings_count == 0`:
       a. Append `"No findings. Application is clean."` to `lines`.
    7. Else (findings_count > 0):
       a. Append `"By Severity:"` to `lines`.
       b. Append `f"  ACTION : {scan_result.action_count}"` to `lines`.
       c. Append `f"  ADVICE : {scan_result.advice_count}"` to `lines`.
       d. Append `"By Rule:"` to `lines`.
       e. Build `rule_counts = Counter(f.rule_id for f in scan_result.findings)`.
       f. For each `(rule_id, count)` in `rule_counts.most_common()`:
          append `f"  {rule_id:<50} {count}"` to `lines`.
       g. Append `"By File:"` to `lines`.
       h. Build `file_counts = Counter(f.file_path for f in scan_result.findings)`.
       i. For each `(file_path, count)` in `file_counts.most_common()`:
          append `f"  {file_path:<60} {count}"` to `lines`.
    8. Return `"\n".join(lines)`.
  - calls: `Counter`, `scan_result.findings_count`, `scan_result.action_count`, `scan_result.advice_count`, `scan_result.timestamp.isoformat()`, `scan_result.repo`, `rule_counts.most_common()`, `file_counts.most_common()`
  - returns: `str` -- multi-line summary with no trailing newline
  - error handling: None.
  - docstring (Google style):
    ```
    Produce a human-readable text summary with counts by severity, rule, and file.

    Args:
        scan_result: The scan result to summarize.

    Returns:
        A multi-line summary string.
    ```

#### Wiring / Integration

- `report_findings` is the public API. It is called from `src/cli.py` (Phase 5) with the
  `ScanResult` returned by `runner.run_audit` and the `ReportFormat` chosen by the user.
- No wiring changes needed at this phase -- cli.py does not yet exist.
- The three functions (`report_findings`, `format_json`, `format_summary`) must be importable
  from `src.reporter` by the time P4.5 writes the test file.

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.reporter import report_findings, format_json, format_summary; print('import OK')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile src/reporter.py && echo 'syntax OK'`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q`
- smoke:
  1. Run: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
import json
from src.models import ExitCode, ScanResult
from src.reporter import format_json, format_summary, report_findings, ReportFormat

result = ScanResult(repo='test/repo', findings_count=0, findings=[], exit_code=ExitCode.CLEAN)
j = format_json(result)
parsed = json.loads(j)
assert parsed['repo'] == 'test/repo', 'JSON repo mismatch'
assert parsed['findings_count'] == 0, 'JSON findings_count mismatch'
s = format_summary(result)
assert 'No findings' in s, 'summary missing clean message'
assert 'test/repo' in s, 'summary missing repo'
d = report_findings(result, ReportFormat.JSON)
assert json.loads(d)['repo'] == 'test/repo', 'dispatcher JSON mismatch'
print('smoke OK')
"`
  2. Expected output: `smoke OK`

## Constraints

- Do NOT create `tests/test_reporter.py` -- that is P4.5.
- Do NOT modify `src/models.py`, `src/runner.py`, `src/scanner.py`, `src/config.py`.
- Do NOT add any imports beyond the six import lines specified above.
- Do NOT add a `__all__` list or any other module-level declarations beyond the logger.
- Do NOT use `print()` anywhere -- logging only.
- format_summary must use `"\n".join(lines)` as the final return -- not a running string
  concatenation.
- The final `raise ReporterError(...)` in `report_findings` must be outside and after all
  `if/elif` branches (not inside an `else`).
