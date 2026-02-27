# Review Report — P4.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -m py_compile src/reporter.py` clean; `uv sync` succeeds)
- Tests: PASS (84/84 existing tests pass)
- Lint: PASS (`uv run ruff check src/reporter.py` -- all checks passed)
- Docker: SKIPPED (no compose files changed)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "src/reporter.py",
      "line": 357,
      "issue": "_build_advice_issue_body inserts finding.message verbatim into a markdown table cell with no pipe-character escaping. A message containing '|' splits the cell and adds phantom columns, corrupting the table. Confirmed with test: message 'Remove console.log | warn calls' renders as a 6-column row under a 4-column header. Real messages from ScriptStringConcatRule and ScriptMagicNumberRule contain backticks and single-quotes today; a future rule with '|' will produce a broken GitHub issue table.",
      "category": "logic"
    },
    {
      "file": "src/reporter.py",
      "line": 275,
      "issue": "_ensure_label catches create_label's GithubException and re-raises any status as ReporterError -- including status 422 (Unprocessable Entity / label already exists). In a concurrent scenario where two agent processes both get 404 from get_label and both call create_label, the second process receives 422 and aborts the entire format_github_issues call with ReporterError instead of treating 'already exists' as a no-op success. This is not guarded by status code and will surface to callers.",
      "category": "race"
    }
  ],
  "low": [
    {
      "file": "src/reporter.py",
      "line": 329,
      "issue": "_build_action_issue_body uses `f\"> {finding.message}\"` as a single string. If finding.message contains '\\n', only the first line is inside the blockquote; subsequent lines render as unformatted body text. Confirmed by inspection: the join produces `> First line\\nSecond line` with no `> ` prefix on the continuation line.",
      "category": "logic"
    },
    {
      "file": "src/reporter.py",
      "line": 311,
      "issue": "_build_action_issue_title omits line number: `f\"[Arcane Auditor] {finding.rule_id}: {finding.file_path}\"`. Two ACTION findings for the same (rule_id, file_path) at different lines produce identical titles. The caller-side `existing_titles.add(title)` at line 239 (added beyond the plan spec) means the second occurrence is silently dropped with only a DEBUG log. The caller receives no indication that a finding was not filed. In dirty_app this does not trigger for ACTION findings (all are unique per rule+file), but it is a latent silent-data-loss path.",
      "category": "logic"
    },
    {
      "file": "src/reporter.py",
      "line": 351,
      "issue": "Grammar: `f\"## Arcane Auditor ADVICE Summary ({len(findings)} findings)\"` produces '1 findings' when len == 1. Minor but visible in all single-finding scans.",
      "category": "style"
    }
  ],
  "validated": [
    "PyGithub v2 Auth.Token usage: implementation correctly uses Github(auth=Auth.Token(token)) rather than the deprecated Github(token) from the plan. Import of Auth is present.",
    "Context manager `with Github(...) as gh:` -- connection is closed on both success and exception paths; all API calls are inside the with block.",
    "All GithubException instances from every API call site are caught and re-raised as ReporterError with descriptive messages. No PyGithub exceptions surface to callers.",
    "Label colors passed without '#' prefix as required by PyGithub create_label.",
    "GITHUB_ISSUES dispatcher stub error message updated correctly to the new wording.",
    "existing_titles.add(title) at line 239 correctly prevents duplicate API calls within a single run when the same (rule_id, file_path) appears more than once in action_findings.",
    "format_json, format_summary, format_sarif, _build_sarif_rules, _build_sarif_result -- all unchanged and all 84 prior tests pass.",
    "All 5 new functions (format_github_issues, _ensure_label, _get_existing_issue_titles, _build_action_issue_title, _build_action_issue_body, _build_advice_issue_body) are importable.",
    "pyproject.toml unchanged; pygithub>=2.1.1 was already declared.",
    "Token is not logged or printed anywhere in the new code."
  ]
}
```
