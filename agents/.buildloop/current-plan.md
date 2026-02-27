# Plan: P6.2

## Dependencies
- list: []
- commands: []  # No new dependencies. stdlib `re` and `logging` only.

## File Operations (in execution order)

### 1. CREATE fix_templates/script_fixes.py
- operation: CREATE
- reason: Implement the three HIGH-confidence script fix templates required by P6.2: VarToLetConst, RemoveConsoleLog, TemplateLiteralFix

#### Imports / Dependencies
```python
from __future__ import annotations

import logging
import re
from typing import Literal

from fix_templates.base import FixTemplate
from src.models import Confidence, Finding, FixResult
```

#### Module-level constants
```python
logger = logging.getLogger(__name__)
```

#### Class: VarToLetConst

```
class VarToLetConst(FixTemplate):
    confidence: Literal["HIGH"] = "HIGH"
```

Private class attributes (define at class body level, before methods):
```python
_VAR_DECL_RE: re.Pattern[str] = re.compile(r'\bvar\s+(\w+)\s*=')
```

##### Functions

- signature: `def match(self, finding: Finding) -> bool`
  - purpose: Return True if the finding is a ScriptVarUsageRule violation
  - logic:
    1. Return `finding.rule_id == "ScriptVarUsageRule"`
  - returns: `bool`
  - error handling: none

- signature: `def _determine_keyword(self, varname: str, after_context: str) -> str`
  - purpose: Return "let" if varname is reassigned anywhere in after_context, else "const"
  - logic:
    1. Compile pattern: `re.compile(r'\b' + re.escape(varname) + r'\s*(?:\+|-|\*|\/|%)?=(?!=)')`
    2. If pattern.search(after_context) returns a match, return `"let"`
    3. Otherwise return `"const"`
  - returns: `str` (literal `"let"` or `"const"`)
  - error handling: none; re.escape ensures varname is safe

- signature: `def apply(self, finding: Finding, source_content: str) -> FixResult | None`
  - purpose: Replace `var` declarations on the finding's line with `let` or `const`
  - logic:
    1. If `finding.line == 0`, return `None`
    2. Call `source_content.splitlines(keepends=True)` and assign to `lines: list[str]`
    3. If `finding.line > len(lines)`, return `None`
    4. Assign `target_idx: int = finding.line - 1`
    5. Assign `target_line: str = lines[target_idx]`
    6. If `self._VAR_DECL_RE.search(target_line)` is None, return `None`
    7. Assign `after_context: str = "".join(lines[target_idx + 1:])`
    8. Define inner function `_replacer(m: re.Match[str]) -> str`:
       - Extract `varname: str = m.group(1)`
       - Call `keyword: str = self._determine_keyword(varname, after_context)`
       - Return `m.group(0).replace("var", keyword, 1)` — replaces only the keyword `var` (the first occurrence in the matched string, which is always the declaration keyword since the regex anchors to `\bvar\s+`)
    9. Call `modified_line: str = self._VAR_DECL_RE.sub(_replacer, target_line)`
    10. If `modified_line == target_line`, return `None`
    11. Assign `lines[target_idx] = modified_line`
    12. Return `FixResult(finding=finding, original_content=source_content, fixed_content="".join(lines), confidence=Confidence.HIGH)`
  - returns: `FixResult | None`
  - error handling: All guard clauses at the top (steps 1-3 and 6) return None for unexpected input

#### Class: RemoveConsoleLog

```
class RemoveConsoleLog(FixTemplate):
    confidence: Literal["HIGH"] = "HIGH"
```

Private class attributes:
```python
_CONSOLE_RE: re.Pattern[str] = re.compile(
    r'console\.(log|warn|error|info|debug)\s*\([^()]*\)\s*;?'
)
```

Note on pattern safety: `[^()]*` intentionally rejects nested parentheses (e.g. `console.log(getMsg())`). If nested parens are present, the pattern will not match and `apply()` returns None.

##### Functions

- signature: `def match(self, finding: Finding) -> bool`
  - purpose: Return True if the finding is a ScriptConsoleLogRule violation
  - logic:
    1. Return `finding.rule_id == "ScriptConsoleLogRule"`
  - returns: `bool`
  - error handling: none

