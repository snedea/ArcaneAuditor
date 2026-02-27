from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

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


def _make_finding(
    rule_id: str = "TestRule",
    severity: Severity = Severity.ACTION,
    message: str = "test message",
    file_path: str = "test.pmd",
    line: int = 10,
) -> Finding:
    return Finding(rule_id=rule_id, severity=severity, message=message, file_path=file_path, line=line)


def _make_scan_result(
    findings: list[Finding] | None = None,
    exit_code: ExitCode = ExitCode.ISSUES_FOUND,
) -> ScanResult:
    if findings is None:
        findings = []
    return ScanResult(repo="owner/test-repo", findings_count=len(findings), findings=findings, exit_code=exit_code)


@pytest.fixture()
def mock_github_ctx():
    with patch("src.reporter.Github") as mock_cls:
        mock_gh = MagicMock()
        mock_cls.return_value.__enter__.return_value = mock_gh
        mock_cls.return_value.__exit__.return_value = False
        mock_repo = MagicMock()
        mock_gh.get_repo.return_value = mock_repo
        mock_repo.get_issues.return_value = []
        mock_issue = MagicMock()
        mock_issue.html_url = "https://github.com/owner/test-repo/issues/1"
        mock_repo.create_issue.return_value = mock_issue
        yield mock_cls, mock_gh, mock_repo


@pytest.fixture()
def mock_pr_ctx():
    with patch("src.reporter.Github") as mock_cls:
        mock_gh = MagicMock()
        mock_cls.return_value.__enter__.return_value = mock_gh
        mock_cls.return_value.__exit__.return_value = False
        mock_repo = MagicMock()
        mock_gh.get_repo.return_value = mock_repo
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_comment = MagicMock()
        mock_comment.html_url = "https://github.com/owner/test-repo/pull/1#issuecomment-99"
        mock_pr.create_issue_comment.return_value = mock_comment
        yield mock_cls, mock_gh, mock_repo, mock_pr


