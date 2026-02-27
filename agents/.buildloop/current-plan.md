# Plan: P2.3

## Current State

All 6 fixture files were created by previous WIP build attempts and already exist on disk:
- `tests/fixtures/clean_app/minimalPage.pmd`
- `tests/fixtures/clean_app/minimalPod.pod`
- `tests/fixtures/clean_app/utils.script`
- `tests/fixtures/dirty_app/dirtyPage.pmd`
- `tests/fixtures/dirty_app/dirtyPod.pod`
- `tests/fixtures/dirty_app/helpers.script`

The IMPL_PLAN.md still shows P2.3 as `[ ]`. The task is to verify these files are correct and complete per spec, apply corrections where needed.

## Dependencies
- list: []
- commands: []

## Critical Technical Notes (read before touching any file)

### console.info vs console.log
The task description says "console.log" as the violation type but the `ConsoleLogDetector` checks:
```python
self.console_methods = {'info', 'warn', 'error', 'debug'}
```
`'log'` is NOT in this set. Using `console.log` in the fixture would NOT trigger `ScriptConsoleLogRule`. The existing fixture correctly uses `console.info` which IS detected. Do NOT change `console.info` to `console.log`.

### Unused function in .script files
The task says "one .script with unused function". For standalone `.script` files, `ScriptUnusedFunctionRule._check()` returns an empty generator (explicitly documented in the source). The "unused function" violation in `helpers.script` is instead caught by `ScriptDeadCodeRule`, which detects variables declared at the top level but not exported in the final JSON object. This is correct behavior -- the `unusedHelper` function IS detected as dead code.

### pageId vs id in .pmd files
The task says "valid pageId". The PMD parser reads `pmd_data.get('id', path_obj.stem)` and stores it as `pageId`. Using `"id": "minimalPage"` in the JSON is correct and intentional.

### dirtyPod.pod has an extra violation
The `dirtyPod.pod` has no `failOnStatusCodes` field on its endpoint. This triggers `EndpointFailOnStatusCodesRule` in addition to `HardcodedWorkdayAPIRule`. This is acceptable -- the task spec only requires the hardcoded URL violation, but extra violations do not invalidate the fixture.

## File Operations (in execution order)

### 1. VERIFY tests/fixtures/clean_app/minimalPage.pmd
- operation: VERIFY (existing file -- no changes needed if content matches spec below)
- reason: Confirm the file has valid pageId, script with const/let, all widgets have ids, no violations

#### Expected content (exact)
```json
{
  "id": "minimalPage",
  "securityDomains": ["Everyone"],
  "script": "<% const greeting = 'Hello'; let count = 0; %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Minimal Page"
    },
    "body": {
      "type": "section",
      "id": "bodySection",
      "children": [
        {
          "type": "text",
          "id": "greetingText",
          "label": "Greeting",
          "value": "Hello"
        }
      ]
    },
    "footer": {
      "type": "footer",
      "children": [
        {
          "type": "pod",
          "id": "footerPod"
        }
      ]
    }
  }
}
```

#### Rule analysis for clean_app/minimalPage.pmd
- `PMDSecurityDomainRule`: securityDomains is present and non-empty -- PASS
- `ScriptVarUsageRule`: script uses `const` and `let`, no `var` -- PASS
- `ScriptConsoleLogRule`: no console calls -- PASS
- `ScriptMagicNumberRule`: no magic numbers in script -- PASS
- `WidgetIdRequiredRule`: `section` (bodySection), `text` (greetingText) have ids; `title`, `footer`, `pod` are in the exempt types set -- PASS
- `PMDSectionOrderingRule`: order is id, securityDomains, script, presentation -- matches expected order -- PASS
- `FooterPodRequiredRule`: footer contains a pod widget -- PASS
- `FileNameLowerCamelCaseRule`: "minimalPage" is lowerCamelCase -- PASS
- `HardcodedWorkdayAPIRule`: no endpoints in this file -- PASS

### 2. VERIFY tests/fixtures/clean_app/minimalPod.pod
- operation: VERIFY (existing file -- no changes needed if content matches spec below)
- reason: Confirm valid podId, endpoint uses template literal URL (not hardcoded workday URL), has failOnStatusCodes, all widgets have ids

#### Expected content (exact)
```json
{
  "podId": "minimalPod",
  "seed": {
    "parameters": [],
    "endPoints": [
      {
        "name": "getWorkerData",
        "url": "<% `${baseEndpoint}/workers/me` %>",
        "failOnStatusCodes": [{ "code": 400 }, { "code": 403 }]
      }
    ],
    "template": {
      "type": "text",
      "id": "workerText",
      "label": "Worker",
      "value": "Worker data"
    }
  }
}
```

#### Rule analysis for clean_app/minimalPod.pod
- `HardcodedWorkdayAPIRule`: URL uses `${baseEndpoint}` template expression, not a hardcoded workday.com URL -- PASS
- `EndpointFailOnStatusCodesRule`: failOnStatusCodes present with 400 and 403 -- PASS
- `EndpointNameLowerCamelCaseRule`: "getWorkerData" is lowerCamelCase -- PASS
- `WidgetIdRequiredRule`: template widget `text` has id "workerText" -- PASS
- `FileNameLowerCamelCaseRule`: "minimalPod" is lowerCamelCase -- PASS

### 3. VERIFY tests/fixtures/clean_app/utils.script
- operation: VERIFY (existing file -- no changes needed if content matches spec below)
- reason: Confirm script uses const (not var), all declared functions are exported (no dead code)

#### Expected content (exact)
```
const getCurrentTime = function() {
  return date:getTodaysDate(date:getDateTimeZone('US/Pacific'));
};

const formatName = function(name) {
  return name;
};

{
  "getCurrentTime": getCurrentTime,
  "formatName": formatName
}
```

