# Plan: P2.3

## Dependencies
- list: []
- commands: []
  (No new Python packages required. All files are plain JSON or standalone JS data files.)

## File Operations (in execution order)

### 1. CREATE tests/fixtures/clean_app/minimalPage.pmd
- operation: CREATE
- reason: Minimal valid Workday Extend PMD page file with zero rule violations -- required as input for clean-scan tests

#### Content
The file is a JSON document. Write the following content exactly:

```json
{
  "id": "minimalPage",
  "securityDomains": ["Everyone"],
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
          "type": "richText",
          "id": "footerText",
          "value": "Footer"
        }
      ]
    }
  },
  "script": "<% const greeting = 'Hello'; let count = 0; %>"
}
```

Design rationale (do NOT include this block in the file -- it is for the builder's reference only):
- `"id": "minimalPage"` -- the parser reads the `"id"` key and assigns it to `PMDModel.pageId`; filename `minimalPage.pmd` is lowerCamelCase so `FileNameLowerCamelCaseRule` does not trigger
- `"securityDomains": ["Everyone"]` -- non-empty list satisfies `PMDSecurityDomainRule` (ACTION)
- All widgets in `body` and `footer` have explicit `"id"` fields -- satisfies `WidgetIdRequiredRule` (ACTION)
- `"script"` uses `const` and `let`, no `var` -- satisfies `ScriptVarUsageRule` (ADVICE)
- No `console.log`, `console.warn`, `console.error`, or `console.debug` in any script field -- satisfies `ScriptConsoleLogRule` (ACTION)
- `0` appears only as a named-variable initialiser (`let count = 0`), not in an expression context -- satisfies `ScriptMagicNumberRule` (ADVICE)
- No `*.workday.com` URLs anywhere -- satisfies `HardcodedWorkdayAPIRule` (ACTION)

---

### 2. CREATE tests/fixtures/clean_app/minimalPod.pod
- operation: CREATE
- reason: Minimal valid Workday Extend POD file with zero rule violations

#### Content
The file is a JSON document. Write the following content exactly:

```json
{
  "podId": "minimalPod",
  "seed": {
    "parameters": [],
    "endPoints": [
      {
        "name": "getWorkerData",
        "url": "<% apiGatewayEndpoint + '/workers/me' %>"
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

Design rationale (do NOT include this block in the file):
- `"podId": "minimalPod"` -- lowerCamelCase; filename `minimalPod.pod` is lowerCamelCase
- Endpoint `"url"` uses `apiGatewayEndpoint` template expression, not a hardcoded `*.workday.com` domain -- satisfies `HardcodedWorkdayAPIRule` (ACTION)
- Template widget has `"id": "workerText"` -- satisfies `WidgetIdRequiredRule` (ACTION)

---

### 3. CREATE tests/fixtures/clean_app/utils.script
- operation: CREATE
- reason: Minimal valid Workday Extend standalone script file with zero rule violations

#### Content
The file is a plain text JS-like file (no `<%` wrapper -- standalone `.script` files are not wrapped). Write the following content exactly:

```javascript
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

Design rationale (do NOT include this block in the file):
- Both `getCurrentTime` and `formatName` are declared with `const` (not `var`) -- satisfies `ScriptVarUsageRule`
- Both functions are exported in the trailing object literal -- satisfies `ScriptDeadCodeRule` (the "unused function" rule for standalone scripts)
- No `console.log` calls -- satisfies `ScriptConsoleLogRule`
- No bare numeric literals used in expressions -- satisfies `ScriptMagicNumberRule`
- The trailing object literal `{ "getCurrentTime": getCurrentTime, "formatName": formatName }` is the standard Workday Extend export pattern for standalone `.script` files

---

### 4. CREATE tests/fixtures/dirty_app/dirtyPage.pmd
- operation: CREATE
- reason: PMD file containing exactly four known violations: ScriptVarUsageRule, ScriptConsoleLogRule, ScriptMagicNumberRule, WidgetIdRequiredRule

#### Content
The file is a JSON document. Write the following content exactly:

```json
{
  "id": "dirtyPage",
  "securityDomains": ["Everyone"],
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
  },
  "script": "<% var count = 0; console.log(count); if (count > 42) { count = 100; } %>"
}
```

Violations this file intentionally contains (do NOT include this block in the file):
1. `var count` in the `"script"` field -- triggers `ScriptVarUsageRule` (ADVICE)
2. `console.log(count)` in the `"script"` field -- triggers `ScriptConsoleLogRule` (ACTION)
3. `42` in `count > 42` and `100` in `count = 100` are bare numeric literals in expression context -- triggers `ScriptMagicNumberRule` (ADVICE); note: `0` in `var count = 0` is a named-variable initialiser and may not trigger this rule
4. The `"type": "text"` widget under `body.children` has no `"id"` field -- triggers `WidgetIdRequiredRule` (ACTION)

---

### 5. CREATE tests/fixtures/dirty_app/dirtyPod.pod
- operation: CREATE
- reason: POD file containing exactly one known violation: HardcodedWorkdayAPIRule

#### Content
The file is a JSON document. Write the following content exactly:

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

Violations this file intentionally contains (do NOT include this block in the file):
1. `"url": "https://api.workday.com/common/v1/workers"` is a hardcoded `*.workday.com` URL in an endpoint `"url"` field -- triggers `HardcodedWorkdayAPIRule` (ACTION)

The rule `HardcodedWorkdayAPIRule.visit_pod()` iterates `pod_model.seed.endPoints`, calls `_check_endpoint_url(endpoint, pod_model, 'pod', i)`, which reads `endpoint.get('url', '')` and runs a regex match against `*.workday.com`.

---

### 6. CREATE tests/fixtures/dirty_app/helpers.script
- operation: CREATE
- reason: Standalone script file containing exactly one known violation: ScriptDeadCodeRule (unused function not exported or used internally)

#### Content
The file is a plain text JS-like file. Write the following content exactly:

```javascript
const formatDate = function(date) {
  return date:getTodaysDate(date);
};

const unusedHelper = function() {
  return "not exported or used";
};

{
  "formatDate": formatDate
}
```

Violations this file intentionally contains (do NOT include this block in the file):
1. `unusedHelper` is declared with `const` but is neither exported in the trailing object literal nor called by any other function in the file -- triggers `ScriptDeadCodeRule` (ADVICE) with a message containing "neither exported nor used internally"

`formatDate` IS exported in the trailing object literal, so it does not trigger the rule. `unusedHelper` is NOT in the export object and is NOT called by `formatDate` or any other code, so it IS flagged as dead code.

---

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_scanner.py -v`
  (existing scanner tests must all pass -- they do not test file content, just that the scanner finds files by extension)

- lint: no lint step for data files

- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_scanner.py -v`

- smoke:
  1. Verify the scanner finds exactly 3 files in clean_app:
     `cd /Users/name/homelab/ArcaneAuditor/agents && python -c "from pathlib import Path; from src.scanner import scan_local; m = scan_local(Path('tests/fixtures/clean_app')); print(m.total_count, m.files_by_type)"`
     Expected: `total_count=3`, one file each in `pmd`, `pod`, `script` keys.

  2. Verify the scanner finds exactly 3 files in dirty_app:
     `cd /Users/name/homelab/ArcaneAuditor/agents && python -c "from pathlib import Path; from src.scanner import scan_local; m = scan_local(Path('tests/fixtures/dirty_app')); print(m.total_count, m.files_by_type)"`
     Expected: `total_count=3`, one file each in `pmd`, `pod`, `script` keys.

  3. Verify clean_app has zero ACTION findings when run through the parent tool:
     `cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/clean_app --format json --quiet`
     Expected: exit code 0 (or at most ADVICE-only findings which also yield exit code 0).

  4. Verify dirty_app has ACTION findings when run through the parent tool:
     `cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/dirty_app --format json --quiet`
     Expected: exit code 1 (ACTION issues found). The JSON output must contain findings for `ScriptConsoleLogRule`, `ScriptVarUsageRule`, `ScriptMagicNumberRule`, `WidgetIdRequiredRule`, and `HardcodedWorkdayAPIRule`.

## Constraints

- Do NOT create any `.py` files -- this task is purely data file creation
- Do NOT modify `src/scanner.py`, `src/models.py`, `src/config.py`, or any existing test file
- Do NOT create `tests/fixtures/__init__.py` -- the fixtures directory is a data directory, not a Python package
- Do NOT create `tests/fixtures/expected/` -- that is scope for a later task (P3.3 specifies expected output for runner tests)
- Do NOT add Python imports or boilerplate to the JSON fixture files -- they must be pure JSON
- The `.script` file content must NOT be wrapped in `<% %>` -- standalone `.script` files use raw JS syntax (no template wrappers); the `<% %>` wrapper is only for embedded script blocks within `.pmd` and `.pod` JSON field values
- The file encoding must be UTF-8
- If smoke test 3 reveals that the clean_app files trigger ACTION violations (exit code 1 instead of 0), fix the offending fixture file content before moving on -- the clean_app fixture MUST produce exit code 0
- If smoke test 4 reveals that the parent tool produces exit code 0 for dirty_app (meaning it found no ACTION violations), check that the JSON fields match exactly what the parser expects (e.g., the endpoint `"url"` field must be at the top level of the endpoint object, not nested)
