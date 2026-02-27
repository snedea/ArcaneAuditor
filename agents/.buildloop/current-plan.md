# Plan: P4.5

## Dependencies
- list: []
- commands: []
  (All required packages -- pytest, pygithub -- are already in pyproject.toml. No new installs needed.)

## File Operations (in execution order)

### 1. CREATE tests/test_reporter.py
- operation: CREATE
- reason: P4.5 requires tests covering format_json, format_sarif, format_summary, format_github_issues, format_pr_comment, and the report_findings dispatcher. PyGithub calls must be mocked.

#### Imports / Dependencies
```python
from __future__ import annotations

import json
from unittest.mock import MagicMock, call, patch

import pytest
from github import GithubException

from src.models import ExitCode, Finding, ReportFormat, ReporterError, ScanResult, Severity
from src.reporter import (
    format_github_issues,
    format_json,
    format_pr_comment,
    format_sarif,
    format_summary,
    report_findings,
)
```

#### Module-level helpers (plain functions, not fixtures)

**`_make_finding`**
- signature: `def _make_finding(rule_id: str = "TestRule", severity: Severity = Severity.ACTION, message: str = "test message", file_path: str = "test.pmd", line: int = 10) -> Finding:`
- purpose: Build a Finding with overridable fields for test parameterization
- logic:
  1. Return `Finding(rule_id=rule_id, severity=severity, message=message, file_path=file_path, line=line)`
- returns: `Finding`

**`_make_scan_result`**
- signature: `def _make_scan_result(findings: list[Finding] | None = None, exit_code: ExitCode = ExitCode.ISSUES_FOUND) -> ScanResult:`
- purpose: Build a ScanResult with overridable fields
- logic:
  1. If findings is None, set findings to `[]`
  2. Return `ScanResult(repo="owner/test-repo", findings_count=len(findings), findings=findings, exit_code=exit_code)`
- returns: `ScanResult`

#### Fixtures

**`mock_github_ctx` (function-scoped pytest fixture)**
- purpose: Patch `src.reporter.Github` and yield a tuple `(mock_cls, mock_gh, mock_repo)` for GitHub API tests
- logic:
  1. Enter `patch("src.reporter.Github") as mock_cls`
  2. Create `mock_gh = MagicMock()`
  3. Set `mock_cls.return_value.__enter__.return_value = mock_gh`
  4. Set `mock_cls.return_value.__exit__.return_value = False`
  5. Create `mock_repo = MagicMock()`
  6. Set `mock_gh.get_repo.return_value = mock_repo`
  7. Set `mock_repo.get_issues.return_value = []` (no existing issues by default)
  8. Create `mock_issue = MagicMock()` and set `mock_issue.html_url = "https://github.com/owner/test-repo/issues/1"`
  9. Set `mock_repo.create_issue.return_value = mock_issue`
  10. `yield mock_cls, mock_gh, mock_repo`
- returns: yields `tuple[MagicMock, MagicMock, MagicMock]`

**`mock_pr_ctx` (function-scoped pytest fixture)**
- purpose: Extend mock_github_ctx with a mock PR and comment for format_pr_comment tests
- logic:
  1. Enter `patch("src.reporter.Github") as mock_cls`
  2. Create `mock_gh = MagicMock()`
  3. Set `mock_cls.return_value.__enter__.return_value = mock_gh`
  4. Set `mock_cls.return_value.__exit__.return_value = False`
  5. Create `mock_repo = MagicMock()`
  6. Set `mock_gh.get_repo.return_value = mock_repo`
  7. Create `mock_pr = MagicMock()`
  8. Set `mock_repo.get_pull.return_value = mock_pr`
  9. Create `mock_comment = MagicMock()`
  10. Set `mock_comment.html_url = "https://github.com/owner/test-repo/pull/1#issuecomment-99"`
  11. Set `mock_pr.create_issue_comment.return_value = mock_comment`
  12. `yield mock_cls, mock_gh, mock_repo, mock_pr`
