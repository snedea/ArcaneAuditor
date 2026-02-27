# Plan: P2.3

## Context

The fixture files in `tests/fixtures/clean_app/` and `tests/fixtures/dirty_app/` already exist from previous build attempts (5 WIP commits). However, two problems remain:

1. `clean_app/minimalPage.pmd` has `"script": "<% const greeting = 'Hello'; let count = 0; %>"` which triggers `ScriptUnusedVariableRule` (2 ADVICE findings) when run with `test-config.json`. The clean_app must produce **zero findings** per CLAUDE.md: "minimal Extend app with zero violations".

2. `tests/fixtures/expected/` directory does not exist. CLAUDE.md specifies this directory must exist and contain expected JSON output for each fixture, used by future test_runner.py tests (P3.3).

**Root cause of clean_app problem**: `ScriptUnusedVariableRule` checks script content in isolation. It cannot see that variables declared in `<% %>` blocks might be used in presentation template expressions in other fields. Any `const`/`let` variable in a PMD's `script` field that is not referenced WITHIN that same script block is flagged as unused. The `utils.script` file already demonstrates `const` usage throughout the app, satisfying the "script with const/let" intent for the clean fixture set.

## Dependencies

- list: []
- commands: []

## File Operations (in execution order)

### 1. MODIFY tests/fixtures/clean_app/minimalPage.pmd

- operation: MODIFY
- reason: Remove `script` field whose const/let variable declarations trigger ScriptUnusedVariableRule, preventing truly zero findings. The `utils.script` file already demonstrates const/let usage in the clean app.
- anchor: `"script": "<% const greeting = 'Hello'; let count = 0; %>",`

#### New file content (complete replacement)

