# Plan: P4.4

## Dependencies
- list: [] (PyGithub already declared as `pygithub>=2.1.1` in pyproject.toml -- no new packages needed)
- commands: []

## File Operations (in execution order)

### 1. MODIFY src/reporter.py
- operation: MODIFY
- reason: Add `format_pr_comment()` public function and `_build_pr_comment_body()` private helper; update the `PR_COMMENT` branch in the `report_findings()` dispatcher to reflect that the function now exists but requires extra parameters

#### Imports / Dependencies
No new imports required. All needed symbols (`Github`, `Auth`, `GithubException`, `Finding`, `ScanResult`, `Severity`, `ReporterError`) are already imported at the top of the file.

#### Functions

##### A. Update `report_findings()` dispatcher -- MODIFY existing function body

- anchor (unique line to locate the block): `raise ReporterError("PR Comment format not yet implemented")`
- Replace that single raise statement with:
  ```python
  raise ReporterError(
      "PR Comment format requires repo, pr_number, and token -- call format_pr_comment() directly"
  )
  ```

##### B. New function: `_build_pr_comment_body`

- signature: `def _build_pr_comment_body(scan_result: ScanResult) -> str:`
- purpose: Build the full markdown string for the PR comment body, including a clean-pass message or ACTION table plus collapsible ADVICE section.
- logic:
  1. Initialize `lines: list[str] = []`
  2. Append `"## Arcane Auditor Results"` to `lines`
  3. Append `""` (blank line) to `lines`
  4. If `scan_result.findings_count == 0`:
     a. Append `"No findings. This application is clean."` to `lines`
     b. Append `""` to `lines`
     c. Append `"---"` to `lines`
     d. Append `"*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*"` to `lines`
     e. Return `"\n".join(lines)`
  5. Build `action_findings: list[Finding] = [f for f in scan_result.findings if f.severity == Severity.ACTION]`
  6. Build `advice_findings: list[Finding] = [f for f in scan_result.findings if f.severity == Severity.ADVICE]`
  7. Append `f"**{scan_result.findings_count} findings** (ACTION: {scan_result.action_count}, ADVICE: {scan_result.advice_count})"` to `lines`
  8. Append `""` to `lines`
  9. If `action_findings` is non-empty:
     a. Append `"### ACTION Findings"` to `lines`
     b. Append `""` to `lines`
     c. Append `"| Rule | File | Line | Message |"` to `lines`
     d. Append `"| --- | --- | --- | --- |"` to `lines`
     e. For each `f` in `action_findings`:
        - Compute `safe_path = f.file_path.replace("|", r"\|").replace("\n", " ")`
        - Compute `safe_msg = f.message.replace("|", r"\|").replace("\n", " ")`
        - Append `f"| {f.rule_id} | {safe_path} | {f.line} | {safe_msg} |"` to `lines`
     f. Append `""` to `lines`
  10. If `advice_findings` is non-empty:
      a. Append `"<details>"` to `lines`
      b. Append `f"<summary>ADVICE Findings ({len(advice_findings)})</summary>"` to `lines`
      c. Append `""` to `lines`
      d. Append `"| Rule | File | Line | Message |"` to `lines`
      e. Append `"| --- | --- | --- | --- |"` to `lines`
      f. For each `f` in `advice_findings`:
         - Compute `safe_path = f.file_path.replace("|", r"\|").replace("\n", " ")`
         - Compute `safe_msg = f.message.replace("|", r"\|").replace("\n", " ")`
         - Append `f"| {f.rule_id} | {safe_path} | {f.line} | {safe_msg} |"` to `lines`
      g. Append `""` to `lines`
      h. Append `"</details>"` to `lines`
      i. Append `""` to `lines`
  11. Append `"---"` to `lines`
  12. Append `"*Found by [Arcane Auditor](https://github.com/snedea/homelab) -- deterministic rule-based code review.*"` to `lines`
  13. Return `"\n".join(lines)`
- calls: nothing external
- returns: `str` -- the full markdown body for the PR comment
- error handling: none (pure string manipulation, no I/O)
- docstring style: Google style, Args + Returns sections

##### C. New function: `format_pr_comment`