- returns: yields `tuple[MagicMock, MagicMock, MagicMock, MagicMock]`

#### Test Classes

---

**`class TestFormatJson`**

`test_returns_valid_json_string`
- logic:
  1. Call `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `format_json(scan_result)`
  3. Call `json.loads(result)` -- assert no exception is raised
  4. Assert that the parsed value is a `dict`

`test_json_contains_required_top_level_keys`
- logic:
  1. Build a scan_result with `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `format_json(scan_result)` and parse with `json.loads`
  3. Assert that `parsed.keys()` is a superset of `{"repo", "timestamp", "findings_count", "findings", "exit_code"}`

`test_json_repo_matches_scan_result`
- logic:
  1. Build scan_result with `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Parse `format_json(scan_result)` with `json.loads`
  3. Assert `parsed["repo"] == "owner/test-repo"`

`test_json_findings_count_matches`
- logic:
  1. Build two findings: `_make_finding()` and `_make_finding(rule_id="Rule2", severity=Severity.ADVICE)`
  2. Build `_make_scan_result(findings=[f1, f2])`
  3. Parse `format_json(scan_result)` with `json.loads`
  4. Assert `parsed["findings_count"] == 2`
  5. Assert `len(parsed["findings"]) == 2`

`test_json_findings_contain_expected_fields`
- logic:
  1. Build `finding = _make_finding(rule_id="ScriptConsoleLogRule", severity=Severity.ACTION, message="bad log", file_path="app.pmd", line=42)`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_json(scan_result)` with `json.loads`
  4. Set `parsed_finding = parsed["findings"][0]`
  5. Assert `parsed_finding["rule_id"] == "ScriptConsoleLogRule"`
  6. Assert `parsed_finding["severity"] == "ACTION"`
  7. Assert `parsed_finding["message"] == "bad log"`
  8. Assert `parsed_finding["file_path"] == "app.pmd"`
  9. Assert `parsed_finding["line"] == 42`

`test_json_roundtrip_validates_against_scan_result_schema`
- logic:
  1. Build `_make_scan_result(findings=[_make_finding()])`
  2. Call `format_json(scan_result)` and parse with `json.loads`
  3. Call `ScanResult.model_validate(parsed)` -- assert no exception is raised
  4. Assert the reconstructed ScanResult `.repo == scan_result.repo`
  5. Assert `.findings_count == scan_result.findings_count`

`test_json_is_indented_with_2_spaces`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `format_json(scan_result)`
  3. Assert `result.startswith("{\n  ")` is True (2-space indent from json.dumps with indent=2)

`test_report_findings_json_dispatches_to_format_json`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `report_findings(scan_result, ReportFormat.JSON)`
  3. Assert `json.loads(result)` does not raise (result is valid JSON)

---

**`class TestFormatSarif`**

`test_returns_valid_json_string`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `format_sarif(scan_result)` and parse with `json.loads` -- assert no exception

`test_sarif_version_is_2_1_0`
- logic:
  1. Parse `format_sarif(_make_scan_result())` with `json.loads`
  2. Assert `doc["version"] == "2.1.0"`

`test_sarif_has_runs_list`
- logic:
  1. Parse `format_sarif(_make_scan_result())` with `json.loads`
  2. Assert `"runs"` in `doc`
  3. Assert `isinstance(doc["runs"], list)`
  4. Assert `len(doc["runs"]) == 1`

`test_sarif_runs_has_results_key`
- logic:
  1. Parse `format_sarif(_make_scan_result())` with `json.loads`
  2. Assert `"results"` in `doc["runs"][0]`

`test_sarif_runs_has_tool_driver_rules_key`
- logic:
  1. Parse `format_sarif(_make_scan_result())` with `json.loads`
  2. Assert `"tool"` in `doc["runs"][0]`
  3. Assert `"driver"` in `doc["runs"][0]["tool"]`
  4. Assert `"rules"` in `doc["runs"][0]["tool"]["driver"]`

