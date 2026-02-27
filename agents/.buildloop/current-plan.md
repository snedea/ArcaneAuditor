# Plan: P2.3

Date: 2026-02-27
Version: v2
Status: in-progress

## Context

Task P2.3 creates test fixtures for the agent test suite. The previous builder made multiple WIP commits that created partial fixtures. This plan completes the work.

**Current state after prior builder runs:**
- `tests/fixtures/clean_app/minimalPage.pmd` EXISTS but is missing required `script` field
- `tests/fixtures/clean_app/minimalPod.pod` EXISTS and is complete
- `tests/fixtures/clean_app/utils.script` EXISTS and is complete
- `tests/fixtures/dirty_app/dirtyPage.pmd` EXISTS with var, console.info, magic numbers, missing id
- `tests/fixtures/dirty_app/dirtyPod.pod` EXISTS with hardcoded workday URL
- `tests/fixtures/dirty_app/helpers.script` EXISTS with var + unexported function
- `tests/fixtures/expected/clean_app.json` EXISTS (format: `{exit_code, findings:[]}`)
- `tests/fixtures/expected/dirty_app.json` EXISTS with 11 findings listed
- `tests/fixtures/test-config.json` EXISTS with all rules enabled

**Gap**: `clean_app/minimalPage.pmd` is missing the `script` field. The IMPL_PLAN.md task description explicitly requires "a minimal valid .pmd file (valid pageId, **script with const/let**, proper naming)".

**Critical**: The expected JSON files were written by the prior builder without running the tool. They must be verified against actual parent tool output and updated if wrong.

## Dependencies

- list: []
- commands: []
  (No new packages needed. Parent tool is invoked as subprocess.)

## File Operations (in execution order)

### 1. MODIFY tests/fixtures/clean_app/minimalPage.pmd
- operation: MODIFY
- reason: Add `script` field with const/let to satisfy task requirement "script with const/let". Currently the file has id, securityDomains, presentation but no script field.
- anchor: `"securityDomains": ["Everyone"],`

#### Content change

The file currently reads:
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

