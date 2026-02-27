# Review Report — P6.2

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`py_compile` clean, imports succeed)
- Tests: PASS (177/177 passed)
- Lint: PASS (`ruff check` clean)
- Docker: SKIPPED (no Docker files changed)

## Findings

```json
{
  "high": [
    {
      "file": "fix_templates/script_fixes.py",
      "line": 159,
      "issue": "TemplateLiteralFix Pattern B (_CONCAT_B_RE) produces syntactically invalid JavaScript when the left-hand side of a concatenation is a property access. Example: `this.name + 'suffix'` → the regex matches `name` (last word before `+`), leaving `this.` as a prefix: result is `this.`${name}suffix`` which is invalid JS. Property access `obj.prop + 'str'` → `obj.\`${prop}str\`` similarly breaks. Confirmed via runtime test: input `\"this.name + 'suffix'\"` produced `'this.`${name}suffix`'`. No guard exists to detect that `m.start()-1` is `.`.",
      "category": "logic"
    },
    {
      "file": "fix_templates/script_fixes.py",
      "line": 153,
      "issue": "TemplateLiteralFix Pattern A (_CONCAT_A_RE) produces syntactically invalid JavaScript when the right-hand side of a concatenation is a property access. The pattern `'([^'...]*)'\\ s*\\+\\s*(\\w+)\\b(?!\\s*\\()` stops at the first word of a dotted expression. Example: `'Error: ' + this.field` → `_CONCAT_A_RE` matches `this` (stops at `.`), leaving `.field` dangling: result is `` `Error: ${this}`.field `` which is invalid JS. Confirmed via runtime test: input `\"'Error: ' + this.field\"` produced `'`Error: ${this}`.field'`. The `(?!\\s*\\()` guard correctly rejects function calls but does NOT reject property accesses (next char after `obj` is `.`, not `(`).",
      "category": "logic"
    }
  ],
  "medium": [
    {
      "file": "fix_templates/script_fixes.py",
      "line": 70,
      "issue": "VarToLetConst._replacer checks extra_varnames (multi-var declarations after the first comma) against bare `after_context`, not `primary_context`. `primary_context` includes `same_line_tail + '\\n' + after_context` and is used for the first variable. For `var x = 1, y = 2; y++;` on one line, `y` is mutated in `same_line_tail` (` 2; y++;`) but `extra_varnames` check only searches `after_context` (empty). Result: `y` is classified as `const`, producing `const x = 1, y = 2; y++;` — a runtime TypeError (const reassignment). Confirmed via runtime test.",
      "category": "logic"
    },
    {
      "file": "fix_templates/script_fixes.py",
      "line": 78,
      "issue": "`_VAR_DECL_RE.sub(_replacer, target_line)` replaces ALL regex matches on the line, including `var x =` patterns embedded in string literals. Example: `var x = \"var y = 5\"` has two matches: `var x =` (code) and `var y =` (inside string). Both are replaced, producing `const x = \"const y = 5\"` — the string value is corrupted. `re.sub` has no awareness of string literal context. Confirmed via runtime test.",
      "category": "logic"
    }
  ],
  "low": [],
  "validated": [
    "Syntax compiles clean (py_compile)",
    "All 177 tests pass",
    "Ruff lint passes with no issues",
    "All three classes correctly use `confidence: Literal[\"HIGH\"] = \"HIGH\"` as a class-level string assignment (not annotation-only), satisfying `inspect.getattr_static` check in registry",
    "All three `apply()` methods use `confidence=Confidence.HIGH` (enum) for FixResult construction, not the string",
    "`_VAR_DECL_RE` correctly uses `\\bvar` word boundary — does not match `evar` or `myvar`",
    "`_CONSOLE_RE` correctly uses `[^()]*` to reject nested parens, making RemoveConsoleLog conservative and safe",
    "`_determine_keyword` comprehensively detects compound assignments (+=, -=, *=, **=, &&=, ||=, ??=, >>=, >>>=, <<=, ++, --) and plain assignment",
    "VarToLetConst correctly uses `primary_context` (same_line_tail + after_context) for the FIRST variable in a declaration — same-line mutations like `for (var i = 0; i < n; i++)` are handled correctly",
    "TemplateLiteralFix correctly returns None when both patterns match, neither matches, or either has multiple matches — ambiguous/chained concatenations are not auto-fixed",
    "`_CONCAT_A_RE` `(?!\\s*\\()` lookahead correctly rejects function calls (e.g., `'str' + fn()` is not transformed)",
    "FixTemplateRegistry auto-discovery works: all three classes are discovered without manual registration"
  ]
}
```