`test_sarif_empty_findings_produces_empty_results`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Parse `format_sarif(scan_result)` with `json.loads`
  3. Assert `doc["runs"][0]["results"] == []`
  4. Assert `doc["runs"][0]["tool"]["driver"]["rules"] == []`

`test_sarif_action_severity_maps_to_error`
- logic:
  1. Build `finding = _make_finding(severity=Severity.ACTION, rule_id="ActionRule")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Assert `doc["runs"][0]["results"][0]["level"] == "error"`

`test_sarif_advice_severity_maps_to_warning`
- logic:
  1. Build `finding = _make_finding(severity=Severity.ADVICE, rule_id="AdviceRule")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Assert `doc["runs"][0]["results"][0]["level"] == "warning"`

`test_sarif_result_contains_rule_id`
- logic:
  1. Build `finding = _make_finding(rule_id="ScriptVarUsageRule")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Assert `doc["runs"][0]["results"][0]["ruleId"] == "ScriptVarUsageRule"`

`test_sarif_result_rule_index_is_valid_integer`
- logic:
  1. Build `finding = _make_finding(rule_id="SomeRule")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Assert `isinstance(doc["runs"][0]["results"][0]["ruleIndex"], int)`
  5. Assert `doc["runs"][0]["results"][0]["ruleIndex"] >= 0`

`test_sarif_rule_index_matches_rules_array_position`
- logic:
  1. Build two findings with different rule_ids: `f1 = _make_finding(rule_id="RuleA")` and `f2 = _make_finding(rule_id="RuleB", severity=Severity.ADVICE)`
  2. Build `_make_scan_result(findings=[f1, f2])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Set `rules = doc["runs"][0]["tool"]["driver"]["rules"]`
  5. Build `rule_id_to_index = {r["id"]: i for i, r in enumerate(rules)}`
  6. For each result in `doc["runs"][0]["results"]`: assert `result["ruleIndex"] == rule_id_to_index[result["ruleId"]]`

`test_sarif_rules_are_deduplicated`
- logic:
  1. Build two findings with the same rule_id: `f1 = _make_finding(rule_id="DupRule")` and `f2 = _make_finding(rule_id="DupRule", file_path="other.pmd")`
  2. Build `_make_scan_result(findings=[f1, f2])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Set `rules = doc["runs"][0]["tool"]["driver"]["rules"]`
  5. Assert `len(rules) == 1` (only one entry despite two findings with same rule)

`test_sarif_line_zero_clamped_to_1`
- logic:
  1. Build `finding = _make_finding(line=0)`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Set `start_line = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"]`
  5. Assert `start_line == 1`

`test_sarif_nonzero_line_preserved`
- logic:
  1. Build `finding = _make_finding(line=42)`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Set `start_line = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"]`
  5. Assert `start_line == 42`

`test_sarif_file_path_in_artifact_location`
- logic:
  1. Build `finding = _make_finding(file_path="src/myapp.pmd")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Set `uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]`
  5. Assert `uri == "src/myapp.pmd"`

`test_sarif_rule_descriptor_has_required_fields`
- logic:
  1. Build `finding = _make_finding(rule_id="TestDescriptor")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Parse `format_sarif(scan_result)` with `json.loads`
  4. Set `rule = doc["runs"][0]["tool"]["driver"]["rules"][0]`
  5. Assert `"id"` in `rule`
  6. Assert `"name"` in `rule`
  7. Assert `"shortDescription"` in `rule`
  8. Assert `"defaultConfiguration"` in `rule`
  9. Assert `"level"` in `rule["defaultConfiguration"]`

`test_report_findings_sarif_dispatches_to_format_sarif`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `report_findings(scan_result, ReportFormat.SARIF)`
  3. Assert `json.loads(result)["version"] == "2.1.0"`

---

**`class TestFormatSummary`**

`test_contains_repo_name`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `format_summary(scan_result)`
  3. Assert `"owner/test-repo"` in `result`

