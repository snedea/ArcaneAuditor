# Plan: P6.4

## Status Note

`src/fixer.py` was already created in a prior WIP commit (97f87b1) and is fully correct.
The builder must NOT recreate or overwrite it. Read it first, then verify it matches the
spec below. The primary work for P6.4 is creating `tests/test_fixer.py`.

## Dependencies

- list: []  (no new packages; pytest already in dev dependencies)
- commands: []

## File Operations (in execution order)

### 1. VERIFY src/fixer.py

- operation: MODIFY (verify only -- the file is already correct; only fix if a specific
  discrepancy is found relative to the spec below)
- reason: file exists from WIP commit; must confirm both public functions are present and
  correct before writing tests against them

#### Expected public API (verify these signatures exist verbatim):

```python
def fix_findings(scan_result: ScanResult, source_dir: Path) -> list[FixResult]:
```

Logic the builder must confirm is present:
1. Instantiate `FixTemplateRegistry()` once at the top of the function.
2. Iterate `scan_result.findings`.
3. For each finding, construct `file_path = source_dir / finding.file_path`.
4. If `file_path` does not exist, log a WARNING and `continue`.
5. Read `file_path.read_text(encoding="utf-8")`, catch `OSError`, log WARNING, `continue`.
6. Call `registry.find_matching(finding)` to get all matching templates.
7. Filter to `high_conf = [t for t in matching if t.confidence == Confidence.HIGH]`.
8. If `high_conf` is empty, log DEBUG and `continue`.
9. Call `high_conf[0].apply(finding, original_content)` inside a try/except `Exception`.
10. If exception, log WARNING and `continue`.
11. If result is None, log DEBUG and `continue`.
12. Append result to `results` list.
13. Return `results`.

```python
def apply_fixes(fix_results: list[FixResult], target_dir: Path) -> list[Path]:
```

Logic the builder must confirm is present:
1. Initialize `written: list[Path] = []` and `seen: set[str] = set()`.
2. For each `fix_result` in `fix_results`:
   a. Get `file_path_str = fix_result.finding.file_path`.
   b. If `file_path_str in seen`, log WARNING and `continue` (first fix wins).
   c. Construct `candidate = Path(file_path_str)`.
   d. If `candidate.is_absolute()` or `".." in candidate.parts`, raise
      `FixerError(f"apply_fixes: unsafe path in finding: {file_path_str}")`.
   e. Construct `dest = target_dir / candidate`.
   f. Call `dest.parent.mkdir(parents=True, exist_ok=True)`.
   g. Call `dest.write_text(fix_result.fixed_content, encoding="utf-8")`.
   h. On `OSError`, raise `FixerError(f"apply_fixes: failed to write {dest}: {exc}")`.
   i. Log DEBUG, add `file_path_str` to `seen`, append `dest` to `written`.
3. Return `written`.

If ANY of the above is missing or wrong in the existing file, apply a targeted Edit to
correct only the broken portion. If everything matches, make no changes.

---

### 2. CREATE tests/test_fixer.py

- operation: CREATE
- reason: no test file exists for src/fixer.py; per project convention every module gets
  a test file

#### Imports / Dependencies

```python
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.fixer import apply_fixes, fix_findings
from src.models import (
    Confidence,
    ExitCode,
    Finding,
    FixerError,
    FixResult,
    ScanResult,
    Severity,
)
```

#### Helper functions

```python
def _finding(
    rule_id: str = "ScriptVarUsageRule",
    line: int = 1,
    file_path: str = "test.script",
    message: str = "test",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=Severity.ACTION,
        message=message,
        file_path=file_path,
        line=line,
    )


def _scan_result(findings: list[Finding]) -> ScanResult:
    return ScanResult(
        repo="test-repo",
        findings_count=len(findings),
        findings=findings,
        exit_code=ExitCode.ISSUES_FOUND if findings else ExitCode.CLEAN,
    )


def _fix_result(
    file_path: str = "test.script",
    original: str = "var x = 1;\n",
    fixed: str = "const x = 1;\n",
) -> FixResult:
    return FixResult(
        finding=_finding(file_path=file_path),
        original_content=original,
        fixed_content=fixed,
        confidence=Confidence.HIGH,
    )
```

