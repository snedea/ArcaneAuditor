# Plan: P6.2

## State Assessment

`fix_templates/script_fixes.py` already exists with all three classes fully implemented
(`VarToLetConst`, `RemoveConsoleLog`, `TemplateLiteralFix`). The WIP commit `eb30039`
created the file but left P6.2 incomplete because `tests/test_script_fixes.py` is missing.

**Remaining work:**
1. CREATE `tests/test_script_fixes.py` -- unit tests for all three fix template classes
   plus registry auto-discovery
2. MODIFY `IMPL_PLAN.md` -- mark P6.2 `[ ]` -> `[x]`

## Dependencies
- list: []
- commands: []

No new dependencies. All required imports (`re`, `pytest`, `src.models`, `fix_templates.*`)
are already available.

## File Operations (in execution order)

### 1. CREATE tests/test_script_fixes.py
- operation: CREATE
- reason: P6.2 requires tests for all three fix template classes; file does not exist

#### Imports / Dependencies
```python
from __future__ import annotations

import pytest

from fix_templates.base import FixTemplate, FixTemplateRegistry
from fix_templates.script_fixes import RemoveConsoleLog, TemplateLiteralFix, VarToLetConst
from src.models import Confidence, Finding, FixResult, Severity
```

#### Helper
- Create a module-level helper `_finding(rule_id: str, line: int, file_path: str = "test.pmd") -> Finding`
  - logic:
    1. Return `Finding(rule_id=rule_id, severity=Severity.ACTION, message="test", file_path=file_path, line=line)`

---

#### Class `TestVarToLetConst`

All methods use `template = VarToLetConst()` instantiated at the top of each test.

##### `test_match_true_for_ScriptVarUsageRule`
- signature: `def test_match_true_for_ScriptVarUsageRule(self) -> None`
- logic:
  1. Instantiate `template = VarToLetConst()`
  2. Call `template.match(_finding("ScriptVarUsageRule", 1))`
  3. Assert result is `True`

##### `test_match_false_for_other_rule`
- signature: `def test_match_false_for_other_rule(self) -> None`
- logic:
  1. Instantiate `template = VarToLetConst()`
  2. Call `template.match(_finding("ScriptConsoleLogRule", 1))`
  3. Assert result is `False`

##### `test_apply_var_becomes_const_when_no_reassignment`
- signature: `def test_apply_var_becomes_const_when_no_reassignment(self) -> None`
- logic:
  1. `source = "var x = 1;\nreturn x;\n"`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `result = VarToLetConst().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == "const x = 1;\nreturn x;\n"`
  6. Assert `result.confidence == Confidence.HIGH`

##### `test_apply_var_becomes_let_when_reassigned_below`
- signature: `def test_apply_var_becomes_let_when_reassigned_below(self) -> None`
- logic:
  1. `source = "var x = 1;\nx = 2;\nreturn x;\n"`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `result = VarToLetConst().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == "let x = 1;\nx = 2;\nreturn x;\n"`

##### `test_apply_var_becomes_let_when_incremented`
- signature: `def test_apply_var_becomes_let_when_incremented(self) -> None`
- logic:
  1. `source = "var i = 0;\ni++;\nreturn i;\n"`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `result = VarToLetConst().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == "let i = 0;\ni++;\nreturn i;\n"`

##### `test_apply_returns_none_when_line_zero`
- signature: `def test_apply_returns_none_when_line_zero(self) -> None`
- logic:
  1. `finding = _finding("ScriptVarUsageRule", 0)`
  2. `result = VarToLetConst().apply(finding, "var x = 1;\n")`
  3. Assert `result is None`

##### `test_apply_returns_none_when_line_exceeds_content`
- signature: `def test_apply_returns_none_when_line_exceeds_content(self) -> None`
- logic:
  1. `finding = _finding("ScriptVarUsageRule", 99)`
  2. `result = VarToLetConst().apply(finding, "var x = 1;\n")`
  3. Assert `result is None`

##### `test_apply_returns_none_when_no_var_on_line`
- signature: `def test_apply_returns_none_when_no_var_on_line(self) -> None`
- logic:
  1. `source = "let x = 1;\n"`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `result = VarToLetConst().apply(finding, source)`
  4. Assert `result is None`

##### `test_apply_multi_var_const_when_none_reassigned`
- signature: `def test_apply_multi_var_const_when_none_reassigned(self) -> None`
- logic:
  1. `source = "var x = 1, y = 2;\nreturn x + y;\n"`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `result = VarToLetConst().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == "const x = 1, y = 2;\nreturn x + y;\n"`