Replace with this exact content:
```json
{
  "id": "minimalPage",
  "securityDomains": ["Everyone"],
  "script": "<% const greeting = 'Hello'; %>",
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
          "value": "<% greeting %>"
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

**Design rationale (no judgment calls needed):**
- `script` field placed between `securityDomains` and `presentation` to satisfy `PMDSectionOrderingRule` (config order: id, securityDomains, include, script, endPoints, onSubmit, outboundData, onLoad, presentation)
- `const greeting = 'Hello'` uses const (not var), satisfying `ScriptVarUsageRule`
- `'Hello'` is a string literal with no magic numbers, satisfying `ScriptMagicNumberRule`
- No console.* calls, satisfying `ScriptConsoleLogRule`
- No string concatenation (`+`), satisfying `ScriptStringConcatRule`
- `greeting` is referenced in `"value": "<% greeting %>"` in the presentation body -- this prevents `ScriptUnusedVariableRule` from firing (the parser scans full source_content for variable references)
- `id: "minimalPage"` is a valid lowerCamelCase page ID
- All widgets have `id` fields (bodySection, greetingText, footerPod), satisfying `WidgetIdRequiredRule`

**If `ScriptUnusedVariableRule` still fires after this change:**
- Fallback: change the script to `"<% const getGreeting = function() { return 'Hello'; }; const greeting = getGreeting(); %>"` and keep `"value": "<% greeting %>"`
- This ensures `getGreeting` is used (called), and `greeting` is referenced in presentation

### 2. VERIFY AND UPDATE tests/fixtures/expected/clean_app.json
- operation: MODIFY (or no-op if already correct)
- reason: The existing expected/clean_app.json was written by the prior builder without running the tool. Must verify against actual parent tool output.
- anchor: `"exit_code": 0,`

**Steps to verify:**
1. Run the parent tool against the (now updated) clean_app fixture:
   ```bash
   cd /Users/name/homelab/ArcaneAuditor
   uv run main.py review-app agents/tests/fixtures/clean_app \
     --format json \
     --config agents/tests/fixtures/test-config.json \
     --output /tmp/arcane_clean_actual.json \
     --quiet
   echo "Exit code: $?"
   ```
2. Read `/tmp/arcane_clean_actual.json` to see actual parent tool JSON output
3. The actual output has this schema:
   ```json
   {
     "summary": {"total_files": N, "total_rules": N, "total_findings": N, "findings_by_severity": {...}},
     "findings": [{"rule_id": "...", "severity": "...", "message": "...", "file_path": "...", "line": N}]
   }
   ```
4. Check `summary.total_findings`. If it is 0, the clean_app fixture is correct.
5. If `total_findings > 0`, debug each finding and adjust the clean_app fixture files to eliminate the violation. Then re-run.
6. Once confirmed `total_findings == 0`, the existing `expected/clean_app.json` content is already correct as-is:
   ```json
   {
     "exit_code": 0,
     "findings": []
   }
   ```
   No update needed.

**If findings appear in clean_app scan, common causes and fixes:**
- `ScriptUnusedVariableRule` fires on `greeting`: change script to `"<% const greeting = 'Hello'; const msg = greeting; %>"` -- then `greeting` is used in the same block, and `msg` is referenced in presentation `"value": "<% msg %>"`
- `ScriptMagicNumberRule` fires: no numbers in `'Hello'` so this should not happen
- `PMDSectionOrderingRule` fires: verify `script` key appears between `securityDomains` and `presentation` in the JSON

### 3. VERIFY AND UPDATE tests/fixtures/expected/dirty_app.json
- operation: MODIFY (or no-op if already correct)
- reason: The existing expected/dirty_app.json was written by the prior builder without running the tool. Line numbers and message text must match actual parent tool output exactly.
- anchor: `"rule_id": "ScriptMagicNumberRule",`

**Steps to verify:**
1. Run the parent tool against the dirty_app fixture:
   ```bash
   cd /Users/name/homelab/ArcaneAuditor
   uv run main.py review-app agents/tests/fixtures/dirty_app \
     --format json \
     --config agents/tests/fixtures/test-config.json \
     --output /tmp/arcane_dirty_actual.json \
     --quiet
   echo "Exit code: $?"
   ```
2. Read `/tmp/arcane_dirty_actual.json`
3. Extract the `findings` array from the actual output
4. The exit code should be 1 (ACTION issues found: `ScriptConsoleLogRule`, `EndpointFailOnStatusCodesRule`, `HardcodedWorkdayAPIRule`, `WidgetIdRequiredRule` are all ACTION severity)
5. Compare actual findings against `expected/dirty_app.json`

**What to check in the comparison:**
- `rule_id` values: must match exactly (case-sensitive)
- `severity` values: must match exactly ("ACTION" or "ADVICE")
- `file_path` values: the parent tool uses relative paths from the app root. Confirm whether it emits `"dirtyPage.pmd"` or `"dirty_app/dirtyPage.pmd"` or the full absolute path
- `line` values: these are the most likely to differ from the estimated values in the prior builder's expected file
- `message` text: must match exactly including punctuation and spacing

6. Overwrite `expected/dirty_app.json` with a file built from the actual findings:
   ```json
   {
     "exit_code": 1,
     "findings": [
       <-- paste each finding from /tmp/arcane_dirty_actual.json findings array here -->
     ]
   }
   ```
   Important: use the `exit_code` from the actual tool run (should be 1), not from the summary.

**Expected violations (must all appear; if any are missing, the dirty fixture is wrong):**
- `ScriptVarUsageRule` ADVICE: var declaration in `dirtyPage.pmd` (the `var count` in script block, line 4)
- `ScriptVarUsageRule` ADVICE: var declaration in `helpers.script` (the `var unusedHelper`, line 5)
- `ScriptConsoleLogRule` ACTION: console.info in `dirtyPage.pmd` script block (line 4)
- `ScriptMagicNumberRule` ADVICE: magic number 42 in `dirtyPage.pmd` (line 4)
- `ScriptMagicNumberRule` ADVICE: magic number 100 in `dirtyPage.pmd` (line 4)
- `ScriptStringConcatRule` ADVICE: string concat `'Count: ' + count` in `dirtyPage.pmd` (line 4)
- `ScriptDeadCodeRule` ADVICE: `unusedHelper` declared but not exported in `helpers.script` (line 5)
- `HardcodedWorkdayAPIRule` ACTION: hardcoded workday.com URL in `dirtyPod.pod`
- `EndpointFailOnStatusCodesRule` ACTION: missing failOnStatusCodes in `dirtyPod.pod`
- `EndpointBaseUrlTypeRule` ADVICE: workday URL without baseUrlType in `dirtyPod.pod`
- `WidgetIdRequiredRule` ACTION: text widget at body->children[0] missing id in `dirtyPage.pmd`

**Minimum required violations: at least 1 ACTION finding** (to confirm exit_code is 1, not 0).

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no linter configured for fixture files; they are JSON/script content, not Python)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -v`
  (Note: test_scanner.py tests scan_local on these fixtures; they should all pass. P3.3 test_runner.py does not exist yet.)
- smoke-clean:
  ```bash
  cd /Users/name/homelab/ArcaneAuditor
  uv run main.py review-app agents/tests/fixtures/clean_app \
    --format json \
    --config agents/tests/fixtures/test-config.json \
    --quiet
  # Expect: exit code 0, output contains "total_findings": 0
  ```
- smoke-dirty:
  ```bash
  cd /Users/name/homelab/ArcaneAuditor
  uv run main.py review-app agents/tests/fixtures/dirty_app \
    --format json \
    --config agents/tests/fixtures/test-config.json \
    --quiet
  # Expect: exit code 1, output contains findings for ScriptConsoleLogRule, HardcodedWorkdayAPIRule, EndpointFailOnStatusCodesRule, WidgetIdRequiredRule
  ```

## Constraints

- Do NOT modify `tests/fixtures/dirty_app/dirtyPage.pmd`, `tests/fixtures/dirty_app/dirtyPod.pod`, or `tests/fixtures/dirty_app/helpers.script` -- they are correct and complete.
- Do NOT modify `tests/fixtures/clean_app/minimalPod.pod` or `tests/fixtures/clean_app/utils.script` -- they are correct and complete.
- Do NOT modify `tests/fixtures/test-config.json`.
- Do NOT change the format of `expected/clean_app.json` and `expected/dirty_app.json` -- they use `{exit_code, findings:[]}` schema intentionally.
- Do NOT modify any `.py` source files in `src/` or `tests/`.
- Do NOT add new fixture files beyond what already exists.
- The only Python test that may fail before this task: none. `test_scanner.py` tests do not depend on fixture file content, only on file existence.
- Always use the `test-config.json` config file when running the parent tool against fixtures, to ensure consistent rule enablement.