`test_contains_total_findings_count`
- logic:
  1. Build two findings and `_make_scan_result(findings=[f1, f2])`
  2. Call `format_summary(scan_result)`
  3. Assert `"Total findings: 2"` in `result`

`test_contains_action_count`
- logic:
  1. Build `f1 = _make_finding(severity=Severity.ACTION)` and `f2 = _make_finding(rule_id="R2", severity=Severity.ADVICE)`
  2. Build `_make_scan_result(findings=[f1, f2])`
  3. Call `format_summary(scan_result)`
  4. Assert `"ACTION: 1"` in `result`

`test_contains_advice_count`
- logic:
  1. Build `f1 = _make_finding(severity=Severity.ACTION)` and `f2 = _make_finding(rule_id="R2", severity=Severity.ADVICE)`
  2. Build `_make_scan_result(findings=[f1, f2])`
  3. Call `format_summary(scan_result)`
  4. Assert `"ADVICE: 1"` in `result`

`test_contains_rule_id_in_by_rule_section`
- logic:
  1. Build `finding = _make_finding(rule_id="ScriptConsoleLogRule")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Call `format_summary(scan_result)`
  4. Assert `"ScriptConsoleLogRule"` in `result`

`test_contains_file_path_in_by_file_section`
- logic:
  1. Build `finding = _make_finding(file_path="src/myPage.pmd")`
  2. Build `_make_scan_result(findings=[finding])`
  3. Call `format_summary(scan_result)`
  4. Assert `"src/myPage.pmd"` in `result`

`test_clean_scan_shows_no_findings_message`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `format_summary(scan_result)`
  3. Assert `"No findings"` in `result`

`test_clean_scan_does_not_show_rule_section`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `format_summary(scan_result)`
  3. Assert `"By Rule:"` not in `result`

`test_report_findings_summary_dispatches_to_format_summary`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `report_findings(scan_result, ReportFormat.SUMMARY)`
  3. Assert `"owner/test-repo"` in `result` (confirms format_summary was called)

---

**`class TestFormatGithubIssues`**

All tests in this class use the `mock_github_ctx` fixture as a parameter.

`test_creates_one_issue_per_action_finding`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build `f1 = _make_finding(rule_id="RuleA", severity=Severity.ACTION, file_path="a.pmd")` and `f2 = _make_finding(rule_id="RuleB", severity=Severity.ACTION, file_path="b.pmd")`
  3. Build `_make_scan_result(findings=[f1, f2])`
  4. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  5. Assert `mock_repo.create_issue.call_count == 2`

`test_groups_all_advice_into_single_issue`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build `f1 = _make_finding(rule_id="AdvR1", severity=Severity.ADVICE)` and `f2 = _make_finding(rule_id="AdvR2", severity=Severity.ADVICE, file_path="b.pmd")`
  3. Build `_make_scan_result(findings=[f1, f2])`
  4. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  5. Assert `mock_repo.create_issue.call_count == 1`
  6. Assert the `title` kwarg of the call contains `"ADVICE Summary"`

`test_returns_list_of_html_urls`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build one ACTION finding and `_make_scan_result(findings=[f])`
  3. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  4. Assert `isinstance(result, list)`
  5. Assert `len(result) == 1`
  6. Assert `result[0] == "https://github.com/owner/test-repo/issues/1"`

`test_skips_duplicate_action_issue`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build `finding = _make_finding(rule_id="DupRule", severity=Severity.ACTION, file_path="x.pmd")`
  3. Build `_make_scan_result(findings=[finding])`
  4. Compute expected title: `"[Arcane Auditor] DupRule: x.pmd"`
  5. Create a mock existing issue: `existing = MagicMock(); existing.title = "[Arcane Auditor] DupRule: x.pmd"`
  6. Set `mock_repo.get_issues.return_value = [existing]`
  7. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  8. Assert `mock_repo.create_issue.call_count == 0`
  9. Assert `result == []`

`test_skips_duplicate_advice_summary_issue`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build `finding = _make_finding(rule_id="AdvR", severity=Severity.ADVICE)`
  3. Build `_make_scan_result(findings=[finding])`
  4. Create mock existing issue: `existing = MagicMock(); existing.title = "[Arcane Auditor] ADVICE Summary"`
  5. Set `mock_repo.get_issues.return_value = [existing]`
  6. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  7. Assert `mock_repo.create_issue.call_count == 0`

`test_no_findings_creates_no_issues`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  3. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  4. Assert `mock_repo.create_issue.call_count == 0`
  5. Assert `result == []`

`test_action_issue_title_format`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build `finding = _make_finding(rule_id="ScriptVarUsageRule", severity=Severity.ACTION, file_path="myPage.pmd")`
  3. Build `_make_scan_result(findings=[finding])`
  4. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  5. Assert `mock_repo.create_issue.call_count == 1`
  6. Set `call_kwargs = mock_repo.create_issue.call_args[1]`
  7. Assert `call_kwargs["title"] == "[Arcane Auditor] ScriptVarUsageRule: myPage.pmd"`

`test_get_repo_github_exception_raises_reporter_error`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Set `mock_gh.get_repo.side_effect = GithubException(404, "not found", None)`
  3. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  4. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")` inside `pytest.raises(ReporterError)`
  5. Assert the exception message contains `"owner/test-repo"`

