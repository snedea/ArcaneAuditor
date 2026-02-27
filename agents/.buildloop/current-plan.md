# Plan: P2.3

## Context

All 6 fixture files were created in previous WIP commits and exist on disk. This plan
verifies their content is semantically correct against the parent Arcane Auditor rules
and provides exact content to overwrite them with confirmed, deterministic content.

**Critical finding from rule analysis:**

- `ScriptConsoleLogRule` detects: `{info, warn, error, debug}` — NOT `log`. The dirty
  fixture uses `console.info` which IS detected. The task description says "console.log"
  but that is a loose label; `console.info` is the correct choice.
- `ScriptUnusedFunctionRule` does NOT analyze standalone `.script` files. Its `_check()`
  method returns `yield from []`. The dirty `.script` fixture's unused function is NOT
  detectable by that rule. However, `var unusedHelper` in `helpers.script` IS detected
  by `ScriptVarUsageRule`. Document this in the fixture.
- `FooterPodRequiredRule` (ADVICE) fires when footer children are not of type `pod`.
  The existing `minimalPage.pmd` has `richText` in the footer — it WILL trigger the
  rule. The clean_app fixture MUST be fixed to use a pod child in the footer.
- `ScriptMagicNumberRule` exempts `{0, 1, -1}`. Numbers in `const` declarations are
  also exempt. The clean fixture uses `let count = 0` (0 is exempt) — safe.
- `WidgetIdRequiredRule` exempts these types from the id requirement:
  `{footer, item, group, title, pod, cardContainer, card, instanceList, taskReference,
  editTasks, multiSelectCalendar, bpExtender, hub}`.

## Dependencies

- list: []
- commands: []

## File Operations (in execution order)

### 1. MODIFY tests/fixtures/clean_app/minimalPage.pmd

- operation: MODIFY
- reason: Footer uses richText child which triggers FooterPodRequiredRule (ADVICE). Must
  change footer child to type "pod" to make this fixture violation-free.
- anchor: `"type": "richText",`

#### Content

Replace the entire file with:

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

**Violation analysis — expected zero ACTION findings, zero ADVICE findings:**
- `id` field present: "minimalPage" — passes WidgetIdRequiredRule ✓
- `securityDomains` present and non-empty — passes PMDSecurityDomainRule ✓
- Script uses `const` and `let`, no `var` — passes ScriptVarUsageRule ✓
- `0` is in allowed_numbers {0, 1, -1} — passes ScriptMagicNumberRule ✓
- No console statements — passes ScriptConsoleLogRule ✓
- All widgets with types requiring id have one set (greetingText, bodySection,
  footerPod uses pod type which is exempt) — passes WidgetIdRequiredRule ✓
- Footer child is type "pod" — passes FooterPodRequiredRule ✓
- Section order is id → securityDomains → script → presentation — passes
  PMDSectionOrderingRule ✓
- No hardcoded workday.com URL — passes HardcodedWorkdayAPIRule ✓

### 2. CREATE tests/fixtures/clean_app/minimalPod.pod

- operation: CREATE (overwrite existing with confirmed content)
- reason: Confirm this file contains a valid pod with no violations.

#### Content

Write the entire file as:

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

**Violation analysis — expected zero ACTION findings, zero ADVICE findings:**
- `failOnStatusCodes` present — passes EndpointFailOnStatusCodesRule ✓
- URL uses template expression `${baseEndpoint}`, not hardcoded workday.com —
  passes HardcodedWorkdayAPIRule ✓
- Endpoint name `getWorkerData` is lowerCamelCase — passes
  EndpointNameLowerCamelCaseRule ✓
- Template widget has `id` — passes WidgetIdRequiredRule ✓
- File name `minimalPod` is lowerCamelCase — passes FileNameLowerCamelCaseRule ✓

Note: The existing file uses backtick template literal `{baseEndpoint}`. The
corrected content uses `${baseEndpoint}` (ES6 template literal syntax with `$`).
If the parent parser requires the non-standard `{baseEndpoint}` form without `$`,
revert to the original: `"<% \`{baseEndpoint}/workers/me\` %>"`. The key constraint
is that no hardcoded `*.workday.com` hostname appears in the URL value.

### 3. CREATE tests/fixtures/clean_app/utils.script

- operation: CREATE (overwrite existing with confirmed content)
- reason: Confirm this file contains valid script with no violations.

#### Content

Write the entire file as:

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

**Violation analysis — expected zero ACTION findings, zero ADVICE findings:**
- Uses `const` only, no `var` — passes ScriptVarUsageRule ✓
- No magic numbers — passes ScriptMagicNumberRule ✓
- No console statements — passes ScriptConsoleLogRule ✓
- All declared functions are exported in the trailing object — passes
  ScriptUnusedFunctionRule conceptually (rule does not check .script files) ✓