#### Class TestFixFindings

All tests in this class use `tmp_path: Path` from pytest.

**Function: test_returns_empty_list_for_empty_findings**
- signature: `def test_returns_empty_list_for_empty_findings(self, tmp_path: Path) -> None:`
- logic:
  1. Call `fix_findings(_scan_result([]), tmp_path)`.
  2. Assert result equals `[]`.

**Function: test_skips_finding_when_file_not_found**
- signature: `def test_skips_finding_when_file_not_found(self, tmp_path: Path) -> None:`
- logic:
  1. Create a finding with `file_path="nonexistent.script"`.
  2. Call `fix_findings(_scan_result([finding]), tmp_path)`.
  3. Assert result equals `[]`.

**Function: test_skips_finding_with_no_matching_template**
- signature: `def test_skips_finding_with_no_matching_template(self, tmp_path: Path) -> None:`
- logic:
  1. Write `tmp_path / "test.script"` with content `"var x = 1;\n"`.
  2. Create finding with `rule_id="UnknownRuleWithNoTemplate"`, `file_path="test.script"`, `line=1`.
  3. Call `fix_findings(_scan_result([finding]), tmp_path)`.
  4. Assert result equals `[]`.

**Function: test_applies_high_confidence_template_and_returns_fix_result**
- signature: `def test_applies_high_confidence_template_and_returns_fix_result(self, tmp_path: Path) -> None:`
- logic:
  1. Write `tmp_path / "test.script"` with content `"var x = 1;\nreturn x;\n"`.
  2. Create finding with `rule_id="ScriptVarUsageRule"`, `file_path="test.script"`, `line=1`.
  3. Call `result = fix_findings(_scan_result([finding]), tmp_path)`.
  4. Assert `len(result) == 1`.
  5. Assert `result[0]` is a `FixResult` instance.
  6. Assert `"const x = 1;" in result[0].fixed_content`.
  7. Assert `result[0].confidence == Confidence.HIGH`.

**Function: test_does_not_modify_file_on_disk**
- signature: `def test_does_not_modify_file_on_disk(self, tmp_path: Path) -> None:`
- logic:
  1. Write `tmp_path / "test.script"` with content `"var x = 1;\n"`.
  2. Create finding with `rule_id="ScriptVarUsageRule"`, `file_path="test.script"`, `line=1`.
  3. Call `fix_findings(_scan_result([finding]), tmp_path)`.
  4. Read `(tmp_path / "test.script").read_text(encoding="utf-8")`.
  5. Assert it still equals `"var x = 1;\n"` (file unchanged on disk).

**Function: test_does_not_apply_non_high_confidence_template**
- signature: `def test_does_not_apply_non_high_confidence_template(self, tmp_path: Path) -> None:`
- logic:
  1. Write `tmp_path / "test.script"` with content `"var x = 1;\n"`.
  2. Create finding with `rule_id="ScriptVarUsageRule"`, `file_path="test.script"`, `line=1`.
  3. Create a `MagicMock()` named `mock_template`. Set `mock_template.confidence = "MEDIUM"`.
     Set `mock_template.match.return_value = True`.
  4. Create a `MagicMock()` named `mock_registry`.
     Set `mock_registry.find_matching.return_value = [mock_template]`.
  5. Use `patch("src.fixer.FixTemplateRegistry", return_value=mock_registry)` as a
     context manager.
  6. Inside the patch context, call `result = fix_findings(_scan_result([finding]), tmp_path)`.
  7. Assert result equals `[]`.
  8. Assert `mock_template.apply` was NOT called (`mock_template.apply.assert_not_called()`).