`test_create_issue_github_exception_raises_reporter_error`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Set `mock_repo.create_issue.side_effect = GithubException(422, "error", None)`
  3. Build `finding = _make_finding(severity=Severity.ACTION)`
  4. Build `_make_scan_result(findings=[finding])`
  5. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")` inside `pytest.raises(ReporterError)`

`test_action_issue_labels_include_arcane_auditor_and_severity`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo` from `mock_github_ctx`
  2. Build `finding = _make_finding(severity=Severity.ACTION)`
  3. Build `_make_scan_result(findings=[finding])`
  4. Call `format_github_issues(scan_result, "owner/test-repo", "fake-token")`
  5. Set `call_kwargs = mock_repo.create_issue.call_args[1]`
  6. Assert `"arcane-auditor"` in `call_kwargs["labels"]`
  7. Assert `"arcane-auditor:ACTION"` in `call_kwargs["labels"]`

---

**`class TestFormatPrComment`**

All tests in this class use the `mock_pr_ctx` fixture.

`test_posts_single_comment`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  3. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")`
  4. Assert `mock_pr.create_issue_comment.call_count == 1`

`test_returns_comment_html_url`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  3. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")`
  4. Assert `result == "https://github.com/owner/test-repo/pull/1#issuecomment-99"`

`test_clean_comment_body_contains_no_findings_message`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  3. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")`
  4. Set `body = mock_pr.create_issue_comment.call_args[0][0]`
  5. Assert `"No findings"` in `body`

`test_comment_body_contains_action_findings_table`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `finding = _make_finding(rule_id="ScriptConsoleLogRule", severity=Severity.ACTION, file_path="app.pmd", line=5)`
  3. Build `_make_scan_result(findings=[finding])`
  4. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")`
  5. Set `body = mock_pr.create_issue_comment.call_args[0][0]`
  6. Assert `"ScriptConsoleLogRule"` in `body`
  7. Assert `"app.pmd"` in `body`

`test_comment_body_advice_in_collapsible_details`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `finding = _make_finding(rule_id="AdviceRule", severity=Severity.ADVICE)`
  3. Build `_make_scan_result(findings=[finding])`
  4. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")`
  5. Set `body = mock_pr.create_issue_comment.call_args[0][0]`
  6. Assert `"<details>"` in `body`
  7. Assert `"<summary>"` in `body`
  8. Assert `"AdviceRule"` in `body`

`test_comment_body_has_blank_line_after_summary_tag`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `finding = _make_finding(severity=Severity.ADVICE)`
  3. Build `_make_scan_result(findings=[finding])`
  4. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")`
  5. Set `body = mock_pr.create_issue_comment.call_args[0][0]`
  6. Assert `"</summary>\n\n"` in `body` (blank line after closing summary tag for table rendering)

