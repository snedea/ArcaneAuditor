# Plan: P6.4

## Dependencies
- list: []
- commands: []
  (No new packages needed — all imports come from stdlib and already-installed project deps)

## File Operations (in execution order)

### 1. CREATE src/fixer.py
- operation: CREATE
- reason: Implements fix_findings() and apply_fixes() as specified in P6.4; no file currently exists at this path

#### Imports / Dependencies
```python
from __future__ import annotations

import logging
from pathlib import Path

from fix_templates.base import FixTemplateRegistry
from src.models import Confidence, Finding, FixerError, FixResult, ScanResult
```

#### Functions

- signature: `def fix_findings(scan_result: ScanResult, source_dir: Path) -> list[FixResult]`
  - purpose: Iterate every finding in scan_result; for each finding find the first HIGH-confidence matching template, apply it, and collect the FixResult.
  - logic:
    1. Instantiate `registry = FixTemplateRegistry()`.
    2. Initialize `results: list[FixResult] = []`.
    3. For each `finding` in `scan_result.findings`:
       a. Resolve the file path: `file_path = source_dir / finding.file_path`. (finding.file_path is a relative string from the auditor output; source_dir is the root of the scanned app.)
       b. If `file_path` does not exist on disk, log a warning with `logger.warning("fixer: file not found, skipping: %s", file_path)` and `continue`.
       c. Read file content: `original_content = file_path.read_text(encoding="utf-8")`.
       d. Call `matching = registry.find_matching(finding)`.
       e. Filter to only HIGH-confidence templates: `high_conf = [t for t in matching if t.confidence == Confidence.HIGH]`.
       f. If `high_conf` is empty, log debug `logger.debug("fixer: no HIGH template for rule %s", finding.rule_id)` and `continue`.
       g. Take the first template: `template = high_conf[0]`.
       h. Call `fix_result = template.apply(finding, original_content)` inside a `try/except Exception as exc` block.
       i. If `fix_result` is None, log debug `logger.debug("fixer: template %s returned None for rule %s", type(template).__name__, finding.rule_id)` and `continue`.
       j. If `apply()` raises any exception, log a warning `logger.warning("fixer: template %s raised %s for rule %s: %s", type(template).__name__, type(exc).__name__, finding.rule_id, exc)` and `continue` (do NOT re-raise).
       k. Append `fix_result` to `results`.
    4. Return `results`.
  - calls: `FixTemplateRegistry()`, `registry.find_matching(finding)`, `template.apply(finding, original_content)`, `file_path.read_text()`
  - returns: `list[FixResult]` — may be empty if no HIGH-confidence fixes matched or all templates returned None
  - error handling: File-not-found is handled by existence check (step 3b). `template.apply()` exceptions are caught per-finding and logged as warnings — never propagate to caller. `file_path.read_text()` OSError is NOT silently swallowed: wrap in `try/except OSError as exc`, log warning `logger.warning("fixer: cannot read %s: %s", file_path, exc)`, and `continue`.

- signature: `def apply_fixes(fix_results: list[FixResult], target_dir: Path) -> list[Path]`
  - purpose: Write each FixResult's fixed_content to the corresponding file under target_dir, creating parent directories as needed.
  - logic:
    1. Initialize `written: list[Path] = []`.
    2. For each `fix_result` in `fix_results`:
       a. Compute `dest = target_dir / fix_result.finding.file_path`.
       b. Call `dest.parent.mkdir(parents=True, exist_ok=True)`.
       c. Write `dest.write_text(fix_result.fixed_content, encoding="utf-8")` inside a `try/except OSError as exc` block.
       d. If `write_text` raises `OSError`, raise `FixerError(f"apply_fixes: failed to write {dest}: {exc}")` from `exc`.
       e. Log debug `logger.debug("apply_fixes: wrote %s", dest)`.
       f. Append `dest` to `written`.
    3. Return `written`.
  - calls: `dest.parent.mkdir()`, `dest.write_text()`, `FixerError()`
  - returns: `list[Path]` — the list of file paths that were successfully written
  - error handling: Raise `FixerError` (not a bare `OSError`) so callers get a consistent exception type. Do NOT silently ignore write failures.

#### Module-level
- Add `logger = logging.getLogger(__name__)` at module scope, after imports.
- Add a module docstring: `"""Apply deterministic fix templates to Arcane Auditor findings."""`

#### Wiring / Integration
- `fix_findings` is called by `src/cli.py` in Phase 7 (P7.1). No wiring needed in this task — the function is self-contained.
- `apply_fixes` is likewise called by `src/cli.py` in P7.1. Not wired in this task.
- Both functions are importable as `from src.fixer import fix_findings, apply_fixes`.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.fixer import fix_findings, apply_fixes; print('import ok')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run ruff check src/fixer.py`
- test: no existing test file for fixer.py yet (tests/test_fixer.py is P6.5) — run `uv run pytest tests/ -x -q` to confirm no existing tests break
- smoke:
  1. Run `uv run python -c "from src.fixer import fix_findings, apply_fixes; from src.models import ScanResult, ExitCode; from pathlib import Path; sr = ScanResult(repo='test', findings_count=0, findings=[], exit_code=ExitCode.CLEAN); result = fix_findings(sr, Path('.')); print('fix_findings ok, results:', result)"`
  2. Expect output: `fix_findings ok, results: []`

## Constraints
- Do NOT modify any existing file: not models.py, not fix_templates/base.py, not fix_templates/script_fixes.py, not fix_templates/structure_fixes.py, not src/cli.py, not IMPL_PLAN.md, not CLAUDE.md.
- Do NOT add a new entry point, CLI command, or route — P7.1 handles CLI wiring.
- Do NOT apply fixes to source_dir in fix_findings — the function returns FixResult objects with fixed_content strings only. File writes are exclusively in apply_fixes.
- Do NOT filter by finding.severity inside fix_findings. The confidence filter (HIGH only) is sufficient; severity filtering is the caller's concern.
- Only one template is applied per finding — the first HIGH-confidence match from `registry.find_matching()`. Do not try multiple templates per finding.
- apply_fixes MUST raise FixerError on write failure, not silently continue.