##### `test_apply_multi_var_let_when_extra_var_reassigned`
- signature: `def test_apply_multi_var_let_when_extra_var_reassigned(self) -> None`
- logic:
  1. `source = "var x = 1, y = 2;\ny = 3;\nreturn x + y;\n"`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `result = VarToLetConst().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == "let x = 1, y = 2;\ny = 3;\nreturn x + y;\n"`

##### `test_apply_fix_result_fields`
- signature: `def test_apply_fix_result_fields(self) -> None`
- logic:
  1. `source = "var n = 5;\n"`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `result = VarToLetConst().apply(finding, source)`
  4. Assert `isinstance(result, FixResult)`
  5. Assert `result.finding == finding`
  6. Assert `result.original_content == source`
  7. Assert `result.confidence == Confidence.HIGH`

---

#### Class `TestRemoveConsoleLog`

##### `test_match_true_for_ScriptConsoleLogRule`
- signature: `def test_match_true_for_ScriptConsoleLogRule(self) -> None`
- logic:
  1. `template = RemoveConsoleLog()`
  2. Assert `template.match(_finding("ScriptConsoleLogRule", 1))` is `True`

##### `test_match_false_for_other_rule`
- signature: `def test_match_false_for_other_rule(self) -> None`
- logic:
  1. `template = RemoveConsoleLog()`
  2. Assert `template.match(_finding("ScriptVarUsageRule", 1))` is `False`

##### `test_apply_removes_console_log_only_line`
- signature: `def test_apply_removes_console_log_only_line(self) -> None`
- logic:
  1. `source = "doSomething();\nconsole.log('debug');\nreturn 1;\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 2)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == "doSomething();\nreturn 1;\n"` (line 2 removed entirely)
  6. Assert `result.confidence == Confidence.HIGH`

##### `test_apply_removes_console_warn`
- signature: `def test_apply_removes_console_warn(self) -> None`
- logic:
  1. `source = "console.warn('x');\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == ""`

##### `test_apply_removes_console_error`
- signature: `def test_apply_removes_console_error(self) -> None`
- logic:
  1. `source = "console.error('x');\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == ""`

##### `test_apply_removes_console_info`
- signature: `def test_apply_removes_console_info(self) -> None`
- logic:
  1. `source = "console.info('x');\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == ""`

##### `test_apply_removes_console_debug`
- signature: `def test_apply_removes_console_debug(self) -> None`
- logic:
  1. `source = "console.debug('x');\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `result.fixed_content == ""`

##### `test_apply_keeps_line_when_other_code_present`
- signature: `def test_apply_keeps_line_when_other_code_present(self) -> None`
- logic:
  1. `source = "foo(); console.log('x');\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `"console.log" not in result.fixed_content`
  6. Assert `"foo()" in result.fixed_content`

##### `test_apply_returns_none_when_line_zero`
- signature: `def test_apply_returns_none_when_line_zero(self) -> None`
- logic:
  1. `finding = _finding("ScriptConsoleLogRule", 0)`
  2. Assert `RemoveConsoleLog().apply(finding, "console.log('x');\n") is None`

##### `test_apply_returns_none_when_line_exceeds_content`
- signature: `def test_apply_returns_none_when_line_exceeds_content(self) -> None`
- logic:
  1. `finding = _finding("ScriptConsoleLogRule", 99)`
  2. Assert `RemoveConsoleLog().apply(finding, "console.log('x');\n") is None`

##### `test_apply_returns_none_when_no_console_on_line`
- signature: `def test_apply_returns_none_when_no_console_on_line(self) -> None`
- logic:
  1. `source = "doSomething();\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. Assert `RemoveConsoleLog().apply(finding, source) is None`

##### `test_apply_returns_none_when_nested_console_remains`
- signature: `def test_apply_returns_none_when_nested_console_remains(self) -> None`
- logic:
  1. `source = "console.log(console.error('x'));\n"` -- nested; outer match removes inner arg reference but "console." remains
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `result is None` (because `console.` still in modified_line after single sub)

##### `test_apply_fix_result_fields`
- signature: `def test_apply_fix_result_fields(self) -> None`
- logic:
  1. `source = "console.log('x');\n"`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `result = RemoveConsoleLog().apply(finding, source)`
  4. Assert `isinstance(result, FixResult)`
  5. Assert `result.finding == finding`
  6. Assert `result.original_content == source`
  7. Assert `result.confidence == Confidence.HIGH`

---

#### Class `TestTemplateLiteralFix`

##### `test_match_true_for_ScriptStringConcatRule`
- signature: `def test_match_true_for_ScriptStringConcatRule(self) -> None`
- logic:
  1. `template = TemplateLiteralFix()`
  2. Assert `template.match(_finding("ScriptStringConcatRule", 1))` is `True`

##### `test_match_false_for_other_rule`
- signature: `def test_match_false_for_other_rule(self) -> None`
- logic:
  1. `template = TemplateLiteralFix()`
  2. Assert `template.match(_finding("ScriptVarUsageRule", 1))` is `False`

##### `test_apply_string_plus_var_to_template_literal`
- signature: `def test_apply_string_plus_var_to_template_literal(self) -> None`
- logic:
  1. `source = "var msg = 'Hello ' + name;\n"` (note: var is separate; line 1 is the concat)
  2. `finding = _finding("ScriptStringConcatRule", 1)`
  3. `result = TemplateLiteralFix().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `` "`Hello ${name}`" `` appears in `result.fixed_content`
  6. Assert `result.confidence == Confidence.HIGH`

