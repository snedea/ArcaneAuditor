# Review Report — P2.3

## Verdict: FAIL

## Runtime Checks
- Build: SKIPPED (no Python source files changed; fixture files are JSON/script)
- Tests: PASS (19/19 scanner tests pass; `uv run pytest tests/test_scanner.py -q`)
- Lint: SKIPPED (no Python source files changed)
- Docker: SKIPPED (no compose files changed)
- **clean_app scan**: PASS — exit code 0, `total_findings: 0` confirmed by running the tool
- **dirty_app scan**: PASS — exit code 1, `total_findings: 11` confirmed by running the tool

## Findings

```json
{
  "high": [
    {
      "file": "tests/fixtures/expected/dirty_app.json",
      "line": 4,
      "issue": "Findings order does not match actual tool output. The file records findings in this order: ScriptMagicNumberRule(42), ScriptMagicNumberRule(100), ScriptDeadCodeRule, ScriptVarUsageRule(count), ScriptVarUsageRule(unusedHelper), ScriptConsoleLogRule, ScriptStringConcatRule, then endpoint/widget rules. The tool actually outputs them as: ScriptStringConcatRule, ScriptVarUsageRule(count), ScriptVarUsageRule(unusedHelper), ScriptMagicNumberRule(42), ScriptMagicNumberRule(100), ScriptDeadCodeRule, ScriptConsoleLogRule, then endpoint/widget rules. Seven of eleven findings are in the wrong position. The plan (line 104) states 'findings are ordered by the tool's output order' but the file was written manually with a different order. P3.3 tests that do exact comparison against this file will fail on the first run.",
      "category": "logic"
    }
  ],
  "medium": [],
  "low": [
    {
      "file": "tests/fixtures/__pycache__/test-config.cpython-312.pyc",
      "line": 0,
      "issue": "Stray bytecode cache file exists in the fixtures directory. Python compiled something named 'test-config' to bytecode, which is unexpected for a JSON file. The ArcaneAuditor/.gitignore line 5 covers __pycache__/ so it will not be committed, but the artifact's presence is unexplained and suggests Python may have found a conftest or py file in the fixtures directory at some point.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "clean_app/minimalPage.pmd matches the plan's exact JSON spec (no script field, all widget ids present)",
    "clean_app scan: exit code 0, zero findings across all 42 enabled rules -- ScriptUnusedVariableRule no longer triggers",
    "dirty_app scan: exit code 1, exactly 11 findings -- all 6 required violation categories covered",
    "All 11 dirty_app finding messages and file_path/line values in dirty_app.json are correct (only order is wrong)",
    "clean_app.json content is correct: {exit_code: 0, findings: []}",
    "Both expected/ files omit volatile summary/context fields as required by the plan",
    "tests/fixtures/expected/ directory was created and contains both required files",
    "clean_app fixture: 3 files (pmd: 1, pod: 1, script: 1)",
    "dirty_app fixture: 3 files (pmd: 1, pod: 1, script: 1)",
    "test-config.json enables all 42 rules including ScriptConsoleLogRule",
    "19 existing scanner tests pass without regression",
    "ArcaneAuditor/.gitignore line 5 covers __pycache__/ -- bytecode file will not be committed"
  ]
}
```