- `name` and `date` parameters are 4+ chars — passes ScriptDescriptiveParameterRule ✓
- Parameters are used in function bodies — passes ScriptUnusedFunctionParametersRule ✓
- File name `utils` is lowerCamelCase — passes FileNameLowerCamelCaseRule ✓

### 4. CREATE tests/fixtures/dirty_app/dirtyPage.pmd

- operation: CREATE (overwrite existing with confirmed content)
- reason: Confirm this file contains known violations for use in runner tests.

#### Content

Write the entire file as:

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

**Intended detectable violations:**
- `var count` → ScriptVarUsageRule (ADVICE): uses var instead of let/const
- `console.info(msg)` → ScriptConsoleLogRule (ACTION): console.info is in the
  detected set {info, warn, error, debug}
- `42` → ScriptMagicNumberRule (ADVICE): not in allowed {0, 1, -1}, not in const decl
- `100` → ScriptMagicNumberRule (ADVICE): not in allowed {0, 1, -1}
- `'Count: ' + count` → ScriptStringConcatRule (ADVICE): string concatenation
- Widget `{"type": "text", "value": "Missing ID widget"}` has no `id` field →
  WidgetIdRequiredRule (ACTION): widget missing required id

**Note on footer:** The footer uses a pod child to avoid triggering FooterPodRequiredRule.
This keeps the violation set limited to the intended violations listed above. If the
intention is to also have a footer violation, the footer can be changed back to the
richText version — but that adds an unintended violation to the dirty_app that tests
in P3.3 would need to account for.

### 5. CREATE tests/fixtures/dirty_app/dirtyPod.pod

- operation: CREATE (overwrite existing with confirmed content)
- reason: Confirm this file contains a hardcoded Workday API URL violation.

#### Content

Write the entire file as:

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

**Intended detectable violations:**
- `https://api.workday.com/common/v1/workers` → HardcodedWorkdayAPIRule (ACTION):
  matches `*.workday.com` URL pattern
- Missing `failOnStatusCodes` field → EndpointFailOnStatusCodesRule (ADVICE)

### 6. CREATE tests/fixtures/dirty_app/helpers.script

- operation: CREATE (overwrite existing with confirmed content)
- reason: Confirm this file contains a var usage violation (primary detectable violation
  for .script files).

#### Content

Write the entire file as:

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

**Intended detectable violations:**
- `var unusedHelper` → ScriptVarUsageRule (ADVICE): uses var instead of let/const

**Limitation note:** The task description says "unused function" but
ScriptUnusedFunctionRule.`_check()` returns `yield from []`, so it never fires for
standalone `.script` files (it only fires via `_analyze_fields` for PMD/POD script
sections). The `unusedHelper` function is semantically unused (not exported in the
trailing object, never called), but this is NOT detectable by the current rule
implementation. The var usage IS detectable and serves as the observable violation.
Runner tests in P3.3 must assert ScriptVarUsageRule fires, NOT ScriptUnusedFunctionRule,
for this file.

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.scanner import scan_local; from pathlib import Path; m = scan_local(Path('tests/fixtures/clean_app')); print('clean_app total:', m.total_count, 'pmd:', len(m.files_by_type['pmd']), 'pod:', len(m.files_by_type['pod']), 'script:', len(m.files_by_type['script']))"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.scanner import scan_local; from pathlib import Path; m = scan_local(Path('tests/fixtures/dirty_app')); print('dirty_app total:', m.total_count, 'pmd:', len(m.files_by_type['pmd']), 'pod:', len(m.files_by_type['pod']), 'script:', len(m.files_by_type['script']))"`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_scanner.py -v`
- smoke: `cd /Users/name/homelab/ArcaneAuditor && uv run main.py review-app agents/tests/fixtures/clean_app --format json --quiet; echo "clean_app exit=$?"; uv run main.py review-app agents/tests/fixtures/dirty_app --format json --quiet; echo "dirty_app exit=$?"`

Expected smoke results:
- `clean_app exit=0` (zero ACTION findings)
- `dirty_app exit=1` (at least one ACTION finding: ScriptConsoleLogRule or
  WidgetIdRequiredRule or HardcodedWorkdayAPIRule)

## Constraints

- Do NOT modify ARCHITECTURE.md, CLAUDE.md, IMPL_PLAN.md
- Do NOT create tests/fixtures/expected/ — that directory is created in P3.3
- Do NOT add any Python (.py) files — this task only creates data fixture files
- Do NOT modify tests/fixtures/test-config.json — it is pre-existing configuration
- The 6 fixture files are the ONLY outputs of this task
- Do NOT create a conftest.py or any pytest infrastructure — P2.4 handles that
- After creating files, run the smoke verification command above before marking done
- If the clean_app smoke test exits non-zero, debug which rule is firing and adjust
  the fixture content to eliminate the violation before completing the task
- If the dirty_app smoke test exits zero, debug why no ACTION violations are detected
  and adjust the dirty fixtures accordingly