- signature: `def apply(self, finding: Finding, source_content: str) -> FixResult | None`
  - purpose: Remove the console.* call on the finding's line; remove the entire line if it becomes empty
  - logic:
    1. If `finding.line == 0`, return `None`
    2. Call `source_content.splitlines(keepends=True)` and assign to `lines: list[str]`
    3. If `finding.line > len(lines)`, return `None`
    4. Assign `target_idx: int = finding.line - 1`
    5. Assign `target_line: str = lines[target_idx]`
    6. If `self._CONSOLE_RE.search(target_line)` is None, return `None` (pattern didn't match -- likely has nested parens or not a simple call)
    7. Assign `modified_line: str = self._CONSOLE_RE.sub("", target_line)`
    8. If `"console."` in modified_line, return `None` (partial removal -- unexpected; a second console call on same line or regex left a fragment; unsafe to apply)
    9. Assign `stripped: str = modified_line.strip()`
    10. If `stripped == ""` or `stripped in ("%>", "<%")`:
        - Call `lines.pop(target_idx)` to remove the now-empty line entirely
    11. Else:
        - Assign `lines[target_idx] = modified_line`
    12. Return `FixResult(finding=finding, original_content=source_content, fixed_content="".join(lines), confidence=Confidence.HIGH)`
  - returns: `FixResult | None`
  - error handling: Guard clauses at steps 1-3, 6, and 8 return None for unsafe cases

#### Class: TemplateLiteralFix

```
class TemplateLiteralFix(FixTemplate):
    confidence: Literal["HIGH"] = "HIGH"
```

Private class attributes:
```python
# Pattern A: 'literal_without_special_chars' + identifier
_CONCAT_A_RE: re.Pattern[str] = re.compile(r"'([^'\\`\${}]*)'\s*\+\s*(\w+)")

