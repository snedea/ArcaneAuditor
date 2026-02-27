# Plan: P4.3

## Status: ALREADY COMPLETE

The implementation of `format_github_issues` is fully present in `src/reporter.py` as of the prior WIP commit (`4be1a9c`). No new code needs to be written.

This plan contains verification-only steps. The builder MUST NOT rewrite or overwrite existing code.

---

## Dependencies
- list: [] (PyGithub is already in pyproject.toml as `pygithub>=2.1.1`)
- commands: [] (nothing to install; `uv sync` was run previously)

---

## File Operations (in execution order)

### 1. VERIFY src/reporter.py
- operation: VERIFY (read-only)
- reason: Confirm the existing WIP implementation is complete and correct against all P4.3 requirements

**Checklist — verify each item is present:**

1. Function signature `format_github_issues(scan_result: ScanResult, repo: str, token: str) -> list[str]` exists at line 191.
2. `Github(auth=Auth.Token(token))` context manager wraps all API calls.
3. `gh.get_repo(repo)` is called; `GithubException` is caught and re-raised as `ReporterError`.
4. `_ensure_label(repo_obj, "arcane-auditor", "0075ca")` is called.
5. `_ensure_label(repo_obj, "arcane-auditor:ACTION", "e11d48")` is called.
6. `_ensure_label(repo_obj, "arcane-auditor:ADVICE", "f59e0b")` is called.
7. `_get_existing_issue_titles(repo_obj)` returns a `set[str]` of open issue titles labelled "arcane-auditor".
8. ACTION findings loop: for each finding, `_build_action_issue_title(finding)` is checked against `existing_titles`; if present, log DEBUG and skip; if absent, call `repo_obj.create_issue(title=..., body=..., labels=["arcane-auditor", "arcane-auditor:ACTION"])` and append `issue.html_url` to `created_urls`.
9. After creating each ACTION issue, the title is added to `existing_titles` to prevent duplicate creation within the same run.
10. ADVICE block: if `advice_findings` is non-empty, title is `"[Arcane Auditor] ADVICE Summary"`; duplicate check against `existing_titles`; if absent, `repo_obj.create_issue(...)` with `labels=["arcane-auditor", "arcane-auditor:ADVICE"]`.
11. Returns `created_urls: list[str]`.

**Helper functions to verify exist:**
- `_ensure_label(repo_obj: Any, name: str, color: str) -> None` (line ~260): calls `repo_obj.get_label(name)`; on `exc.status == 404` calls `repo_obj.create_label(name=name, color=color)`; other statuses raise `ReporterError`.
- `_get_existing_issue_titles(repo_obj: Any) -> set[str]` (line ~283): calls `repo_obj.get_issues(state="open", labels=["arcane-auditor"])`; returns `{issue.title for issue in issues}`.
- `_build_action_issue_title(finding: Finding) -> str` (line ~302): returns `f"[Arcane Auditor] {finding.rule_id}: {finding.file_path}"`.
- `_build_action_issue_body(finding: Finding) -> str` (line ~314): returns a multi-line markdown string with rule_id, severity ACTION, file_path, line, message.
- `_build_advice_issue_body(findings: list[Finding]) -> str` (line ~341): returns a markdown table with one row per ADVICE finding.

### 2. MODIFY IMPL_PLAN.md
- operation: MODIFY
- reason: Mark P4.3 as complete since implementation is fully present
- anchor: `- [ ] P4.3: Implement format_github_issues(scan_result, repo: str, token: str) in reporter.py`

#### Change to make:
Replace:
```
- [ ] P4.3: Implement format_github_issues(scan_result, repo: str, token: str) in reporter.py -- create one GitHub issue per ACTION finding, group ADVICE findings into a single summary issue. Use PyGithub. Label issues with "arcane-auditor" and severity labels. Check for duplicate issues before creating (by title match). Return list of created issue URLs
```
With:
```
- [x] P4.3: Implement format_github_issues(scan_result, repo: str, token: str) in reporter.py -- create one GitHub issue per ACTION finding, group ADVICE findings into a single summary issue. Use PyGithub. Label issues with "arcane-auditor" and severity labels. Check for duplicate issues before creating (by title match). Return list of created issue URLs
```

---

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.reporter import format_github_issues; print('import OK')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile src/reporter.py && echo 'syntax OK'`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -v` (no test_reporter.py yet -- that is P4.5; existing tests for scanner, runner, models, config must still pass)
- smoke: Run `uv run python -c "from src.reporter import format_github_issues, _ensure_label, _get_existing_issue_titles, _build_action_issue_title, _build_action_issue_body, _build_advice_issue_body; print('all helpers importable')"` and expect the string `all helpers importable`.

---

## Constraints
- Do NOT rewrite or overwrite any existing function in src/reporter.py.
- Do NOT create tests/test_reporter.py -- that is P4.5, a separate task.
- Do NOT install any new packages.
- Do NOT modify pyproject.toml.
- Do NOT modify src/models.py.
- The only file that changes content is IMPL_PLAN.md (checkbox flip from `[ ]` to `[x]` on P4.3).
