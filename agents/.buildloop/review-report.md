# Review Report — P2.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (no compiled artifacts; data files only)
- Tests: PASS (19/19 scanner tests pass: `uv run pytest tests/test_scanner.py -v`)
- Lint: SKIPPED (no lint step for JSON/script data files per plan)
- Docker: SKIPPED (no Docker components in this task)
- Smoke 1 (scanner clean_app): PASS (`total_count=3`, one file per type)
- Smoke 2 (scanner dirty_app): PASS (`total_count=3`, one file per type)
- Smoke 3 (clean_app exit code): PASS (exit code 0; 0 ACTION findings, 1 ADVICE)
- Smoke 4 (dirty_app exit code): PASS (exit code 1; 3 ACTION findings present)

## Findings

```json
{
  "high": [
    {
      "file": "tests/fixtures/dirty_app/dirtyPage.pmd",
      "line": 4,
      "issue": "ScriptConsoleLogRule violation is absent and can never fire. The plan's smoke test 4 explicitly requires 'The JSON output must contain findings for ScriptConsoleLogRule'. Two compounding problems: (1) the builder replaced 'console.log(count)' from the plan with 'const msg = \\'Count: \\' + count;', removing the console.log call; (2) ScriptConsoleLogRule is permanently disabled in config/presets/development.json line 38 ('enabled': false). Future runner/integration tests built against this fixture (P3.x tasks) will assert ScriptConsoleLogRule appears in dirty_app output and will always fail.",
      "category": "logic"
    }
  ],
  "medium": [
    {
      "file": "tests/fixtures/dirty_app/dirtyPage.pmd",
      "line": 4,
      "issue": "Undocumented ScriptStringConcatRule ADVICE violation. The builder introduced 'const msg = \\'Count: \\' + count;' when replacing console.log. This triggers ScriptStringConcatRule (confirmed in actual output). The plan states this file has exactly four violations: ScriptVarUsageRule, ScriptConsoleLogRule, ScriptMagicNumberRule, WidgetIdRequiredRule. Actual violations are: ScriptVarUsageRule, ScriptMagicNumberRule (x2), ScriptStringConcatRule, WidgetIdRequiredRule. Tests that enumerate expected violations per file will fail due to ScriptStringConcatRule being present and ScriptConsoleLogRule being absent.",
      "category": "inconsistency"
    },
    {
      "file": "tests/fixtures/dirty_app/dirtyPod.pod",
      "line": 1,
      "issue": "Undocumented EndpointFailOnStatusCodesRule ACTION violation. The plan states dirtyPod.pod has 'exactly one known violation: HardcodedWorkdayAPIRule'. Actual findings: HardcodedWorkdayAPIRule (ACTION) + EndpointFailOnStatusCodesRule (ACTION) + EndpointBaseUrlTypeRule (ADVICE) = 3 violations, 2 of which are ACTION. The missing 'failOnStatusCodes' field triggers EndpointFailOnStatusCodesRule because EndpointFailOnStatusCodesRule is enabled (config/presets/development.json line 124) and requires all POD endpoints to have that field. Tests written against the plan's 'exactly one violation' design will fail.",
      "category": "inconsistency"
    },
    {
      "file": "tests/fixtures/dirty_app/helpers.script",
      "line": 5,
      "issue": "ScriptDeadCodeRule is permanently disabled; the file's actual violation is ScriptVarUsageRule from 'var unusedHelper', not the planned ScriptDeadCodeRule. The plan says 'exactly one known violation: ScriptDeadCodeRule'. Both ScriptDeadCodeRule and ScriptUnusedFunctionRule are disabled in config/presets/development.json (lines 47 and 104). The builder adapted by changing 'const unusedHelper' (as specified in the plan) to 'var unusedHelper' to trigger ScriptVarUsageRule instead. The violation class, severity, and message are all different from what the plan documents. Tests written against the plan's intended violation will assert the wrong rule.",
      "category": "inconsistency"
    }
  ],
  "low": [
    {
      "file": "tests/fixtures/clean_app/minimalPod.pod",
      "line": 8,
      "issue": "URL template deviates from plan, producing an unexpected EndpointBaseUrlTypeRule ADVICE finding on the clean_app. Plan specifies: '\"url\": \"<% apiGatewayEndpoint + \\'/workers/me\\' %>\"'. Actual: '\"url\": \"<% `{apiGatewayEndpoint}/workers/me` %>\"'. The backtick template literal syntax causes EndpointBaseUrlTypeRule to flag the endpoint as pointing to a Workday API without a baseUrlType. Exit code is still 0 (ADVICE only), so smoke test 3 passes, but the clean_app is not truly violation-free as the plan intends."
    },
    {
      "file": "tests/fixtures/clean_app/minimalPod.pod",
      "line": 9,
      "issue": "'failOnStatusCodes: [{\"code\": 400}, {\"code\": 403}]' was added to the endpoint — not present in the plan. This was likely added to prevent EndpointFailOnStatusCodesRule from firing on the clean_app (which it does correctly). The addition is functional but undocumented: it creates an asymmetry where clean_app's endpoint structure differs from dirty_app's not just by URL but by a structural field. This complicates future fixture documentation."
    }
  ],
  "validated": [
    "All 6 fixture files exist at the correct paths under tests/fixtures/clean_app/ and tests/fixtures/dirty_app/",
    "Scanner correctly finds total_count=3 with one pmd, one pod, one script per directory",
    "All 19 tests in tests/test_scanner.py pass without modification",
    "clean_app exits with code 0: 0 ACTION findings, 1 ADVICE (EndpointBaseUrlTypeRule on minimalPod.pod)",
    "dirty_app exits with code 1: 3 ACTION findings (WidgetIdRequiredRule, HardcodedWorkdayAPIRule, EndpointFailOnStatusCodesRule)",
    "dirtyPage.pmd correctly triggers ScriptVarUsageRule, ScriptMagicNumberRule (42 and 100), and WidgetIdRequiredRule",
    "dirtyPod.pod correctly triggers HardcodedWorkdayAPIRule for 'https://api.workday.com/common/v1/workers'",
    "PMD key ordering in both minimalPage.pmd and dirtyPage.pmd follows PMDSectionOrderingRule required order (id -> securityDomains -> script -> presentation), which avoids a violation the plan's original ordering would have caused",
    "No .py files were created; no existing source files were modified; no tests/fixtures/__init__.py was created",
    "File encoding is UTF-8; .script files are not wrapped in <% %>"
  ]
}
```