**Function: test_exception_in_apply_is_suppressed**
- signature: `def test_exception_in_apply_is_suppressed(self, tmp_path: Path) -> None:`
- logic:
  1. Write `tmp_path / "test.script"` with content `"var x = 1;\n"`.
  2. Create finding with `rule_id="ScriptVarUsageRule"`, `file_path="test.script"`, `line=1`.
  3. Create a `MagicMock()` named `mock_template`. Set `mock_template.confidence = "HIGH"`.
     Set `mock_template.match.return_value = True`.
     Set `mock_template.apply.side_effect = RuntimeError("boom")`.
  4. Create `mock_registry = MagicMock()`.
     Set `mock_registry.find_matching.return_value = [mock_template]`.
  5. Use `patch("src.fixer.FixTemplateRegistry", return_value=mock_registry)` as a
     context manager.
  6. Inside the patch context, call `result = fix_findings(_scan_result([finding]), tmp_path)`.
  7. Assert result equals `[]` (exception was swallowed, not re-raised).

**Function: test_apply_returning_none_is_skipped**
- signature: `def test_apply_returning_none_is_skipped(self, tmp_path: Path) -> None:`
- logic:
  1. Write `tmp_path / "test.script"` with content `"var x = 1;\n"`.
  2. Create finding with `rule_id="ScriptVarUsageRule"`, `file_path="test.script"`, `line=1`.
  3. Create `mock_template = MagicMock()`. Set `mock_template.confidence = "HIGH"`.
     Set `mock_template.match.return_value = True`.
     Set `mock_template.apply.return_value = None`.
  4. Create `mock_registry = MagicMock()`.
     Set `mock_registry.find_matching.return_value = [mock_template]`.
  5. Use `patch("src.fixer.FixTemplateRegistry", return_value=mock_registry)`.
  6. Call `fix_findings(...)`.
  7. Assert result equals `[]`.

**Function: test_multiple_findings_multiple_fixes**
- signature: `def test_multiple_findings_multiple_fixes(self, tmp_path: Path) -> None:`
- logic:
  1. Write `tmp_path / "a.script"` with content `"var x = 1;\n"`.
  2. Write `tmp_path / "b.script"` with content `"var y = 2;\n"`.
  3. Create `finding_a = _finding(rule_id="ScriptVarUsageRule", file_path="a.script", line=1)`.
  4. Create `finding_b = _finding(rule_id="ScriptVarUsageRule", file_path="b.script", line=1)`.
  5. Call `result = fix_findings(_scan_result([finding_a, finding_b]), tmp_path)`.
  6. Assert `len(result) == 2`.

---

#### Class TestApplyFixes

All tests use `tmp_path: Path`.

**Function: test_returns_empty_list_for_empty_input**
- signature: `def test_returns_empty_list_for_empty_input(self, tmp_path: Path) -> None:`
- logic:
  1. Call `result = apply_fixes([], tmp_path)`.
  2. Assert result equals `[]`.

**Function: test_writes_fixed_content_to_target_dir**
- signature: `def test_writes_fixed_content_to_target_dir(self, tmp_path: Path) -> None:`
- logic:
  1. Create `fr = _fix_result(file_path="test.script", fixed="const x = 1;\n")`.
  2. Call `written = apply_fixes([fr], tmp_path)`.
  3. Assert `len(written) == 1`.
  4. Assert `written[0] == tmp_path / "test.script"`.
  5. Assert `(tmp_path / "test.script").read_text(encoding="utf-8") == "const x = 1;\n"`.

**Function: test_creates_nested_parent_directories**
- signature: `def test_creates_nested_parent_directories(self, tmp_path: Path) -> None:`
- logic:
  1. Create `fr = _fix_result(file_path="subdir/nested/test.script", fixed="let z = 3;\n")`.
  2. Call `apply_fixes([fr], tmp_path)`.
  3. Assert `(tmp_path / "subdir" / "nested" / "test.script").exists()` is True.
  4. Assert `(tmp_path / "subdir" / "nested" / "test.script").read_text(encoding="utf-8") == "let z = 3;\n"`.

