# Review Report — P6.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -c "from fix_templates.structure_fixes import ..."` exits clean)
- Tests: PASS (219 passed in 4.52s — no regressions)
- Lint: PASS (`ruff check fix_templates/structure_fixes.py` — all checks passed)
- Docker: SKIPPED (no compose files changed in this task)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "fix_templates/structure_fixes.py",
      "line": 299,
      "issue": "Sort key in _add_missing_codes crashes unhandled. `ep[\"failOnStatusCodes\"].sort(key=lambda e: int(e.get(\"code\", 0)) ...)` calls int() inside the lambda without exception handling. When an existing entry has {\"code\": null} (JSON null -> Python None), int(None) raises TypeError. When an entry has {\"code\": \"abc\"} (non-numeric string), int(\"abc\") raises ValueError. Both propagate unhandled through _fix_endpoint_in_data and apply(). The apply() method only catches json.JSONDecodeError, so this crash escapes to the caller. The documented contract -- 'apply() returns FixResult | None' -- is violated. Verified: reproducing with source containing {\"code\": null} raises TypeError from apply().",
      "category": "crash"
    }
  ],
  "low": [
    {
      "file": "fix_templates/structure_fixes.py",
      "line": 155,
      "issue": "LowerCamelCaseEndpointName.apply() calls self._MSG_RE.search() on a pattern anchored with '^'. With no MULTILINE flag, search() with '^' only matches at position 0 -- functionally identical to .match() for single-line inputs, but misleading. Should use .match() for idiomatic clarity.",
      "category": "style"
    },
    {
      "file": "fix_templates/structure_fixes.py",
      "line": 103,
      "issue": "The guard 'if \"<\" in invalid_id: return None' in LowerCamelCaseWidgetId.apply() checks for any '<' character, but _to_lower_camel_case() only checks for '<%'. The docstring attributes both to 'script syntax'. In practice _to_lower_camel_case() returns None for any value containing '<' anyway (no pattern matches), so the guard is redundant -- but the inconsistency between the two checks is misleading.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "All three classes import cleanly and register in FixTemplateRegistry (registry smoke test passed: ['RemoveConsoleLog', 'TemplateLiteralFix', 'VarToLetConst', 'AddFailOnStatusCodes', 'LowerCamelCaseEndpointName', 'LowerCamelCaseWidgetId'])",
    "confidence: Literal['HIGH'] = 'HIGH' is a class-level string attribute on all three classes; registry discovery check passes (inspect.getattr_static returns 'HIGH', isinstance(..., str) is True)",
    "_to_lower_camel_case correctly returns None for: empty string, '<%' template syntax, all-uppercase identifiers without separators, values that start with a digit, and values with no recognized form",
    "_to_lower_camel_case separator branch correctly lowercases before split, so mixed-case intermediates are normalized (documented known limitation in docstring)",
    "LowerCamelCaseWidgetId.apply() and LowerCamelCaseEndpointName.apply() both use re.escape() on the extracted identifier when building field_re, preventing regex injection from special characters in the identifier value",
    "Replacement f-strings are safe: fixed_id/fixed_name always match _LOWER_CAMEL_RE (only [a-zA-Z0-9]), so no backslash or backreference characters appear in the substitution string",
    "AddFailOnStatusCodes._extract_endpoint_and_codes correctly handles both message subtypes; missing_codes empty-set guard is present",
    "AddFailOnStatusCodes._add_missing_codes existing_codes loop correctly wraps int() in try/except (ValueError, TypeError) -- the bug is only in the subsequent sort call",
    "All three apply() methods guard against finding.line == 0 and finding.line > len(lines) before accessing the lines list",
    "AddFailOnStatusCodes uses json.loads/json.dumps as required by the plan; LowerCamelCaseWidgetId and LowerCamelCaseEndpointName use line-targeted regex replacement as required",
    "All 219 existing tests pass with no regressions introduced by the new module"
  ]
}
```