- signature: `def format_pr_comment(scan_result: ScanResult, repo: str, pr_number: int, token: str) -> str:`
- purpose: Post a single comment on a GitHub PR summarizing all findings, then return the comment's HTML URL.
- logic:
  1. Open a `with Github(auth=Auth.Token(token)) as gh:` context manager
  2. Inside the `with` block, call `gh.get_repo(repo)` and assign to `repo_obj`. Wrap in `try/except GithubException as exc` and raise `ReporterError(f"GitHub API error accessing repo {repo!r}: {exc}")` on failure.
  3. Call `repo_obj.get_pull(pr_number)` and assign to `pr`. Wrap in `try/except GithubException as exc` and raise `ReporterError(f"GitHub API error accessing PR #{pr_number} in {repo!r}: {exc}")` on failure.
  4. Call `_build_pr_comment_body(scan_result)` and assign to `body: str`.
  5. Call `pr.create_issue_comment(body)` and assign to `comment`. Wrap in `try/except GithubException as exc` and raise `ReporterError(f"GitHub API error posting comment on PR #{pr_number} in {repo!r}: {exc}")` on failure.
  6. Return `comment.html_url`
- calls: `_build_pr_comment_body(scan_result)`, `gh.get_repo(repo)`, `repo_obj.get_pull(pr_number)`, `pr.create_issue_comment(body)`
- returns: `str` -- the HTML URL of the created PR comment (e.g. `"https://github.com/owner/repo/pull/42#issuecomment-12345"`)
- error handling: all three GitHub API calls (`get_repo`, `get_pull`, `create_issue_comment`) are individually wrapped in `try/except GithubException` with distinct error messages that identify which call failed and include the offending repo/PR number
- docstring style: Google style, Args + Returns + Raises sections

#### Placement within the file

- `_build_pr_comment_body` must be inserted AFTER `_build_advice_issue_body` (the last existing private helper, ending at line 365) and BEFORE `format_pr_comment`.
- `format_pr_comment` must be inserted immediately after `_build_pr_comment_body`.
- Both functions go at the end of the file (after all existing code).
- Do NOT insert them between existing functions.

#### Wiring / Integration

- The `report_findings()` dispatcher already has a `PR_COMMENT` branch (lines 38-39). Update only the error message string in that branch -- do not change control flow or add new branches.
- No other files need modification for this task.

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run ruff check src/reporter.py`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -v` (no test_reporter.py exists yet -- P4.5 will add it; existing tests must still pass)
- smoke:
  1. Run the following Python snippet to verify the clean-path body renders correctly:
     ```
     cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
     from src.models import ScanResult, ExitCode
     from src.reporter import _build_pr_comment_body
     from datetime import datetime, UTC
     r = ScanResult(repo='test/repo', findings_count=0, findings=[], exit_code=ExitCode.CLEAN, timestamp=datetime.now(UTC))
     print(_build_pr_comment_body(r))
     "
     ```
     Expected output contains: `## Arcane Auditor Results` and `No findings. This application is clean.`
  2. Run the following to verify the findings-path body renders ACTION table and ADVICE details:
     ```
     cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
     from src.models import ScanResult, Finding, Severity, ExitCode
     from src.reporter import _build_pr_comment_body
     from datetime import datetime, UTC
     findings = [
         Finding(rule_id='ScriptVarUsageRule', severity=Severity.ACTION, message='Use let/const', file_path='dirtyPage.pmd', line=5),
         Finding(rule_id='ScriptStringConcatRule', severity=Severity.ADVICE, message='Use template literals', file_path='dirtyPage.pmd', line=10),
     ]
     r = ScanResult(repo='test/repo', findings_count=2, findings=findings, exit_code=ExitCode.ISSUES_FOUND, timestamp=datetime.now(UTC))
     print(_build_pr_comment_body(r))
     "
     ```
     Expected output contains: `### ACTION Findings`, `ScriptVarUsageRule`, `<details>`, `ADVICE Findings (1)`, `ScriptStringConcatRule`, `</details>`

## Constraints

- Do NOT modify `src/models.py` -- all needed types already exist.
- Do NOT modify `pyproject.toml` -- PyGithub is already declared.
- Do NOT modify `ARCHITECTURE.md`, `CLAUDE.md`, or `IMPL_PLAN.md`.
- Do NOT create `tests/test_reporter.py` -- that is P4.5.
- Do NOT use parameter names that shadow Python built-ins. The existing `format` parameter in `report_findings()` is pre-existing and must not be renamed; do not use `format` as a parameter name in any new function.
- The `<details>` / `<summary>` block must include a blank line after the `<summary>` tag and before the table so GitHub Markdown renders the table correctly inside the collapsible section.
- Use `logging.debug()` (not `print()`) for any diagnostic messages inside `format_pr_comment`.
- The `_build_pr_comment_body` helper is a private function (underscore prefix) and must NOT be called from `report_findings()` dispatcher -- it is only called by `format_pr_comment()`.
