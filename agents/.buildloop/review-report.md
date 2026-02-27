# Review Report — P2.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (py_compile on src/*.py: 0 errors)
- Tests: PASS (19/19 in tests/test_scanner.py)
- Lint: SKIPPED (neither ruff nor flake8 installed in agents venv)
- Docker: N/A (no compose files changed)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "tests/fixtures/dirty_app/dirtyPage.pmd",
      "line": 4,
      "issue": "ScriptConsoleLogRule is DISABLED in the default config. The console.info(msg) addition produces zero findings when the scan runs without --config. The plan's verification step explicitly says 'Expected: exit code 1, JSON with findings including ScriptConsoleLogRule' -- this is false. The rule is skipped with 'Skipping disabled rule: ScriptConsoleLogRule' in both clean and dirty app scans. P3.3 tests that assert on this violation will fail unless they pass --config pointing to test-config.json (which is itself untracked and unwired).",
      "category": "logic"
    },
    {
      "file": "tests/fixtures/dirty_app/dirtyPage.pmd",
      "line": 4,
      "issue": "Plan's violation inventory for dirtyPage.pmd is wrong. ScriptStringConcatRule fires on 'Count: ' + count (ADVICE) but is not listed in the plan. Actual dirty_app findings: ScriptVarUsageRule, ScriptStringConcatRule, ScriptMagicNumberRule x2, WidgetIdRequiredRule = 5 violations. Plan documents 4 (omitting ScriptStringConcatRule, including ScriptConsoleLogRule which does not fire).",
      "category": "inconsistency"
    },
    {
      "file": "tests/fixtures/dirty_app/dirtyPod.pod",
      "line": 7,
      "issue": "Plan's violation inventory for dirtyPod.pod documents 2 violations (EndpointBaseUrlTypeRule, EndpointFailOnStatusCodesRule). The actual scan fires 3: HardcodedWorkdayAPIRule (ACTION) also fires on the workday.com URL. The plan's violation count is wrong; any P3.3 test that asserts exactly 2 findings for dirtyPod.pod will fail.",
      "category": "inconsistency"
    }
  ],
  "low": [
    {
      "file": "tests/fixtures/dirty_app/helpers.script",
      "line": 5,
      "issue": "Plan claims ScriptUnusedFunctionRule fires on unusedHelper (2 violations from helpers.script). The rule is disabled by default. Only ScriptVarUsageRule fires. Plan's violation inventory for this file overstates by one.",
      "category": "inconsistency"
    },
    {
      "file": "tests/fixtures/test-config.json",
      "line": 1,
      "issue": "Untracked file added outside the stated scope of this plan iteration. The plan says 'The ONLY code change is the console.info(msg) addition to dirty_app/dirtyPage.pmd line 4.' This file is not referenced by any scan command, test, or runner invocation -- it exists but has no current integration.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "dirtyPage.pmd: console.info(msg) correctly added at line 4; file is valid JSON",
    "All 6 fixture files exist on disk (3 clean_app, 3 dirty_app)",
    "clean_app scan: exit 0, 0 findings -- correct",
    "dirty_app scan: exit 1 (3 ACTION findings) -- exit code is correct",
    "ScriptVarUsageRule fires on dirtyPage.pmd (var count) and helpers.script (var unusedHelper)",
    "ScriptMagicNumberRule fires on 42 and 100 in dirtyPage.pmd; 0 is correctly exempt",
    "WidgetIdRequiredRule fires on the text widget missing id in dirtyPage.pmd body.children[0]",
    "EndpointFailOnStatusCodesRule and EndpointBaseUrlTypeRule both fire on dirtyPod.pod",
    "clean_app/minimalPage.pmd: const/let only, all widgets have ids, zero violations",
    "clean_app/minimalPod.pod: template URL (no workday.com), failOnStatusCodes present, zero violations",
    "clean_app/utils.script: const only, both functions exported, zero violations",
    "19/19 pytest scanner tests pass after the fixture change"
  ]
}
```

## Evidence for key findings

**ScriptConsoleLogRule disabled by default** (confirmed by actual scan output):
```
Skipping disabled rule: ScriptConsoleLogRule   # appears in BOTH clean and dirty app scans
```
Plan verification claim: "Expected: exit code 1, JSON with findings including ScriptConsoleLogRule" -- NOT MET.

**ScriptStringConcatRule fires (unplanned)** (from actual dirty_app scan JSON):
```json
{
  "rule_id": "ScriptStringConcatRule",
  "severity": "ADVICE",
  "message": "...uses string concatenation with + operator: ''Count: ' + count'...",
  "file_path": "dirtyPage.pmd",
  "line": 4
}
```

**HardcodedWorkdayAPIRule fires (unplanned)** (from actual dirty_app scan JSON):
```json
{
  "rule_id": "HardcodedWorkdayAPIRule",
  "severity": "ACTION",
  "message": "Pod endpoint 'getHrData' uses hardcoded *.workday.com URL...",
  "file_path": "dirtyPod.pod",
  "line": 7
}
```

**ScriptUnusedFunctionRule disabled by default**:
```
Skipping disabled rule: ScriptUnusedFunctionRule   # appears in BOTH scans
```
