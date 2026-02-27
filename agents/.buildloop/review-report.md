# Review Report — P2.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (ruff: all checks passed)
- Tests: PASS (56/56 pytest)
- Lint: PASS (ruff clean on src/ and tests/)
- Docker: SKIPPED (no compose files changed in this task)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "tests/fixtures/clean_app/minimalPage.pmd",
      "line": 4,
      "issue": "Script declares 'const greeting' and 'let count' but neither variable is referenced anywhere in the script or presentation. When ScriptUnusedVariableRule is enabled (as in test-config.json which has all 42 rules on), this produces 2 ADVICE findings against the supposedly clean fixture. CLAUDE.md defines clean_app as 'minimal Extend app with zero violations' and mandates that every test 'verifies findings match expected output exactly'. Any runner test that uses test-config.json and checks for zero findings on clean_app will fail. Confirmed: running `uv run main.py review-app agents/tests/fixtures/clean_app --format json --quiet --config agents/tests/fixtures/test-config.json` exits 0 but returns total_findings: 2 (ScriptUnusedVariableRule for 'greeting' and 'count').",
      "category": "logic"
    }
  ],
  "low": [
    {
      "file": ".buildloop/current-plan.md",
      "line": 256,
      "issue": "The plan's smoke-dirty verification command does not pass --config. Without it, the parent tool loads config/presets/development.json (the CWD-relative default), which disables ScriptConsoleLogRule and ScriptDeadCodeRule. The plan claims the command produces findings for both rules, but it does not: actual output shows 'Skipping disabled rule: ScriptConsoleLogRule' and 'Skipping disabled rule: ScriptDeadCodeRule'. The correct command is: `uv run main.py review-app agents/tests/fixtures/dirty_app --format json --quiet --config agents/tests/fixtures/test-config.json`. With test-config.json, all 6 expected violations do fire correctly. The fixture content is correct; the verification command in the plan is wrong.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "All 6 fixture files match exact byte-for-byte expected content from the plan",
    "56/56 pytest tests pass (test_scanner, test_models, test_config)",
    "Ruff lint: all checks passed on src/ and tests/",
    "clean_app exits 0, total_findings: 0 in default config mode (development.json preset)",
    "dirty_app exits 1 in default config mode -- ScriptVarUsageRule (x2), ScriptMagicNumberRule (x2), ScriptStringConcatRule, EndpointFailOnStatusCodesRule, EndpointBaseUrlTypeRule, HardcodedWorkdayAPIRule, WidgetIdRequiredRule all fire correctly",
    "With test-config.json: all 6 plan-specified dirty violations confirmed -- ScriptConsoleLogRule fires for console.info in dirtyPage.pmd:4, ScriptDeadCodeRule fires for unusedHelper in helpers.script:5",
    "console.info (not console.log) in dirtyPage.pmd correctly triggers ScriptConsoleLogRule (ConsoleLogDetector checks info/warn/error/debug, not log)",
    "helpers.script unusedHelper is top-level and not exported -- correctly detected by ScriptDeadCodeRule when enabled",
    "minimalPod.pod template URL ${baseEndpoint} correctly passes HardcodedWorkdayAPIRule",
    "minimalPod.pod failOnStatusCodes present -- correctly passes EndpointFailOnStatusCodesRule",
    "dirtyPage.pmd text widget missing 'id' field -- correctly triggers WidgetIdRequiredRule at line 14",
    "test-config.json exists at tests/fixtures/test-config.json with all 42 rules enabled"
  ]
}
```

## Evidence for MEDIUM finding

`minimalPage.pmd:4` script: `<% const greeting = 'Hello'; let count = 0; %>`

- `greeting` is assigned `'Hello'` but the presentation uses the literal string `"Hello"` directly (`"value": "Hello"`). `greeting` is never read.
- `count` is initialized to `0` and never incremented, compared, or referenced.

Running with full rule set confirms:
```
"rule_id": "ScriptUnusedVariableRule", "message": "Unused variable 'greeting' in script", "file_path": "minimalPage.pmd", "line": 4
"rule_id": "ScriptUnusedVariableRule", "message": "Unused variable 'count' in script",   "file_path": "minimalPage.pmd", "line": 4
```

Exit is still 0 (ADVICE-only), but `total_findings: 2` breaks any test asserting zero findings.

**Fix**: Remove unused variables from the script, or reference them so they are actually used (e.g., bind `greeting` to the text widget value via a template expression).