Write this exact content to `tests/fixtures/clean_app/minimalPage.pmd`:

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
          "type": "pod",
          "id": "footerPod"
        }
      ]
    }
  }
}
```

#### Wiring / Integration

- `utils.script` and `minimalPod.pod` remain unchanged.
- After this change, running `uv run main.py review-app agents/tests/fixtures/clean_app --config agents/tests/fixtures/test-config.json --format json --quiet` from the parent directory (`../`) must produce 0 findings and exit code 0.

---

### 2. CREATE tests/fixtures/expected/clean_app.json

- operation: CREATE
- reason: Store the expected JSON output when running clean_app with test-config.json, used by future test_runner.py (P3.3) to assert zero findings.

#### File content

Write this exact content to `tests/fixtures/expected/clean_app.json`:

```json
{
  "exit_code": 0,
  "findings": []
}
```

#### Notes

- `exit_code: 0` = CLEAN (no ACTION findings; exit 0 also covers ADVICE-only, but after the pmd fix there are zero findings of any severity)
- `findings` array must be empty
- Format: just `exit_code` + `findings` array -- omit `summary` and `context` which contain volatile fields (`total_rules`, `files_missing`) that change as rules are added

---

### 3. CREATE tests/fixtures/expected/dirty_app.json

- operation: CREATE
- reason: Store the expected JSON output when running dirty_app with test-config.json. Contains 11 findings across 3 files, covering the violations specified in IMPL_PLAN.md P2.3.

#### File content

Write this exact content to `tests/fixtures/expected/dirty_app.json`.

The findings are ordered by the tool's output order (not sorted by file or rule). This order is deterministic across runs as long as the fixture files are unchanged.

```json
{
  "exit_code": 1,
  "findings": [
    {
      "rule_id": "ScriptDeadCodeRule",
      "severity": "ADVICE",
      "message": "Top-level variable 'unusedHelper' is declared but neither exported nor used internally. Consider removing if unused.",
      "file_path": "helpers.script",
      "line": 5
    },
    {
      "rule_id": "ScriptMagicNumberRule",
      "severity": "ADVICE",
      "message": "File section 'script' contains magic number '42': 'var count = 0; const msg = 'Count: ' + count; console.info(msg); if (count > 42) { count = 100; }'. Consider using a named constant instead.",
      "file_path": "dirtyPage.pmd",
      "line": 4
    },
    {
      "rule_id": "ScriptMagicNumberRule",
      "severity": "ADVICE",
      "message": "File section 'script' contains magic number '100': 'var count = 0; const msg = 'Count: ' + count; console.info(msg); if (count > 42) { count = 100; }'. Consider using a named constant instead.",
      "file_path": "dirtyPage.pmd",
      "line": 4
    },
    {
      "rule_id": "ScriptVarUsageRule",
      "severity": "ADVICE",
      "message": "File section 'script' uses 'var' declaration for variable 'count'. Consider using 'let' or 'const' instead.",
      "file_path": "dirtyPage.pmd",
      "line": 4
    },
    {
      "rule_id": "ScriptVarUsageRule",
      "severity": "ADVICE",
      "message": "File section 'script' uses 'var' declaration for variable 'unusedHelper'. Consider using 'let' or 'const' instead.",
      "file_path": "helpers.script",
      "line": 5
    },
    {
      "rule_id": "ScriptConsoleLogRule",
      "severity": "ACTION",
      "message": "File section 'script' contains console.info statement. Remove debug statements from production code.",
      "file_path": "dirtyPage.pmd",
      "line": 4
    },
    {
      "rule_id": "ScriptStringConcatRule",
      "severity": "ADVICE",
      "message": "File section 'script' uses string concatenation with + operator: ''Count: ' + count'. Consider using PMD template strings with backticks and { } syntax instead (e.g., `Hello {name}!`).",
      "file_path": "dirtyPage.pmd",
      "line": 4
    },
    {
      "rule_id": "EndpointFailOnStatusCodesRule",
      "severity": "ACTION",
      "message": "Pod endpoint 'getHrData' is missing required 'failOnStatusCodes' field.",
      "file_path": "dirtyPod.pod",
      "line": 1
    },
    {
      "rule_id": "EndpointBaseUrlTypeRule",
      "severity": "ADVICE",
      "message": "Pod endpoint 'getHrData' is pointing to a Workday API, but not leveraging a baseUrlType. Extract Workday endpoints to shared AMD data providers to avoid duplication.",
      "file_path": "dirtyPod.pod",
      "line": 1
    },
    {
      "rule_id": "HardcodedWorkdayAPIRule",
      "severity": "ACTION",
      "message": "Pod endpoint 'getHrData' uses hardcoded *.workday.com URL: 'https://api.workday.com/common/v1/workers'. Use apiGatewayEndpoint instead of hardcoded Workday URLs for regional awareness.",
      "file_path": "dirtyPod.pod",
      "line": 7
    },
    {
      "rule_id": "WidgetIdRequiredRule",
      "severity": "ACTION",
      "message": "Widget of type 'text' at body->children[0]->type: text is missing required 'id' field.",
      "file_path": "dirtyPage.pmd",
      "line": 14
    }
  ]
}
```

#### Violations coverage (confirms the P2.3 requirement is satisfied)

- `dirtyPage.pmd` var usage: ScriptVarUsageRule (var count) ✓
- `dirtyPage.pmd` console.log: ScriptConsoleLogRule (console.info) ✓  -- Note: the rule name is "ConsoleLogRule" but it detects all console.* statements. `console.info` in `dirtyPage.pmd`'s script triggers it. ScriptConsoleLogRule is disabled in default config but enabled in test-config.json.
- `dirtyPage.pmd` magic numbers: ScriptMagicNumberRule (42 and 100) ✓
- `dirtyPage.pmd` widget missing id: WidgetIdRequiredRule (text widget in body.children[0]) ✓
- `dirtyPod.pod` hardcoded workday URL: HardcodedWorkdayAPIRule ✓
- `helpers.script` unused function: ScriptDeadCodeRule (unusedHelper) ✓  -- Note: ScriptUnusedFunctionRule is also enabled in test-config.json but ScriptDeadCodeRule fires first for this pattern. Both detect the "unused function" semantic violation.

#### Wiring / Integration

- These expected files are consumed by future `tests/test_runner.py` (P3.3).
- Tests in P3.3 must pass `--config tests/fixtures/test-config.json` (relative to parent dir `../`) when invoking the runner to match these expected outputs.
- The config file path passed to the runner: `str(Path(__file__).parent.parent / "tests" / "fixtures" / "test-config.json")` from within the agents directory.

---

## Verification

### Step 1: Confirm clean_app produces zero findings

Run from the parent Arcane Auditor directory (`cd /Users/name/homelab/ArcaneAuditor`):

```bash
uv run main.py review-app agents/tests/fixtures/clean_app --config agents/tests/fixtures/test-config.json --format json --quiet 2>/dev/null
```

Expected: exit code 0, JSON output contains `"total_findings": 0` and `"findings": []`.

### Step 2: Confirm dirty_app produces exactly 11 findings

Run from the parent Arcane Auditor directory:

```bash
uv run main.py review-app agents/tests/fixtures/dirty_app --config agents/tests/fixtures/test-config.json --format json --quiet 2>/dev/null
```

Expected: exit code 1, JSON output contains `"total_findings": 11`.

Verify each of these rule_ids appears in the findings:
- ScriptDeadCodeRule
- ScriptMagicNumberRule (x2)
- ScriptVarUsageRule (x2)
- ScriptConsoleLogRule
- ScriptStringConcatRule
- EndpointFailOnStatusCodesRule
- EndpointBaseUrlTypeRule
- HardcodedWorkdayAPIRule
- WidgetIdRequiredRule

### Step 3: Run existing scanner tests

Run from the agents directory (`/Users/name/homelab/ArcaneAuditor/agents`):

```bash
uv run pytest tests/test_scanner.py -q
```

Expected: all tests pass. The scanner tests use `tmp_path` fixtures, not the clean/dirty app directories directly, so modifying `minimalPage.pmd` does not break them.

### Step 4: Confirm fixture file counts are correct

Run from the agents directory:

```bash
python -c "
from pathlib import Path
from src.scanner import scan_local
clean = scan_local(Path('tests/fixtures/clean_app'))
dirty = scan_local(Path('tests/fixtures/dirty_app'))
print('clean_app total:', clean.total_count, 'by type:', {k: len(v) for k, v in clean.files_by_type.items() if v})
print('dirty_app total:', dirty.total_count, 'by type:', {k: len(v) for k, v in dirty.files_by_type.items() if v})
"
```

Expected:
- `clean_app total: 3 by type: {'pmd': 1, 'pod': 1, 'script': 1}`
- `dirty_app total: 3 by type: {'pmd': 1, 'pod': 1, 'script': 1}`

## Constraints

- Do NOT modify `tests/fixtures/dirty_app/dirtyPage.pmd` -- it already correctly triggers the required violations.
- Do NOT modify `tests/fixtures/dirty_app/dirtyPod.pod` -- already correct.
- Do NOT modify `tests/fixtures/dirty_app/helpers.script` -- already correct.
- Do NOT modify `tests/fixtures/clean_app/utils.script` -- already correct.
- Do NOT modify `tests/fixtures/clean_app/minimalPod.pod` -- already correct.
- Do NOT modify `tests/fixtures/test-config.json` -- already correct (enables all 42 rules).
- Do NOT write test code -- that is P2.4 (scanner tests) and P3.3 (runner tests).
- Do NOT add new Python dependencies.
- Do NOT modify ARCHITECTURE.md, IMPL_PLAN.md, or CLAUDE.md.
- Do NOT mark P2.3 as complete in IMPL_PLAN.md -- that is the foundry loop's responsibility.
- The `tests/fixtures/expected/` directory must be created as part of the file creation operations (Python's `Path.mkdir(parents=True)` or the Write tool will create parent directories automatically).