`test_comment_body_contains_findings_count`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `f1 = _make_finding(severity=Severity.ACTION)` and `f2 = _make_finding(rule_id="R2", severity=Severity.ADVICE)`
  3. Build `_make_scan_result(findings=[f1, f2])`
  4. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")`
  5. Set `body = mock_pr.create_issue_comment.call_args[0][0]`
  6. Assert `"2 findings"` in `body`
  7. Assert `"ACTION: 1"` in `body`
  8. Assert `"ADVICE: 1"` in `body`

`test_get_repo_github_exception_raises_reporter_error`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Set `mock_gh.get_repo.side_effect = GithubException(404, "not found", None)`
  3. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  4. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")` inside `pytest.raises(ReporterError)`
  5. Assert the exception message contains `"owner/test-repo"`

`test_get_pull_github_exception_raises_reporter_error`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Set `mock_repo.get_pull.side_effect = GithubException(404, "PR not found", None)`
  3. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  4. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")` inside `pytest.raises(ReporterError)`
  5. Assert the exception message contains `"#1"`

`test_create_comment_github_exception_raises_reporter_error`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Set `mock_pr.create_issue_comment.side_effect = GithubException(500, "server error", None)`
  3. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  4. Call `format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")` inside `pytest.raises(ReporterError)`
  5. Assert the exception message contains `"#1"`

`test_get_pull_called_with_pr_number`
- logic:
  1. Receive `mock_cls, mock_gh, mock_repo, mock_pr` from `mock_pr_ctx`
  2. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  3. Call `format_pr_comment(scan_result, "owner/test-repo", 42, "fake-token")`
  4. Assert `mock_repo.get_pull.call_args[0][0] == 42`

---

**`class TestReportFindingsDispatcher`**

`test_github_issues_format_raises_reporter_error`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `report_findings(scan_result, ReportFormat.GITHUB_ISSUES)` inside `pytest.raises(ReporterError)`
  3. Assert the exception message contains `"format_github_issues"`

`test_pr_comment_format_raises_reporter_error`
- logic:
  1. Build `_make_scan_result(findings=[], exit_code=ExitCode.CLEAN)`
  2. Call `report_findings(scan_result, ReportFormat.PR_COMMENT)` inside `pytest.raises(ReporterError)`
  3. Assert the exception message contains `"format_pr_comment"`

---

#### Wiring / Integration
- `tests/test_reporter.py` imports directly from `src.reporter` and `src.models`
- `src.reporter.Github` is patched at its import location in `src.reporter`, not in the `github` module
- All GitHub API calls are sync; use `MagicMock` (not `AsyncMock`) throughout
- The `mock_github_ctx` and `mock_pr_ctx` fixtures must use `patch` as a context manager (not decorator) so they can be used as pytest fixtures with `yield`

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run ruff check tests/test_reporter.py`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_reporter.py -v`
- smoke: Run `uv run pytest tests/test_reporter.py -v 2>&1 | tail -20` and verify all tests PASSED with no ERRORS. Then run `uv run pytest tests/ -v 2>&1 | tail -10` to confirm no regressions in other test files.

## Constraints
- Do NOT modify src/reporter.py -- all functions are already implemented and correct
- Do NOT modify src/models.py
- Do NOT modify any existing test files
- Do NOT add any new dependencies to pyproject.toml
- Do NOT use AsyncMock anywhere -- all GitHub API calls are synchronous
- Do NOT patch `github.Github` -- always patch `src.reporter.Github` (the import location)
- Do NOT use `patch` as a decorator on test methods -- use it inside fixtures with `yield` or as a context manager inside the test body
- The `mock_github_ctx` and `mock_pr_ctx` fixtures must be defined at module level (not inside test classes) so they are visible to the test classes
- The `GithubException` constructor signature is `GithubException(status, data, headers)` -- always pass all three positional args: e.g., `GithubException(404, "not found", None)`
