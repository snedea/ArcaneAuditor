# Plan: P4.3

## Dependencies
- list: [pygithub>=2.1.1]  # already present in pyproject.toml -- no new install needed
- commands: []  # no install commands required; pygithub is already a declared dependency

## File Operations (in execution order)

### 1. MODIFY src/reporter.py
- operation: MODIFY
- reason: Add format_github_issues() public function plus five private helpers, and update the report_findings dispatcher stub for GITHUB_ISSUES

#### Imports / Dependencies
Add at the top of the file, immediately after `from collections import Counter`:
```
from github import Github, GithubException
```
The full import block must remain:
```python
from __future__ import annotations

import json
import logging
from collections import Counter

from github import Github, GithubException

from src.models import Finding, ReportFormat, ReporterError, ScanResult, Severity
```

#### Functions

---

**signature**: `def _ensure_label(repo_obj: github.Repository.Repository, name: str, color: str) -> None:`
- purpose: Create the GitHub label if it does not already exist on the repo; silently succeed if it does.
- logic:
  1. Call `repo_obj.get_label(name)` inside a try block.
  2. If `GithubException` is raised and `exc.status == 404`, call `repo_obj.create_label(name=name, color=color)`.
  3. If `GithubException` is raised with any status other than 404, raise `ReporterError(f"GitHub API error ensuring label {name!r}: {exc}")` from exc.
  4. If `get_label` succeeds (no exception), the label already exists -- return without doing anything.
- calls: `repo_obj.get_label(name)`, `repo_obj.create_label(name=name, color=color)`
- returns: `None`
- error handling: `GithubException` with status==404 triggers create; any other status raises `ReporterError`

Note: `github.Repository.Repository` is a forward reference from PyGithub; use `Any` or the string form. The actual parameter type annotation to use in the file is `Any` imported from `typing`, OR simply write the type as `github.Repository.Repository` and add `import github` -- but to keep it simple use the concrete positional arg without a typed annotation since PyGithub does not expose clean public types. Instead, declare the parameter type as the return type of `Github.get_repo`:

Exact signature to write: `def _ensure_label(repo_obj: Any, name: str, color: str) -> None:`

Add `from typing import Any` to the imports block.

Updated full import block:
```python
from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from github import Github, GithubException

from src.models import Finding, ReportFormat, ReporterError, ScanResult, Severity
```

---

**signature**: `def _get_existing_issue_titles(repo_obj: Any) -> set[str]:`
- purpose: Return the set of titles of all currently-open GitHub issues labelled "arcane-auditor".
- logic:
  1. Call `repo_obj.get_issues(state="open", labels=["arcane-auditor"])` inside a try block.
  2. Iterate the paginated result and collect `issue.title` into a `set[str]`.
  3. Return the set.
  4. If `GithubException` is raised, raise `ReporterError(f"GitHub API error fetching existing issues: {exc}")` from exc.
- calls: `repo_obj.get_issues(state="open", labels=["arcane-auditor"])`
- returns: `set[str]`
- error handling: `GithubException` -> `ReporterError`

---

**signature**: `def _build_action_issue_title(finding: Finding) -> str:`
- purpose: Build the canonical GitHub issue title for one ACTION finding.
- logic:
  1. Return the f-string: `f"[Arcane Auditor] {finding.rule_id}: {finding.file_path}"`
- calls: none
- returns: `str`
- error handling: none

---

**signature**: `def _build_action_issue_body(finding: Finding) -> str:`
- purpose: Build the markdown issue body for one ACTION finding.
- logic:
  1. Build and return a multi-line string with the following sections:
     - `## {finding.rule_id}` as the heading
     - `**Severity:** ACTION`
     - `**File:** {finding.file_path}`
     - `**Line:** {finding.line}`
     - `**Message:**` followed by a blank line and then `{finding.message}` in a blockquote: `> {finding.message}`
     - A horizontal rule `---`
     - Footer: `*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*`
  2. Use `"\n".join(lines)` where `lines` is a `list[str]` built from the above sections.
- calls: none
- returns: `str`
- error handling: none

---

**signature**: `def _build_advice_issue_body(findings: list[Finding]) -> str:`
- purpose: Build the markdown issue body for the grouped ADVICE summary issue.
- logic:
  1. Start `lines: list[str] = []`.
  2. Append `f"## Arcane Auditor ADVICE Summary ({len(findings)} findings)"`.
  3. Append `"These are advisory findings -- they do not require immediate action but indicate opportunities for improvement."`.
  4. Append `""` (blank line).
  5. Append the markdown table header: `"| Rule | File | Line | Message |"`.
  6. Append the table separator: `"| --- | --- | --- | --- |"`.
  7. For each `f` in `findings`, append a table row: `f"| {f.rule_id} | {f.file_path} | {f.line} | {f.message} |"`.
  8. Append `""` (blank line).
  9. Append `"---"`.
  10. Append `"*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*"`.
  11. Return `"\n".join(lines)`.
- calls: none
- returns: `str`
- error handling: none

---