#### Rule analysis for clean_app/utils.script
- `ScriptVarUsageRule`: uses `const` for both function declarations -- PASS
- `ScriptDeadCodeRule`: both `getCurrentTime` and `formatName` are exported in the final JSON object -- PASS
- `ScriptUnusedFunctionParametersRule`: `name` parameter in `formatName` is used (returned) -- PASS
- `FileNameLowerCamelCaseRule`: "utils" is lowerCamelCase -- PASS

### 4. VERIFY tests/fixtures/dirty_app/dirtyPage.pmd
- operation: VERIFY (existing file -- no changes needed if content matches spec below)
- reason: Confirm the file triggers exactly these violations: ScriptVarUsageRule, ScriptConsoleLogRule, ScriptMagicNumberRule (two numbers: 42 and 100), WidgetIdRequiredRule

#### Expected content (exact)
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
          "type": "pod",
          "id": "footerPod"
        }
      ]
    }
  }
}
```

#### Rule analysis for dirty_app/dirtyPage.pmd
- `ScriptVarUsageRule` (ADVICE): `var count = 0` -- VIOLATION expected
- `ScriptConsoleLogRule` (ACTION): `console.info(msg)` -- VIOLATION expected. NOTE: `console.info` is used, NOT `console.log`. The detector checks `{'info', 'warn', 'error', 'debug'}` and does NOT include `'log'`. Do not change to `console.log`.
- `ScriptMagicNumberRule` (ADVICE): `42` and `100` are both magic numbers (allowed set is only `{0, 1, -1}`) -- TWO VIOLATIONS expected
- `WidgetIdRequiredRule` (ACTION): `"type": "text"` widget in body children has no `"id"` field -- VIOLATION expected
- `StringConcatRule` (ADVICE): `'Count: ' + count` is string concatenation -- VIOLATION also expected (this is an additional violation not listed in the task spec, but acceptable)

### 5. VERIFY tests/fixtures/dirty_app/dirtyPod.pod
- operation: VERIFY (existing file -- no changes needed if content matches spec below)
- reason: Confirm the file triggers HardcodedWorkdayAPIRule

#### Expected content (exact)
```json
{
  "podId": "dirtyPod",
  "seed": {
    "parameters": [],
    "endPoints": [
      {
        "name": "getHrData",
        "url": "https://api.workday.com/common/v1/workers"
      }
    ],
    "template": {
      "type": "text",
      "id": "hrText",
      "label": "HR",
      "value": "HR data"
    }
  }
}
```

#### Rule analysis for dirty_app/dirtyPod.pod
- `HardcodedWorkdayAPIRule` (ACTION): `"url": "https://api.workday.com/common/v1/workers"` matches `*.workday.com` pattern -- VIOLATION expected
- `EndpointFailOnStatusCodesRule` (ACTION or ADVICE): missing `failOnStatusCodes` -- ADDITIONAL VIOLATION (not in task spec but acceptable)
- `FileNameLowerCamelCaseRule`: "dirtyPod" is lowerCamelCase -- PASS

### 6. VERIFY tests/fixtures/dirty_app/helpers.script
- operation: VERIFY (existing file -- no changes needed if content matches spec below)
- reason: Confirm the file triggers dead code violation for unusedHelper (not exported)

#### Expected content (exact)
```
const formatDate = function(date) {
  return date:getTodaysDate(date);
};

var unusedHelper = function() {
  return "not exported or used";
};

{
  "formatDate": formatDate
}
```

#### Rule analysis for dirty_app/helpers.script
- `ScriptDeadCodeRule` (ADVICE): `unusedHelper` is declared at top level but NOT exported in the final JSON object -- VIOLATION expected. NOTE: `ScriptUnusedFunctionRule._check()` returns empty for standalone `.script` files. Dead code is the correct rule.
- `ScriptVarUsageRule` (ADVICE): `var unusedHelper` uses `var` -- ADDITIONAL VIOLATION (expected, acceptable)
- `formatDate` IS exported in the final JSON object -- no dead code violation for it

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q 2>&1 | head -30`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile tests/fixtures/clean_app/utils.script 2>&1 || true` (not Python, so just confirm files are readable)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q`
- smoke-clean: `cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/clean_app --format json --quiet; echo "Exit: $?"` -- expect exit code 0, JSON output with zero ACTION findings
- smoke-dirty: `cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/dirty_app --format json --quiet; echo "Exit: $?"` -- expect exit code 1, JSON output containing findings for: ScriptVarUsageRule, ScriptConsoleLogRule, ScriptMagicNumberRule, WidgetIdRequiredRule, HardcodedWorkdayAPIRule, ScriptDeadCodeRule

## Constraints

- Do NOT change `console.info` to `console.log` in `dirtyPage.pmd`. The `ConsoleLogDetector` checks `{'info', 'warn', 'error', 'debug'}` -- `log` is not detected.
- Do NOT add an `id` field to the `"type": "text"` widget in `dirtyPage.pmd` body children -- that widget is intentionally missing its id (the violation).
- Do NOT add `failOnStatusCodes` to `dirtyPod.pod` -- the missing field causes an additional violation but that is acceptable.
- Do NOT change `var unusedHelper` to `const unusedHelper` in `helpers.script` -- the `var` usage is intentional.
- Do NOT export `unusedHelper` in the `helpers.script` final JSON object -- it must remain dead code.
- Do NOT modify ARCHITECTURE.md, CLAUDE.md, or IMPL_PLAN.md.
- If any of the 6 fixture files are missing or have incorrect content, CREATE or MODIFY them to exactly match the content shown in the VERIFY sections above. The content shown is the exact required content -- no additions or variations.