class TestFormatJson:
    def test_returns_valid_json_string(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = format_json(scan_result)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_json_contains_required_top_level_keys(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        parsed = json.loads(format_json(scan_result))
        assert parsed.keys() >= {"repo", "timestamp", "findings_count", "findings", "exit_code"}

    def test_json_repo_matches_scan_result(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        parsed = json.loads(format_json(scan_result))
        assert parsed["repo"] == "owner/test-repo"

    def test_json_findings_count_matches(self):
        f1 = _make_finding()
        f2 = _make_finding(rule_id="Rule2", severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[f1, f2])
        parsed = json.loads(format_json(scan_result))
        assert parsed["findings_count"] == 2
        assert len(parsed["findings"]) == 2

    def test_json_findings_contain_expected_fields(self):
        finding = _make_finding(rule_id="ScriptConsoleLogRule", severity=Severity.ACTION, message="bad log", file_path="app.pmd", line=42)
        scan_result = _make_scan_result(findings=[finding])
        parsed = json.loads(format_json(scan_result))
        parsed_finding = parsed["findings"][0]
        assert parsed_finding["rule_id"] == "ScriptConsoleLogRule"
        assert parsed_finding["severity"] == "ACTION"
        assert parsed_finding["message"] == "bad log"
        assert parsed_finding["file_path"] == "app.pmd"
        assert parsed_finding["line"] == 42

    def test_json_roundtrip_validates_against_scan_result_schema(self):
        scan_result = _make_scan_result(findings=[_make_finding()])
        parsed = json.loads(format_json(scan_result))
        reconstructed = ScanResult.model_validate(parsed)
        assert reconstructed.repo == scan_result.repo
        assert reconstructed.findings_count == scan_result.findings_count

    def test_json_is_indented_with_2_spaces(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = format_json(scan_result)
        assert result.startswith("{\n  ")

    def test_report_findings_json_dispatches_to_format_json(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = report_findings(scan_result, ReportFormat.JSON)
        json.loads(result)


class TestFormatSarif:
    def test_returns_valid_json_string(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        json.loads(format_sarif(scan_result))

    def test_sarif_version_is_2_1_0(self):
        doc = json.loads(format_sarif(_make_scan_result()))
        assert doc["version"] == "2.1.0"

    def test_sarif_has_runs_list(self):
        doc = json.loads(format_sarif(_make_scan_result()))
        assert "runs" in doc
        assert isinstance(doc["runs"], list)
        assert len(doc["runs"]) == 1

    def test_sarif_runs_has_results_key(self):
        doc = json.loads(format_sarif(_make_scan_result()))
        assert "results" in doc["runs"][0]

    def test_sarif_runs_has_tool_driver_rules_key(self):
        doc = json.loads(format_sarif(_make_scan_result()))
        assert "tool" in doc["runs"][0]
        assert "driver" in doc["runs"][0]["tool"]
        assert "rules" in doc["runs"][0]["tool"]["driver"]

    def test_sarif_empty_findings_produces_empty_results(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        doc = json.loads(format_sarif(scan_result))
        assert doc["runs"][0]["results"] == []
        assert doc["runs"][0]["tool"]["driver"]["rules"] == []

    def test_sarif_action_severity_maps_to_error(self):
        finding = _make_finding(severity=Severity.ACTION, rule_id="ActionRule")
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        assert doc["runs"][0]["results"][0]["level"] == "error"

    def test_sarif_advice_severity_maps_to_warning(self):
        finding = _make_finding(severity=Severity.ADVICE, rule_id="AdviceRule")
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        assert doc["runs"][0]["results"][0]["level"] == "warning"

    def test_sarif_result_contains_rule_id(self):
        finding = _make_finding(rule_id="ScriptVarUsageRule")
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        assert doc["runs"][0]["results"][0]["ruleId"] == "ScriptVarUsageRule"

    def test_sarif_result_rule_index_is_valid_integer(self):
        finding = _make_finding(rule_id="SomeRule")
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        assert isinstance(doc["runs"][0]["results"][0]["ruleIndex"], int)
        assert doc["runs"][0]["results"][0]["ruleIndex"] >= 0

    def test_sarif_rule_index_matches_rules_array_position(self):
        f1 = _make_finding(rule_id="RuleA")
        f2 = _make_finding(rule_id="RuleB", severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[f1, f2])
        doc = json.loads(format_sarif(scan_result))
        rules = doc["runs"][0]["tool"]["driver"]["rules"]
        rule_id_to_index = {r["id"]: i for i, r in enumerate(rules)}
        for result in doc["runs"][0]["results"]:
            assert result["ruleIndex"] == rule_id_to_index[result["ruleId"]]

    def test_sarif_rules_are_deduplicated(self):
        f1 = _make_finding(rule_id="DupRule")
        f2 = _make_finding(rule_id="DupRule", file_path="other.pmd")
        scan_result = _make_scan_result(findings=[f1, f2])
        doc = json.loads(format_sarif(scan_result))
        rules = doc["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 1

    def test_sarif_rule_severity_escalates_when_advice_precedes_action(self):
        # Same rule_id: ADVICE appears first, ACTION second.
        # The rule descriptor must escalate to 'error', not stay at 'warning'.
        f1 = _make_finding(rule_id="EscalatingRule", severity=Severity.ADVICE, file_path="a.pmd")
        f2 = _make_finding(rule_id="EscalatingRule", severity=Severity.ACTION, file_path="b.pmd")
        scan_result = _make_scan_result(findings=[f1, f2])
        doc = json.loads(format_sarif(scan_result))
        rules = doc["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 1
        assert rules[0]["defaultConfiguration"]["level"] == "error"

    def test_sarif_line_zero_clamped_to_1(self):
        finding = _make_finding(line=0)
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        start_line = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"]
        assert start_line == 1

    def test_sarif_nonzero_line_preserved(self):
        finding = _make_finding(line=42)
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        start_line = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"]
        assert start_line == 42

    def test_sarif_file_path_in_artifact_location(self):
        finding = _make_finding(file_path="src/myapp.pmd")
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        assert uri == "src/myapp.pmd"

    def test_sarif_rule_descriptor_has_required_fields(self):
        finding = _make_finding(rule_id="TestDescriptor")
        scan_result = _make_scan_result(findings=[finding])
        doc = json.loads(format_sarif(scan_result))
        rule = doc["runs"][0]["tool"]["driver"]["rules"][0]
        assert "id" in rule
        assert "name" in rule
        assert "shortDescription" in rule
        assert "defaultConfiguration" in rule
        assert "level" in rule["defaultConfiguration"]

    def test_report_findings_sarif_dispatches_to_format_sarif(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = report_findings(scan_result, ReportFormat.SARIF)
        assert json.loads(result)["version"] == "2.1.0"


class TestFormatSummary:
    def test_contains_repo_name(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = format_summary(scan_result)
        assert "owner/test-repo" in result

    def test_contains_total_findings_count(self):
        f1 = _make_finding()
        f2 = _make_finding(rule_id="Rule2")
        scan_result = _make_scan_result(findings=[f1, f2])
        result = format_summary(scan_result)
        assert "Total findings: 2" in result

    def test_contains_action_count(self):
        f1 = _make_finding(severity=Severity.ACTION)
        f2 = _make_finding(rule_id="R2", severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[f1, f2])
        result = format_summary(scan_result)
        assert "ACTION: 1" in result

    def test_contains_advice_count(self):
        f1 = _make_finding(severity=Severity.ACTION)
        f2 = _make_finding(rule_id="R2", severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[f1, f2])
        result = format_summary(scan_result)
        assert "ADVICE: 1" in result

    def test_contains_rule_id_in_by_rule_section(self):
        finding = _make_finding(rule_id="ScriptConsoleLogRule")
        scan_result = _make_scan_result(findings=[finding])
        result = format_summary(scan_result)
        assert "ScriptConsoleLogRule" in result

    def test_contains_file_path_in_by_file_section(self):
        finding = _make_finding(file_path="src/myPage.pmd")
        scan_result = _make_scan_result(findings=[finding])
        result = format_summary(scan_result)
        assert "src/myPage.pmd" in result

    def test_clean_scan_shows_no_findings_message(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = format_summary(scan_result)
        assert "No findings" in result

    def test_clean_scan_does_not_show_rule_section(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = format_summary(scan_result)
        assert "By Rule:" not in result

    def test_report_findings_summary_dispatches_to_format_summary(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = report_findings(scan_result, ReportFormat.SUMMARY)
        assert "owner/test-repo" in result


class TestFormatGithubIssues:
    def test_creates_one_issue_per_action_finding(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        f1 = _make_finding(rule_id="RuleA", severity=Severity.ACTION, file_path="a.pmd")
        f2 = _make_finding(rule_id="RuleB", severity=Severity.ACTION, file_path="b.pmd")
        scan_result = _make_scan_result(findings=[f1, f2])
        format_github_issues(scan_result, "owner/test-repo", "fake-token")
        assert mock_repo.create_issue.call_count == 2

    def test_groups_all_advice_into_single_issue(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        f1 = _make_finding(rule_id="AdvR1", severity=Severity.ADVICE)
        f2 = _make_finding(rule_id="AdvR2", severity=Severity.ADVICE, file_path="b.pmd")
        scan_result = _make_scan_result(findings=[f1, f2])
        format_github_issues(scan_result, "owner/test-repo", "fake-token")
        assert mock_repo.create_issue.call_count == 1
        call_kwargs = mock_repo.create_issue.call_args[1]
        assert "ADVICE Summary" in call_kwargs["title"]

    def test_returns_list_of_html_urls(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        f = _make_finding(severity=Severity.ACTION)
        scan_result = _make_scan_result(findings=[f])
        result = format_github_issues(scan_result, "owner/test-repo", "fake-token")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "https://github.com/owner/test-repo/issues/1"

    def test_skips_duplicate_action_issue(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        finding = _make_finding(rule_id="DupRule", severity=Severity.ACTION, file_path="x.pmd")
        scan_result = _make_scan_result(findings=[finding])
        existing = MagicMock()
        existing.title = "[Arcane Auditor] DupRule: x.pmd"
        mock_repo.get_issues.return_value = [existing]
        result = format_github_issues(scan_result, "owner/test-repo", "fake-token")
        assert mock_repo.create_issue.call_count == 0
        assert result == []

    def test_skips_duplicate_advice_summary_issue(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        finding = _make_finding(rule_id="AdvR", severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[finding])
        existing = MagicMock()
        existing.title = "[Arcane Auditor] ADVICE Summary"
        mock_repo.get_issues.return_value = [existing]
        format_github_issues(scan_result, "owner/test-repo", "fake-token")
        assert mock_repo.create_issue.call_count == 0

    def test_no_findings_creates_no_issues(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = format_github_issues(scan_result, "owner/test-repo", "fake-token")
        assert mock_repo.create_issue.call_count == 0
        assert result == []

    def test_action_issue_title_format(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        finding = _make_finding(rule_id="ScriptVarUsageRule", severity=Severity.ACTION, file_path="myPage.pmd")
        scan_result = _make_scan_result(findings=[finding])
        format_github_issues(scan_result, "owner/test-repo", "fake-token")
        assert mock_repo.create_issue.call_count == 1
        call_kwargs = mock_repo.create_issue.call_args[1]
        assert call_kwargs["title"] == "[Arcane Auditor] ScriptVarUsageRule: myPage.pmd"

    def test_get_repo_github_exception_raises_reporter_error(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        mock_gh.get_repo.side_effect = GithubException(404, "not found", None)
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        with pytest.raises(ReporterError, match="owner/test-repo"):
            format_github_issues(scan_result, "owner/test-repo", "fake-token")

    def test_create_issue_github_exception_raises_reporter_error(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        mock_repo.create_issue.side_effect = GithubException(422, "error", None)
        finding = _make_finding(severity=Severity.ACTION)
        scan_result = _make_scan_result(findings=[finding])
        with pytest.raises(ReporterError):
            format_github_issues(scan_result, "owner/test-repo", "fake-token")

    def test_action_issue_labels_include_arcane_auditor_and_severity(self, mock_github_ctx):
        mock_cls, mock_gh, mock_repo = mock_github_ctx
        finding = _make_finding(severity=Severity.ACTION)
        scan_result = _make_scan_result(findings=[finding])
        format_github_issues(scan_result, "owner/test-repo", "fake-token")
        call_kwargs = mock_repo.create_issue.call_args[1]
        assert "arcane-auditor" in call_kwargs["labels"]
        assert "arcane-auditor:ACTION" in call_kwargs["labels"]


class TestFormatPrComment:
    def test_posts_single_comment(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")
        assert mock_pr.create_issue_comment.call_count == 1

    def test_returns_comment_html_url(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        result = format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")
        assert result == "https://github.com/owner/test-repo/pull/1#issuecomment-99"

    def test_clean_comment_body_contains_no_findings_message(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")
        body = mock_pr.create_issue_comment.call_args[0][0]
        assert "No findings" in body

    def test_comment_body_contains_action_findings_table(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        finding = _make_finding(rule_id="ScriptConsoleLogRule", severity=Severity.ACTION, file_path="app.pmd", line=5)
        scan_result = _make_scan_result(findings=[finding])
        format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")
        body = mock_pr.create_issue_comment.call_args[0][0]
        assert "ScriptConsoleLogRule" in body
        assert "app.pmd" in body

    def test_comment_body_advice_in_collapsible_details(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        finding = _make_finding(rule_id="AdviceRule", severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[finding])
        format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")
        body = mock_pr.create_issue_comment.call_args[0][0]
        assert "<details>" in body
        assert "<summary>" in body
        assert "AdviceRule" in body

    def test_comment_body_has_blank_line_after_summary_tag(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        finding = _make_finding(severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[finding])
        format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")
        body = mock_pr.create_issue_comment.call_args[0][0]
        assert "</summary>\n\n" in body

    def test_comment_body_contains_findings_count(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        f1 = _make_finding(severity=Severity.ACTION)
        f2 = _make_finding(rule_id="R2", severity=Severity.ADVICE)
        scan_result = _make_scan_result(findings=[f1, f2])
        format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")
        body = mock_pr.create_issue_comment.call_args[0][0]
        assert "2 findings" in body
        assert "ACTION: 1" in body
        assert "ADVICE: 1" in body

    def test_get_repo_github_exception_raises_reporter_error(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        mock_gh.get_repo.side_effect = GithubException(404, "not found", None)
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        with pytest.raises(ReporterError, match="owner/test-repo"):
            format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")

    def test_get_pull_github_exception_raises_reporter_error(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        mock_repo.get_pull.side_effect = GithubException(404, "PR not found", None)
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        with pytest.raises(ReporterError, match="#1"):
            format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")

    def test_create_comment_github_exception_raises_reporter_error(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        mock_pr.create_issue_comment.side_effect = GithubException(500, "server error", None)
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        with pytest.raises(ReporterError, match="#1"):
            format_pr_comment(scan_result, "owner/test-repo", 1, "fake-token")

    def test_get_pull_called_with_pr_number(self, mock_pr_ctx):
        mock_cls, mock_gh, mock_repo, mock_pr = mock_pr_ctx
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        format_pr_comment(scan_result, "owner/test-repo", 42, "fake-token")
        assert mock_repo.get_pull.call_args[0][0] == 42


class TestReportFindingsDispatcher:
    def test_github_issues_format_raises_reporter_error(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        with pytest.raises(ReporterError, match="format_github_issues"):
            report_findings(scan_result, ReportFormat.GITHUB_ISSUES)

    def test_pr_comment_format_raises_reporter_error(self):
        scan_result = _make_scan_result(findings=[], exit_code=ExitCode.CLEAN)
        with pytest.raises(ReporterError, match="format_pr_comment"):
            report_findings(scan_result, ReportFormat.PR_COMMENT)
