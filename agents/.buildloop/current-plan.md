# Plan: P2.3

## Dependencies
- list: []
- commands: []

## Current State Assessment

Five of six fixture files already exist from a prior incomplete build of P2.3.
The only missing requirement is a console statement violation in `dirty_app/dirtyPage.pmd`.

Fixture inventory and status:

| File | Status | Violations present |
|---|---|---|
| clean_app/minimalPage.pmd | COMPLETE | none (all widgets have ids, uses const/let) |
| clean_app/minimalPod.pod | COMPLETE | none (template URL, has failOnStatusCodes 400+403) |
| clean_app/utils.script | COMPLETE | none (uses const, all functions exported) |
| dirty_app/dirtyPage.pmd | INCOMPLETE | var usage, magic numbers, widget missing id -- MISSING console statement |
| dirty_app/dirtyPod.pod | COMPLETE | hardcoded workday.com URL |
| dirty_app/helpers.script | COMPLETE | var usage + unused function (not in export object) |

## File Operations (in execution order)

### 1. MODIFY tests/fixtures/dirty_app/dirtyPage.pmd
- operation: MODIFY
- reason: The script block is missing a console statement. The task requires "console.log" as a violation; the parent tool's ConsoleLogDetector fires on `console.info`, `console.warn`, `console.error`, `console.debug` -- NOT on `console.log` (that method name is absent from the detector's `console_methods` set). Use `console.info` to reliably trigger ScriptConsoleLogRule.
- anchor: `"script": "<% var count = 0; const msg = 'Count: ' + count; if (count > 42) { count = 100; } %>"`

#### Change
Replace the `script` field value. The change is a single string substitution on line 4 of the file.

Old `script` value (exact string):
```
"<% var count = 0; const msg = 'Count: ' + count; if (count > 42) { count = 100; } %>"
```

New `script` value (exact string):
```
"<% var count = 0; const msg = 'Count: ' + count; console.info(msg); if (count > 42) { count = 100; } %>"
```

The full modified file content must be:
```json
{
  "id": "dirtyPage",
  "securityDomains": ["Everyone"],
  "script": "<% var count = 0; const msg = 'Count: ' + count; console.info(msg); if (count > 42) { count = 100; } %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Dirty Page"
    },
    "body": {
      "type": "section",
      "id": "bodySection",
      "children": [
        {
          "type": "text",
          "value": "Missing ID widget"
        }
      ]
    },
    "footer": {
      "type": "footer",
      "children": [
        {
          "type": "richText",
          "id": "footerText",
          "value": "Footer"
        }
      ]
    }
  }
}
```

#### Wiring / Integration
- No Python imports or code changes. This is a static fixture file.
- The dirty_app fixture is consumed by tests/test_runner.py (P3.3) and tests/test_scanner.py (P2.4).
- test_scanner.py does not read file contents; it only checks file counts by extension. No changes to test_scanner.py needed.

## Violation Inventory After This Change

### clean_app/ -- expected: 0 violations
- minimalPage.pmd: valid pageId "minimalPage", script uses `const greeting` and `let count`, all widgets have `id` except `footer`/`title` types (those are in `BUILT_IN_WIDGET_TYPES_WITHOUT_ID_REQUIREMENT`)
- minimalPod.pod: endpoint URL uses `<% \`{baseEndpoint}/workers/me\` %>` (no hardcoded workday.com), has `failOnStatusCodes` with codes 400 and 403
- utils.script: uses `const` throughout, both functions (`getCurrentTime`, `formatName`) appear in the export object

### dirty_app/ -- expected: multiple violations across files

dirtyPage.pmd violations (4):
1. ScriptVarUsageRule (ADVICE) -- `var count = 0`
2. ScriptConsoleLogRule (ACTION) -- `console.info(msg)`
3. ScriptMagicNumberRule (ADVICE) -- magic numbers `42` and `100`
4. WidgetIdRequiredRule (ACTION) -- text widget in body.children has no `id` field

dirtyPod.pod violations (2):
1. EndpointBaseUrlTypeRule (ADVICE) -- URL contains `workday.com`
2. EndpointFailOnStatusCodesRule (ACTION) -- endpoint `getHrData` has no `failOnStatusCodes` field

helpers.script violations (2):
1. ScriptVarUsageRule (ADVICE) -- `var unusedHelper = function() { ... }`
2. ScriptUnusedFunctionRule (ADVICE) -- `unusedHelper` is declared but not in the export object and not called

## Critical Implementation Note: console.log vs console.info

The task description says "console.log" but the parent tool's `ConsoleLogDetector` (at
`parser/rules/script/core/console_log_detector.py:14`) defines:
```python
self.console_methods = {'info', 'warn', 'error', 'debug'}
```
`log` is NOT in this set. A fixture using `console.log(msg)` would produce ZERO findings for
the console rule. The fixture MUST use `console.info(msg)` (or warn/error/debug) to trigger the
actual rule.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m pytest tests/test_scanner.py -v`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m pytest --collect-only 2>&1 | head -20`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m pytest tests/test_scanner.py -v`
- smoke:
  1. Run Arcane Auditor against clean_app and confirm exit 0:
     `cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/clean_app --format json --quiet`
     Expected: exit code 0, JSON output with empty findings array or ADVICE-only findings.
  2. Run Arcane Auditor against dirty_app and confirm exit 1:
     `cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/dirty_app --format json --quiet`
     Expected: exit code 1 (ACTION issues found), JSON with findings including ScriptConsoleLogRule.

## Constraints
- Do NOT modify any file in clean_app/ -- all three clean fixtures are correct as-is.
- Do NOT modify dirty_app/dirtyPod.pod or dirty_app/helpers.script -- they are correct.
- Do NOT create tests/fixtures/expected/ -- that is out of scope for P2.3 (belongs to P3.3).
- Do NOT add new Python source files. This task creates/modifies fixture data files only.
- Do NOT run `uv add` or install any packages. No new dependencies needed.
- The ONLY code change is the `console.info(msg)` addition to dirty_app/dirtyPage.pmd line 4.