**Function: test_returns_list_of_written_paths**
- signature: `def test_returns_list_of_written_paths(self, tmp_path: Path) -> None:`
- logic:
  1. Create `fr_a = _fix_result(file_path="a.script", fixed="const a = 1;\n")`.
  2. Create `fr_b = _fix_result(file_path="b.script", fixed="const b = 2;\n")`.
  3. Call `written = apply_fixes([fr_a, fr_b], tmp_path)`.
  4. Assert `len(written) == 2`.
  5. Assert `tmp_path / "a.script"` in `written`.
  6. Assert `tmp_path / "b.script"` in `written`.

**Function: test_deduplication_first_fix_wins**
- signature: `def test_deduplication_first_fix_wins(self, tmp_path: Path) -> None:`
- logic:
  1. Create `fr_first = _fix_result(file_path="dup.script", original="var x=1;\n", fixed="const x=1;\n")`.
  2. Create `fr_second = _fix_result(file_path="dup.script", original="var x=1;\n", fixed="let x=1;\n")`.
  3. Call `written = apply_fixes([fr_first, fr_second], tmp_path)`.
  4. Assert `len(written) == 1` (second was deduplicated).
  5. Assert `(tmp_path / "dup.script").read_text(encoding="utf-8") == "const x=1;\n"` (first wins).

**Function: test_raises_FixerError_for_absolute_path**
- signature: `def test_raises_FixerError_for_absolute_path(self, tmp_path: Path) -> None:`
- logic:
  1. Create `fr = _fix_result(file_path="/etc/passwd", fixed="bad\n")`.
  2. Use `pytest.raises(FixerError)` context manager.
  3. Inside, call `apply_fixes([fr], tmp_path)`.

**Function: test_raises_FixerError_for_path_traversal**
- signature: `def test_raises_FixerError_for_path_traversal(self, tmp_path: Path) -> None:`
- logic:
  1. Create `fr = _fix_result(file_path="../outside.script", fixed="bad\n")`.
  2. Use `pytest.raises(FixerError)` context manager.
  3. Inside, call `apply_fixes([fr], tmp_path)`.

**Function: test_raises_FixerError_on_write_failure**
- signature: `def test_raises_FixerError_on_write_failure(self, tmp_path: Path) -> None:`
- logic:
  1. Create `fr = _fix_result(file_path="test.script", fixed="const x=1;\n")`.
  2. Use `patch("pathlib.Path.write_text", side_effect=OSError("disk full"))` as context manager.
  3. Inside, use `pytest.raises(FixerError)` context manager.
  4. Inside that, call `apply_fixes([fr], tmp_path)`.

#### Wiring / Integration

- Import `fix_findings` and `apply_fixes` directly from `src.fixer`.
- No fixtures needed beyond `tmp_path` (built-in pytest fixture).
- Tests for `fix_findings` that exercise real templates rely on the VarToLetConst template
  in `fix_templates/script_fixes.py` matching rule_id="ScriptVarUsageRule".
- Tests using mocks patch `src.fixer.FixTemplateRegistry` (the name as imported in fixer.py).

---

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.fixer import fix_findings, apply_fixes; print('import ok')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run ruff check src/fixer.py tests/test_fixer.py` (skip if ruff not installed)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_fixer.py -v`
- smoke: After test run, confirm all 15 tests pass with zero failures and zero errors.

## Constraints

- Do NOT overwrite or recreate `src/fixer.py` unless a specific bug is found relative to
  the spec in section 1. The file was correctly implemented in the prior WIP commit.
- Do NOT add ruff/mypy configuration or new pyproject.toml entries.
- Do NOT create any fixture files; existing `tests/fixtures/` directories are sufficient.
- Do NOT run the full test suite (only `tests/test_fixer.py`); other tests may have
  environment-dependent failures unrelated to this task.
- Do NOT add docstrings or comments to code that is not being written in this task.
- The patch target for FixTemplateRegistry must be `"src.fixer.FixTemplateRegistry"`,
  not `"fix_templates.base.FixTemplateRegistry"`, because that is the name bound in
  fixer.py's namespace.
- The `_fix_result` helper creates a FixResult with a matching Finding; the `file_path`
  passed to `_fix_result` must be a relative path string (no leading `/`).
