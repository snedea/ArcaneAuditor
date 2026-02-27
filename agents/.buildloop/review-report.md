# Review Report — P2.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (py_compile clean on src/scanner.py, src/config.py, src/models.py; runner.py/reporter.py/fixer.py/cli.py not yet created — expected for P2.3 scope)
- Tests: PASS (19/19 tests pass in tests/test_scanner.py)
- Lint: SKIPPED (ruff/flake8 not invoked; py_compile passes as proxy)
- Docker: SKIPPED (no compose files changed)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "tests/fixtures/dirty_app/dirtyPage.pmd",
      "line": 4,
      "issue": "ScriptConsoleLogRule is disabled in the default Arcane Auditor config. The plan's violation analysis lists 'console.info(msg) -> ScriptConsoleLogRule (ACTION)' as an intended detectable violation, but the smoke test proves the rule is globally disabled ('Skipping disabled rule: ScriptConsoleLogRule'). P3.3 tests that assert ScriptConsoleLogRule fires for dirtyPage.pmd will fail unless they explicitly pass a config that re-enables the rule.",
      "category": "inconsistency"
    },
    {
      "file": ".buildloop/current-plan.md",
      "line": 263,
      "issue": "EndpointFailOnStatusCodesRule severity documented as ADVICE in the plan ('Missing failOnStatusCodes field -> EndpointFailOnStatusCodesRule (ADVICE)') but actual smoke test output shows 'severity': 'ACTION'. P3.3 tests that assert ADVICE severity for this rule on dirtyPod.pod will fail.",
      "category": "api-contract"
    },
    {
      "file": ".buildloop/current-plan.md",
      "line": 258,
      "issue": "EndpointBaseUrlTypeRule fires as an unplanned ADVICE violation for dirtyPod.pod ('Pod endpoint getHrData is pointing to a Workday API, but not leveraging a baseUrlType'). The plan's intended violation list for dirtyPod.pod does not mention this rule. P3.3 tests that assert an exact violation list or count for dirty_app will fail: actual has 9 findings (3 ACTION + 6 ADVICE), but plan only documents 8 (2+2 for dirtyPod, 5+1 for dirtyPage).",
      "category": "inconsistency"
    }
  ],
  "low": [
    {
      "file": ".buildloop/current-plan.md",
      "line": 307,
      "issue": "Smoke verification command does not pass --config to the parent tool, so it runs with the default config. The test-config.json in tests/fixtures/ has all rules enabled, including ScriptConsoleLogRule, ScriptUnusedFunctionRule, ScriptDeadCodeRule, and ScriptUnusedVariableRule. If P3.3 runner tests pass test-config.json, additional violations will fire that were not observed or accounted for in this task's verification. The smoke test and the eventual test suite are verifying different rule sets.",
      "category": "inconsistency"
    },
    {
      "file": ".buildloop/current-plan.md",
      "line": 16,
      "issue": "Plan explains ScriptUnusedFunctionRule does not fire because '_check() returns yield from []'. Actual reason observed in smoke test is 'Skipping disabled rule: ScriptUnusedFunctionRule' — the rule is globally disabled, not merely limited by its implementation. The distinction matters: if the rule is later enabled, _check() may or may not actually scan .script files. The plan's explanation gives false confidence about a code-level guarantee that has not been verified.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "clean_app smoke test exits 0 with zero findings — 36 rules loaded, zero violations across minimalPage.pmd, minimalPod.pod, utils.script",
    "dirty_app smoke test exits 1 with 9 findings (3 ACTION + 6 ADVICE) — correct for a dirty fixture",
    "minimalPage.pmd footer uses type='pod' child — FooterPodRequiredRule does not fire",
    "minimalPage.pmd script uses const/let only — ScriptVarUsageRule does not fire",
    "minimalPage.pmd all widgets with non-exempt types have ids (text='greetingText', section='bodySection') — WidgetIdRequiredRule does not fire",
    "minimalPod.pod endpoint URL uses template expression ${baseEndpoint}, no *.workday.com — HardcodedWorkdayAPIRule does not fire",
    "minimalPod.pod has failOnStatusCodes on endpoint — EndpointFailOnStatusCodesRule does not fire",
    "dirtyPage.pmd: ScriptVarUsageRule fires (var count), ScriptMagicNumberRule fires twice (42 and 100), ScriptStringConcatRule fires, WidgetIdRequiredRule fires (type=text missing id) — all confirmed in smoke output",
    "dirtyPod.pod: HardcodedWorkdayAPIRule fires (ACTION) for api.workday.com URL, EndpointFailOnStatusCodesRule fires (ACTION) for missing failOnStatusCodes — confirmed in smoke output",
    "helpers.script: ScriptVarUsageRule fires for 'var unusedHelper' — confirmed in smoke output",
    "All 6 fixture files exist on disk: clean_app/minimalPage.pmd, clean_app/minimalPod.pod, clean_app/utils.script, dirty_app/dirtyPage.pmd, dirty_app/dirtyPod.pod, dirty_app/helpers.script",
    "19/19 tests in tests/test_scanner.py pass",
    "No files outside the 6 fixtures and .buildloop/ were modified"
  ]
}
```

## Evidence for Medium Findings

### M1: ScriptConsoleLogRule disabled
Smoke test output (dirty_app run):
```
Skipping disabled rule: ScriptConsoleLogRule
```
Plan claims (current-plan.md, violation analysis for dirtyPage.pmd):
```
`console.info(msg)` → ScriptConsoleLogRule (ACTION): console.info is in the detected set {info, warn, error, debug}
```
The rule IS listed as `enabled: true` in test-config.json, so it would fire if `--config` were passed. But the smoke test does not pass `--config`, so the verified behavior contradicts the plan's claim.

### M2: EndpointFailOnStatusCodesRule severity is ACTION, not ADVICE
Plan (current-plan.md ~line 263):
```
Missing `failOnStatusCodes` field → EndpointFailOnStatusCodesRule (ADVICE)
```
Actual smoke test JSON output:
```json
{"rule_id": "EndpointFailOnStatusCodesRule", "severity": "ACTION", ...}
```

### M3: EndpointBaseUrlTypeRule fires unplanned
Plan's violation list for dirtyPod.pod lists exactly 2 violations: HardcodedWorkdayAPIRule and EndpointFailOnStatusCodesRule. Actual output has a third:
```json
{"rule_id": "EndpointBaseUrlTypeRule", "severity": "ADVICE", "message": "Pod endpoint 'getHrData' is pointing to a Workday API, but not leveraging a baseUrlType..."}
```
The total finding count (9) also differs from what can be inferred from the plan's violation lists.
