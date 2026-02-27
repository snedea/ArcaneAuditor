# Review Report — P4.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -m py_compile src/reporter.py` clean)
- Tests: PASS (84/84 passed)
- Lint: PASS (`uv run ruff check src/reporter.py` — no warnings)
- Docker: SKIPPED (no Docker files changed in this task)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "src/reporter.py",
      "line": 334,
      "issue": "_build_action_issue_body embeds finding.message in a blockquote with `f\"> {finding.message}\"`. In GitHub Markdown, a blockquote requires `> ` at the start of every line. If finding.message contains a newline, only the first line is quoted; subsequent lines render as unformatted body text outside the blockquote. By contrast, _build_advice_issue_body correctly sanitizes newlines with `.replace(\"\\n\", \" \")` at line 360. The inconsistency means ACTION issue bodies can produce malformed output under conditions that ADVICE bodies handle correctly.",
      "category": "api-contract"
    }
  ],
  "low": [
    {
      "file": "src/reporter.py",
      "line": 361,
      "issue": "_build_advice_issue_body sanitizes `|` and `\\n` in `file_path` and `message` before inserting them into the Markdown table, but `f.rule_id` is inserted raw without any sanitization. If a rule_id ever contains `|`, it would break the table column boundaries. Inconsistent with the sanitization applied to the other two fields.",
      "category": "api-contract"
    },
    {
      "file": "src/reporter.py",
      "line": 338,
      "issue": "_build_action_issue_body (line 338) and _build_advice_issue_body (line 364) both hardcode `https://github.com/snedea/homelab` in the attribution footer. This URL is the homelab monorepo root, not the ArcaneAuditor tool's own path. For any non-snedea deployment the link is misleading. Should either be configurable or point to the specific ArcaneAuditor sub-path.",
      "category": "hardcoded"
    }
  ],
  "validated": [
    "All 6 named functions importable: format_github_issues, _ensure_label, _get_existing_issue_titles, _build_action_issue_title, _build_action_issue_body, _build_advice_issue_body",
    "Function signature at line 191 matches plan: format_github_issues(scan_result: ScanResult, repo: str, token: str) -> list[str]",
    "Github context manager pattern `with Github(auth=Auth.Token(token)) as gh:` used correctly — connection closed on exit",
    "GithubException caught on get_repo and re-raised as ReporterError (line 212)",
    "All three _ensure_label calls present: arcane-auditor/0075ca, arcane-auditor:ACTION/e11d48, arcane-auditor:ADVICE/f59e0b",
    "_ensure_label correctly handles the get→create race condition: 422 on create_label is swallowed (line 279), other statuses raise ReporterError",
    "_get_existing_issue_titles returns set[str] via set comprehension over paginated PyGithub list (line 299)",
    "existing_titles.add(title) after each ACTION issue creation prevents intra-run duplicates (line 239)",
    "GithubException caught and re-raised as ReporterError on both create_issue call sites (lines 236-237, 253-254)",
    "Advice summary title '[Arcane Auditor] ADVICE Summary' is duplicate-checked before creation (line 243)",
    "_build_action_issue_title matches plan spec: f'[Arcane Auditor] {finding.rule_id}: {finding.file_path}' (line 313)",
    "_build_advice_issue_body sanitizes `|` and newlines in file_path and message for Markdown table safety (lines 359-360)",
    "84/84 existing tests pass — no regressions introduced"
  ]
}
```