# Pattern B: identifier + 'literal_without_special_chars'
_CONCAT_B_RE: re.Pattern[str] = re.compile(r"(\w+)\s*\+\s*'([^'\\`\${}]*)'")
```

Note on pattern safety: The literal capture group `[^'\\`\${}]*` excludes: single quotes, backslashes, backticks, `$`, `{`, `}`. This prevents generating broken template literals or interfering with existing template literal syntax in the source.

##### Functions

- signature: `def match(self, finding: Finding) -> bool`
  - purpose: Return True if the finding is a ScriptStringConcatRule violation
  - logic:
    1. Return `finding.rule_id == "ScriptStringConcatRule"`
  - returns: `bool`
  - error handling: none

- signature: `def apply(self, finding: Finding, source_content: str) -> FixResult | None`
  - purpose: Convert a simple string concatenation on the finding's line to a template literal; only applies for exactly one match of pattern A or B, never both
  - logic:
    1. If `finding.line == 0`, return `None`
    2. Call `source_content.splitlines(keepends=True)` and assign to `lines: list[str]`
    3. If `finding.line > len(lines)`, return `None`
    4. Assign `target_idx: int = finding.line - 1`
    5. Assign `target_line: str = lines[target_idx]`
    6. Call `matches_a: list[tuple[str, str]] = self._CONCAT_A_RE.findall(target_line)` — returns list of (literal, varname) tuples
    7. Call `matches_b: list[tuple[str, str]] = self._CONCAT_B_RE.findall(target_line)` — returns list of (varname, literal) tuples
    8. If `len(matches_a) == 1` and `len(matches_b) == 0`:
       - Call `m = self._CONCAT_A_RE.search(target_line)` (guaranteed non-None by step 6)
       - Assign `literal: str = m.group(1)`, `varname: str = m.group(2)`
       - Assign `replacement: str = f"`{literal}${{{varname}}}`"` — backtick-delimited template literal with variable interpolation
       - Assign `modified_line: str = target_line[:m.start()] + replacement + target_line[m.end():]`
    9. Elif `len(matches_b) == 1` and `len(matches_a) == 0`:
       - Call `m = self._CONCAT_B_RE.search(target_line)` (guaranteed non-None by step 7)
       - Assign `varname: str = m.group(1)`, `literal: str = m.group(2)`
       - Assign `replacement: str = f"`${{{varname}}}{literal}`"` — backtick-delimited template literal with variable interpolation
       - Assign `modified_line: str = target_line[:m.start()] + replacement + target_line[m.end():]`
    10. Else (both matched, neither matched, or multiple matches of either):
        - return `None`
    11. If `modified_line == target_line`, return `None`
    12. Assign `lines[target_idx] = modified_line`
    13. Return `FixResult(finding=finding, original_content=source_content, fixed_content="".join(lines), confidence=Confidence.HIGH)`
  - returns: `FixResult | None`
  - error handling: Guard clauses at steps 1-3 and 10 return None for line-out-of-range or ambiguous/complex patterns

#### Wiring / Integration
- This file requires no registration call. `FixTemplateRegistry._discover_templates()` in `fix_templates/base.py` auto-discovers all `FixTemplate` subclasses via `pkgutil.walk_packages` on the `fix_templates` package. Adding this module to the package makes all three classes discoverable automatically.
- Each class must have `confidence: Literal["HIGH"] = "HIGH"` as a CLASS-LEVEL ASSIGNMENT (not just a type annotation). The registry checks `inspect.getattr_static(cls, "confidence")` returns a `str` instance -- an annotation-only declaration would not pass this check and the template would be silently skipped.
- `FixResult.confidence` expects a `Confidence` enum value. Always pass `confidence=Confidence.HIGH`, not the string `"HIGH"`.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from fix_templates.script_fixes import VarToLetConst, RemoveConsoleLog, TemplateLiteralFix; print('import ok')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile fix_templates/script_fixes.py && echo "syntax ok"`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q`
- smoke: Run the following Python snippet to verify all three templates are discovered by the registry:
  ```python
  cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
  from fix_templates.base import FixTemplateRegistry
  from src.models import Finding, Severity
  reg = FixTemplateRegistry()
  print('Discovered templates:', [type(t).__name__ for t in reg.templates])

  # Test VarToLetConst matches
  f = Finding(rule_id='ScriptVarUsageRule', severity=Severity.ADVICE, message='test', file_path='test.script', line=1)
  matches = reg.find_matching(f)
  assert any(type(t).__name__ == 'VarToLetConst' for t in matches), 'VarToLetConst not matched'

  # Test RemoveConsoleLog matches
  f2 = Finding(rule_id='ScriptConsoleLogRule', severity=Severity.ADVICE, message='test', file_path='test.script', line=1)
  matches2 = reg.find_matching(f2)
  assert any(type(t).__name__ == 'RemoveConsoleLog' for t in matches2), 'RemoveConsoleLog not matched'

  # Test TemplateLiteralFix matches
  f3 = Finding(rule_id='ScriptStringConcatRule', severity=Severity.ADVICE, message='test', file_path='test.pmd', line=1)
  matches3 = reg.find_matching(f3)
  assert any(type(t).__name__ == 'TemplateLiteralFix' for t in matches3), 'TemplateLiteralFix not matched'

  print('All match assertions passed')
  "
  ```

## Constraints
- Do NOT create any test files (tests are in P6.5).
- Do NOT modify `fix_templates/__init__.py`, `fix_templates/base.py`, `src/models.py`, or any existing file.
- Do NOT add any new package dependencies to `pyproject.toml`. Use only `re`, `logging`, and `typing` from stdlib plus existing project imports.
- Do NOT use `print()` for any output -- use `logging` only.
- The `confidence` attribute on each class MUST be a class-level string assignment: `confidence: Literal["HIGH"] = "HIGH"`. Do NOT make it annotation-only, do NOT assign `Confidence.HIGH` (the enum) to it -- the registry check `isinstance(inspect.getattr_static(cls, "confidence"), str)` requires a raw string.
- The `FixResult` constructor call MUST use `confidence=Confidence.HIGH` (the enum value from `src.models`), NOT the string `"HIGH"`. `FixResult.confidence` is typed as `Confidence` (enum).
- The `_VAR_DECL_RE` pattern MUST NOT match `var` inside identifiers. The `\b` word boundary at the start ensures `evar` or `myvar` are not matched. Verify the `\b` is present.
- The `_CONSOLE_RE` pattern uses `[^()]*` intentionally to reject nested parentheses -- do NOT change it to a broader pattern. The explicit limitation to flat argument lists is what makes this HIGH confidence.
- The `_CONCAT_A_RE` and `_CONCAT_B_RE` patterns use `[^'\\`\${}]*` for the literal portion -- do NOT relax these exclusions. They prevent mishandling literals that already contain template literal syntax or escape sequences.
- All three `apply()` methods must return `None` (not raise) when they cannot safely apply the fix. The caller (`fixer.py`, in P6.4) expects None to mean "skip this template".