## Supporting Evidence

**ScriptConsoleLogRule disabled (config/presets/development.json:37-41):**
```json
"ScriptConsoleLogRule": {
  "enabled": false,
  ...
}
```
Confirmed by runtime output: `Skipping disabled rule: ScriptConsoleLogRule`

**ScriptDeadCodeRule and ScriptUnusedFunctionRule disabled (config/presets/development.json:47-51, 104-108):**
```json
"ScriptDeadCodeRule": { "enabled": false },
"ScriptUnusedFunctionRule": { "enabled": false }
```
Confirmed by runtime output: `Skipping disabled rule: ScriptDeadCodeRule` and `Skipping disabled rule: ScriptUnusedFunctionRule`

**Actual dirty_app findings (from live run):**
- `ScriptMagicNumberRule` ADVICE — dirtyPage.pmd:4 (42)
- `ScriptMagicNumberRule` ADVICE — dirtyPage.pmd:4 (100)
- `ScriptStringConcatRule` ADVICE — dirtyPage.pmd:4 (`'Count: ' + count`)
- `ScriptVarUsageRule` ADVICE — dirtyPage.pmd:4 (`var count`)
- `ScriptVarUsageRule` ADVICE — helpers.script:5 (`var unusedHelper`)
- `EndpointFailOnStatusCodesRule` ACTION — dirtyPod.pod:1 (missing field)
- `EndpointBaseUrlTypeRule` ADVICE — dirtyPod.pod:1
- `HardcodedWorkdayAPIRule` ACTION — dirtyPod.pod:7
- `WidgetIdRequiredRule` ACTION — dirtyPage.pmd:14

**Missing from plan's required findings:** `ScriptConsoleLogRule` (rule disabled; console.log call also absent from file)