**signature**: `def format_github_issues(scan_result: ScanResult, repo: str, token: str) -> list[str]:`
- purpose: Create one GitHub issue per ACTION finding and one grouped issue for all ADVICE findings; skip duplicates by title; return list of created issue HTML URLs.
- logic:
  1. Call `gh = Github(token)`.
  2. Inside a try block, call `repo_obj = gh.get_repo(repo)`. If `GithubException` is raised, raise `ReporterError(f"GitHub API error accessing repo {repo!r}: {exc}")` from exc.
  3. Call `_ensure_label(repo_obj, "arcane-auditor", "0075ca")`.
  4. Call `_ensure_label(repo_obj, "arcane-auditor:ACTION", "e11d48")`.
  5. Call `_ensure_label(repo_obj, "arcane-auditor:ADVICE", "f59e0b")`.
  6. Call `existing_titles = _get_existing_issue_titles(repo_obj)`.
  7. Set `created_urls: list[str] = []`.
  8. Compute `action_findings = [f for f in scan_result.findings if f.severity == Severity.ACTION]`.
  9. Compute `advice_findings = [f for f in scan_result.findings if f.severity == Severity.ADVICE]`.
  10. For each `finding` in `action_findings`:
      a. Compute `title = _build_action_issue_title(finding)`.
      b. If `title in existing_titles`, call `logger.debug("Skipping duplicate issue: %s", title)` and `continue`.
      c. Compute `body = _build_action_issue_body(finding)`.
      d. Inside a try block, call `issue = repo_obj.create_issue(title=title, body=body, labels=["arcane-auditor", "arcane-auditor:ACTION"])`.
      e. If `GithubException` is raised, raise `ReporterError(f"GitHub API error creating issue {title!r}: {exc}")` from exc.
      f. Append `issue.html_url` to `created_urls`.
  11. If `advice_findings` is not empty:
      a. Compute `title = "[Arcane Auditor] ADVICE Summary"`.
      b. If `title in existing_titles`, call `logger.debug("Skipping duplicate advice summary issue")` and skip the block (do not create).
      c. Otherwise: compute `body = _build_advice_issue_body(advice_findings)`.
      d. Inside a try block, call `issue = repo_obj.create_issue(title=title, body=body, labels=["arcane-auditor", "arcane-auditor:ADVICE"])`.
      e. If `GithubException` is raised, raise `ReporterError(f"GitHub API error creating ADVICE summary issue: {exc}")` from exc.
      f. Append `issue.html_url` to `created_urls`.
  12. Return `created_urls`.
- calls: `Github(token)`, `gh.get_repo(repo)`, `_ensure_label()`, `_get_existing_issue_titles()`, `_build_action_issue_title()`, `_build_action_issue_body()`, `_build_advice_issue_body()`, `repo_obj.create_issue()`
- returns: `list[str]`
- error handling: All `GithubException` raised during API calls become `ReporterError` with descriptive messages.

---

#### Wiring / Integration

**Update `report_findings` dispatcher** -- the existing stub for `GITHUB_ISSUES` format at line 32 raises `ReporterError("GitHub Issues format not yet implemented")`. Update it to raise:
```python
raise ReporterError(
    "GitHub Issues format requires repo and token -- call format_github_issues() directly"
)
```

Anchor for this change (exact line to locate): `raise ReporterError("GitHub Issues format not yet implemented")`

**Placement of new functions** -- append all new private helpers and the public `format_github_issues` function after the last existing function (`_build_sarif_result`). Order within the file:
1. `format_github_issues` (public, immediately after `_build_sarif_result`)
2. `_ensure_label` (private helper)
3. `_get_existing_issue_titles` (private helper)
4. `_build_action_issue_title` (private helper)
5. `_build_action_issue_body` (private helper)
6. `_build_advice_issue_body` (private helper)

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.reporter import format_github_issues, _ensure_label, _get_existing_issue_titles, _build_action_issue_title, _build_action_issue_body, _build_advice_issue_body; print('imports ok')" `
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_runner.py -q` (existing tests must still pass; P4.5 will add reporter-specific tests)
- smoke:
  1. Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.reporter import _build_action_issue_title, _build_action_issue_body, _build_advice_issue_body; from src.models import Finding, Severity; f = Finding(rule_id='ScriptVarUsageRule', severity=Severity.ACTION, message='Use let or const instead of var', file_path='dirtyPage.pmd', line=5); print(_build_action_issue_title(f)); print(_build_action_issue_body(f))"` and verify the output contains `[Arcane Auditor] ScriptVarUsageRule: dirtyPage.pmd` in the title and the finding details in the body.
  2. Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.reporter import _build_advice_issue_body; from src.models import Finding, Severity; findings = [Finding(rule_id='ScriptConsoleLogRule', severity=Severity.ADVICE, message='Remove console.log', file_path='helpers.script', line=10)]; print(_build_advice_issue_body(findings))"` and verify it outputs a markdown table with the finding row.

## Constraints
- Do NOT modify ARCHITECTURE.md, CLAUDE.md, IMPL_PLAN.md, pyproject.toml, or any test files (P4.5 handles tests).
- Do NOT add any new dependencies to pyproject.toml; `pygithub` is already declared.
- Do NOT implement `format_pr_comment` (that is P4.4).
- Do NOT make the `report_findings` dispatcher call `format_github_issues` -- it cannot because it lacks the `repo` and `token` parameters; only update the error message in the stub.
- Do NOT use `shell=True` anywhere.
- The `token` parameter must be passed directly to `Github(token)` -- do not log or print the token value.
- All `GithubException` must be caught and re-raised as `ReporterError`; never let PyGithub exceptions surface to callers.
- Label colors must be passed WITHOUT the `#` prefix (PyGithub's `create_label` expects a 6-character hex string, no `#`).
- Use `Field(default_factory=list)` convention is already followed in models.py -- no model changes needed for this task.
