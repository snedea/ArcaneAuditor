# Plan: P2.3

## Context

Task: Create test fixtures -- clean_app/ and dirty_app/ directories under tests/fixtures/.

**Current state (from WIP commit 04804b6):** Five of the six required fixture files already exist.
The only gap is that `dirty_app/dirtyPage.pmd` is missing `console.log` in its script field,
which is required by the P2.3 spec ("one .pmd with var usage, console.log, magic numbers, and
a widget missing id").

### Files that already exist and MUST NOT be changed:
- `tests/fixtures/clean_app/minimalPage.pmd` -- has valid `id`, const/let in script, all widgets
  have id fields. Matches spec.
- `tests/fixtures/clean_app/minimalPod.pod` -- has valid `podId`, uses `{apiGatewayEndpoint}`
  template (not hardcoded URL). Matches spec.
- `tests/fixtures/clean_app/utils.script` -- uses const for all function declarations, exports
  both functions. Matches spec.
- `tests/fixtures/dirty_app/dirtyPod.pod` -- has hardcoded `https://api.workday.com/common/v1/workers`
  URL. This triggers `EndpointBaseUrlTypeRule`. Matches spec.
- `tests/fixtures/dirty_app/helpers.script` -- declares `var unusedHelper = function()` which is
  neither exported nor called anywhere. This triggers `ScriptVarUsageRule` (var keyword) and
  `ScriptUnusedFunctionRule` (unused function). Matches spec.

### File that needs modification:
- `tests/fixtures/dirty_app/dirtyPage.pmd` -- EXISTS but script field is missing `console.log`.
  Current script: `"<% var count = 0; const msg = 'Count: ' + count; if (count > 42) { count = 100; } %>"`
  Needed violations: var usage (has it), console.log (MISSING), magic numbers (42, 100 -- has them),
  widget missing id (body text widget has no `id` -- has it).

## Dependencies
- list: []
- commands: []

No new dependencies. These are plain JSON and script files with no build step.

## File Operations (in execution order)

### 1. MODIFY tests/fixtures/dirty_app/dirtyPage.pmd
- operation: MODIFY
- reason: Script field is missing `console.log(msg)` call required by spec
- anchor: `"script": "<% var count = 0; const msg = 'Count: ' + count; if (count > 42) { count = 100; } %>"`

#### Change to make
Replace the `script` field value from:
```
"script": "<% var count = 0; const msg = 'Count: ' + count; if (count > 42) { count = 100; } %>"
```
with:
```
"script": "<% var count = 0; const msg = 'Count: ' + count; if (count > 42) { count = 100; } console.log(msg); %>"
```

This single change adds `console.log(msg)` before the closing `%>` tag. The result triggers:
- `ScriptVarUsageRule` -- `var count` uses `var` instead of `let`/`const`
- `ScriptConsoleLogRule` -- `console.log(msg)` is a console statement
- `ScriptMagicNumberRule` -- `42` and `100` are magic numbers
- `WidgetIdRequiredRule` -- the body `text` widget has no `id` field (existing violation, unchanged)

The full resulting file content must be exactly:
```json
{
  "id": "dirtyPage",
  "securityDomains": ["Everyone"],
  "script": "<% var count = 0; const msg = 'Count: ' + count; if (count > 42) { count = 100; } console.log(msg); %>",
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
No imports or wiring. This is a static fixture file consumed by tests in P2.4 and the runner in P3.3.

## Verification
- build: N/A (no build step for fixture files)
- lint: N/A
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -v 2>&1 | head -60`
  (existing tests in test_scanner.py and test_config.py and test_models.py should all still pass)
- smoke: Run `cat tests/fixtures/dirty_app/dirtyPage.pmd` and confirm the script field contains
  `console.log(msg)` followed by ` %>` (space then closing tag).

## Constraints
- Do NOT modify `tests/fixtures/clean_app/minimalPage.pmd` -- it is already valid
- Do NOT modify `tests/fixtures/clean_app/minimalPod.pod` -- it is already valid
- Do NOT modify `tests/fixtures/clean_app/utils.script` -- it is already valid
- Do NOT modify `tests/fixtures/dirty_app/dirtyPod.pod` -- it is already correct
- Do NOT modify `tests/fixtures/dirty_app/helpers.script` -- it is already correct
- Do NOT add new dependencies to pyproject.toml
- Do NOT modify any Python source files in src/
- Do NOT modify any test files in tests/
- The fixture files are plain JSON (for .pmd and .pod) and plain Workday Script (for .script);
  do not add Python syntax or docstrings to them
- The `console.log(msg)` must appear INSIDE the `<% %>` script tags, not outside