##### `test_apply_var_plus_string_to_template_literal`
- signature: `def test_apply_var_plus_string_to_template_literal(self) -> None`
- logic:
  1. `source = "var msg = name + ' world';\n"`
  2. `finding = _finding("ScriptStringConcatRule", 1)`
  3. `result = TemplateLiteralFix().apply(finding, source)`
  4. Assert `result` is not `None`
  5. Assert `` "`${name} world`" `` appears in `result.fixed_content`

##### `test_apply_returns_none_for_function_call_not_var`
- signature: `def test_apply_returns_none_for_function_call_not_var(self) -> None`
- logic:
  1. `source = "var msg = 'Hello ' + getName();\n"` (getName() is a function call; regex excludes it)
  2. `finding = _finding("ScriptStringConcatRule", 1)`
  3. `result = TemplateLiteralFix().apply(finding, source)`
  4. Assert `result is None`
  - NOTE: `_CONCAT_A_RE` uses `(?!\s*\()` lookahead after `\w+` so `getName` followed by `(` won't match

##### `test_apply_returns_none_when_both_patterns_present`
- signature: `def test_apply_returns_none_when_both_patterns_present(self) -> None`
- logic:
  1. `source = "var x = 'a' + b + c + 'd';\n"` -- this line matches both _CONCAT_A_RE and _CONCAT_B_RE
  2. `finding = _finding("ScriptStringConcatRule", 1)`
  3. `result = TemplateLiteralFix().apply(finding, source)`
  4. Assert `result is None` (ambiguous case returns None)

##### `test_apply_returns_none_when_line_zero`
- signature: `def test_apply_returns_none_when_line_zero(self) -> None`
- logic:
  1. `finding = _finding("ScriptStringConcatRule", 0)`
  2. Assert `TemplateLiteralFix().apply(finding, "'a' + b;\n") is None`

##### `test_apply_returns_none_when_line_exceeds_content`
- signature: `def test_apply_returns_none_when_line_exceeds_content(self) -> None`
- logic:
  1. `finding = _finding("ScriptStringConcatRule", 99)`
  2. Assert `TemplateLiteralFix().apply(finding, "'a' + b;\n") is None`

##### `test_apply_returns_none_when_no_concat_on_line`
- signature: `def test_apply_returns_none_when_no_concat_on_line(self) -> None`
- logic:
  1. `source = "var x = 'hello';\n"`
  2. `finding = _finding("ScriptStringConcatRule", 1)`
  3. Assert `TemplateLiteralFix().apply(finding, source) is None`

##### `test_apply_fix_result_fields`
- signature: `def test_apply_fix_result_fields(self) -> None`
- logic:
  1. `source = "var msg = 'Hi ' + user;\n"`
  2. `finding = _finding("ScriptStringConcatRule", 1)`
  3. `result = TemplateLiteralFix().apply(finding, source)`
  4. Assert `isinstance(result, FixResult)`
  5. Assert `result.finding == finding`
  6. Assert `result.original_content == source`
  7. Assert `result.confidence == Confidence.HIGH`

---

#### Class `TestFixTemplateRegistryScriptFixes`

This tests auto-discovery via the registry.

##### `test_registry_discovers_all_three_script_fix_templates`
- signature: `def test_registry_discovers_all_three_script_fix_templates(self) -> None`
- logic:
  1. `registry = FixTemplateRegistry()`
  2. `types = {type(t).__name__ for t in registry.templates}`
  3. Assert `"VarToLetConst" in types`
  4. Assert `"RemoveConsoleLog" in types`
  5. Assert `"TemplateLiteralFix" in types`

