# Plan: P4.1

## Dependencies
- list: []
- commands: []
  (No new packages required. `json`, `collections`, `logging` are stdlib. All model types are already in src/models.py.)

## File Operations (in execution order)

### 1. CREATE src/reporter.py
- operation: CREATE
- reason: New module for formatting ScanResult into multiple output formats; dispatcher + JSON + summary implementations required by P4.1

#### Imports / Dependencies
```python
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict

from src.models import ReportFormat, ReporterError, ScanResult, Severity
```

#### Functions

- signature: `report_findings(scan_result: ScanResult, format: ReportFormat) -> str`
  - purpose: Dispatch to the correct format function based on `format` enum value
  - logic:
    1. Match `format` against each `ReportFormat` enum member using `if/elif` chain
    2. If `format == ReportFormat.JSON`, call `format_json(scan_result)` and return the result
    3. If `format == ReportFormat.SARIF`, raise `ReporterError("SARIF format not yet implemented")`
    4. If `format == ReportFormat.GITHUB_ISSUES`, raise `ReporterError("GitHub Issues format not yet implemented")`
    5. If `format == ReportFormat.PR_COMMENT`, raise `ReporterError("PR Comment format not yet implemented")`
    6. If `format == ReportFormat.SUMMARY` (see note below), call `format_summary(scan_result)` and return the result
    7. After the if/elif chain, raise `ReporterError(f"Unsupported report format: {format!r}")` to handle any unrecognized value

  NOTE: The IMPL_PLAN specifies `ReportFormat.SUMMARY` as a CLI option (`--format summary`). However, the existing `ReportFormat` enum in `src/models.py` does NOT have a `SUMMARY` member. The dispatcher must handle `format_summary` via a new enum value. See "Wiring / Integration" section for the required models.py modification.

  - calls: `format_json(scan_result)`, `format_summary(scan_result)`
  - returns: `str`
  - error handling: Raise `ReporterError` for unimplemented or unrecognized formats

- signature: `format_json(scan_result: ScanResult) -> str`
  - purpose: Serialize ScanResult to a pretty-printed JSON string
  - logic:
    1. Call `scan_result.model_dump(mode="json")` to get a JSON-serializable dict (this handles datetime, Path, and Enum serialization via Pydantic's mode="json")
    2. Call `json.dumps(data, indent=2)` on the resulting dict
    3. Return the resulting string
  - calls: `scan_result.model_dump(mode="json")`, `json.dumps`
  - returns: `str` (valid JSON, indented with 2 spaces)
  - error handling: Let any `TypeError` from `json.dumps` propagate naturally (should not occur with `mode="json"`)

- signature: `format_summary(scan_result: ScanResult) -> str`
  - purpose: Produce a human-readable text summary with counts by severity, rule, and file
  - logic:
    1. Build header line: `f"Arcane Auditor -- {scan_result.repo}"`
    2. Build timestamp line: `f"Scanned: {scan_result.timestamp.isoformat()}"` (timestamp is a datetime with UTC tzinfo)
    3. Build overall counts line: `f"Total findings: {scan_result.findings_count}  (ACTION: {scan_result.action_count}, ADVICE: {scan_result.advice_count})"`
    4. Build separator line of 60 dashes: `"-" * 60`
    5. Build "By Severity" subsection:
       a. Write header `"By Severity:"`
       b. For `Severity.ACTION`: write `f"  ACTION : {scan_result.action_count}"`
       c. For `Severity.ADVICE`: write `f"  ADVICE : {scan_result.advice_count}"`
    6. Build "By Rule" subsection:
       a. Write header `"By Rule:"`
       b. Build a `Counter` by iterating `scan_result.findings` and counting `f.rule_id` occurrences: `rule_counts = Counter(f.rule_id for f in scan_result.findings)`
       c. Sort `rule_counts.most_common()` by count descending (Counter.most_common() already does this)
       d. For each `(rule_id, count)` pair, write `f"  {rule_id:<50} {count}"`
    7. Build "By File" subsection:
       a. Write header `"By File:"`
       b. Build a `Counter` by iterating `scan_result.findings` and counting `f.file_path` occurrences: `file_counts = Counter(f.file_path for f in scan_result.findings)`
       c. Sort `file_counts.most_common()` by count descending
       d. For each `(file_path, count)` pair, write `f"  {file_path:<60} {count}"`
    8. If `scan_result.findings_count == 0`, skip sections 5-7 entirely and instead write a single line: `"No findings. Application is clean."`
    9. Join all lines with `"\n"` and return the resulting string
  - calls: `Counter` (from `collections`), `scan_result.action_count`, `scan_result.advice_count`
  - returns: `str`
  - error handling: No error handling needed; Counter handles empty lists cleanly

#### Wiring / Integration
- `src/reporter.py` imports from `src.models` only; no circular dependencies
- `report_findings` is the single public entry point; `format_json` and `format_summary` are also public (called directly in tests and CLI)

---

### 2. MODIFY src/models.py
- operation: MODIFY
- reason: Add `SUMMARY = "summary"` to the `ReportFormat` enum so the dispatcher and future CLI can reference it
- anchor: `    PR_COMMENT = "pr_comment"`  (line 28, the last existing member of ReportFormat)

#### Change
After the line `    PR_COMMENT = "pr_comment"`, add:
```python
    SUMMARY = "summary"
```

The full updated enum block becomes:
```python
class ReportFormat(str, Enum):
    """Supported output formats for scan reports."""

    JSON = "json"
    SARIF = "sarif"
    GITHUB_ISSUES = "github_issues"
    PR_COMMENT = "pr_comment"
    SUMMARY = "summary"
```

No other changes to models.py.

---

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.reporter import report_findings, format_json, format_summary; print('import ok')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile src/reporter.py && uv run python -m py_compile src/models.py`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q`
- smoke:
  ```
  cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
  from src.models import ReportFormat, ScanResult, ExitCode
  from src.reporter import format_json, format_summary, report_findings
  from datetime import datetime, UTC
  sr = ScanResult(repo='test/repo', findings_count=0, findings=[], exit_code=ExitCode.CLEAN)
  print(format_json(sr)[:80])
  print(format_summary(sr))
  print(report_findings(sr, ReportFormat.JSON)[:40])
  print(report_findings(sr, ReportFormat.SUMMARY))
  "
  ```

## Constraints
- Do NOT modify ARCHITECTURE.md, CLAUDE.md, IMPL_PLAN.md
- Do NOT add any new packages to pyproject.toml; only stdlib modules are needed
- Do NOT implement format_sarif, format_github_issues, or format_pr_comment -- those belong to P4.2-P4.4; the dispatcher must raise ReporterError for those formats
- Do NOT create tests/test_reporter.py -- that belongs to P4.5
- The only two files touched are `src/reporter.py` (CREATE) and `src/models.py` (MODIFY, one line added)
- Use `from __future__ import annotations` as the first import in reporter.py
- Use `logging` module, never `print()`
- All public functions require Google-style docstrings