##### `test_registry_find_matching_returns_var_to_let_const`
- signature: `def test_registry_find_matching_returns_var_to_let_const(self) -> None`
- logic:
  1. `registry = FixTemplateRegistry()`
  2. `finding = _finding("ScriptVarUsageRule", 1)`
  3. `matches = registry.find_matching(finding)`
  4. Assert `len(matches) == 1`
  5. Assert `isinstance(matches[0], VarToLetConst)`

##### `test_registry_find_matching_returns_remove_console_log`
- signature: `def test_registry_find_matching_returns_remove_console_log(self) -> None`
- logic:
  1. `registry = FixTemplateRegistry()`
  2. `finding = _finding("ScriptConsoleLogRule", 1)`
  3. `matches = registry.find_matching(finding)`
  4. Assert `len(matches) == 1`
  5. Assert `isinstance(matches[0], RemoveConsoleLog)`

##### `test_registry_find_matching_returns_template_literal_fix`
- signature: `def test_registry_find_matching_returns_template_literal_fix(self) -> None`
- logic:
  1. `registry = FixTemplateRegistry()`
  2. `finding = _finding("ScriptStringConcatRule", 1)`
  3. `matches = registry.find_matching(finding)`
  4. Assert `len(matches) == 1`
  5. Assert `isinstance(matches[0], TemplateLiteralFix)`

##### `test_registry_find_matching_returns_empty_for_unknown_rule`
- signature: `def test_registry_find_matching_returns_empty_for_unknown_rule(self) -> None`
- logic:
  1. `registry = FixTemplateRegistry()`
  2. `finding = _finding("UnknownRule", 1)`
  3. `matches = registry.find_matching(finding)`
  4. Assert `matches == []`

---

#### Class `TestFixTemplateABC`

##### `test_all_script_fix_templates_are_FixTemplate_subclasses`
- signature: `def test_all_script_fix_templates_are_FixTemplate_subclasses(self) -> None`
- logic:
  1. For each class in `[VarToLetConst, RemoveConsoleLog, TemplateLiteralFix]`:
     - Assert `issubclass(cls, FixTemplate)` is `True`

##### `test_all_script_fix_templates_have_HIGH_confidence`
- signature: `def test_all_script_fix_templates_have_HIGH_confidence(self) -> None`
- logic:
  1. For each class in `[VarToLetConst, RemoveConsoleLog, TemplateLiteralFix]`:
     - `instance = cls()`
     - Assert `instance.confidence == "HIGH"`

---

### 2. MODIFY IMPL_PLAN.md
- operation: MODIFY
- reason: mark P6.2 as complete once tests pass
- anchor: `- [ ] P6.2: Create fix_templates/script_fixes.py with HIGH-confidence fix templates:`

#### Change
Replace `- [ ] P6.2:` with `- [x] P6.2:` on that line. No other changes to IMPL_PLAN.md.

---

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no lint command configured; project uses no ruff/mypy in pyproject.toml)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_script_fixes.py -v`
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -v` (full suite must still pass)

## Constraints
- Do NOT modify `fix_templates/script_fixes.py` -- it is already correctly implemented
- Do NOT modify `fix_templates/base.py` or `fix_templates/__init__.py`
- Do NOT modify `src/models.py`
- Do NOT add any new dependencies to `pyproject.toml`
- Do NOT use `print()` -- the project bans it; use `logging` if needed (tests need no logging)
- The test for `test_apply_returns_none_when_nested_console_remains` must match the actual
  behavior of `_CONSOLE_RE = re.compile(r'console\.(log|warn|error|info|debug)\s*\([^()]*\)\s*;?')`:
  the `[^()]*` in the pattern means it only matches calls with no nested parens. For
  `console.log(console.error('x'))`, the outer call has `(console.error('x'))` which contains
  parens, so `_CONSOLE_RE` will NOT match the outer call -- but it WILL match the inner
  `console.error('x')` portion, leaving `console.log(` in the output. The check
  `if "console." in modified_line` then triggers, returning `None`. This is the correct
  expected behavior and the test must assert `result is None`.
- The test for `test_apply_returns_none_for_function_call_not_var` verifies the negative
  lookahead `(?!\s*\()` in `_CONCAT_A_RE`. The source `'Hello ' + getName()` must produce
  `None` because `getName` is immediately followed by `(`.
- Mark IMPL_PLAN.md P6.2 as `[x]` only AFTER `uv run pytest tests/test_script_fixes.py -v`
  exits 0 with no failures.
