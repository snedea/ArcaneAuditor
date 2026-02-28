from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import AgentConfig, ExitCode, RunnerError, ScanManifest, ScanResult, Severity
from src.runner import run_audit

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
CLEAN_APP_FIXTURE: Path = FIXTURES_DIR / "clean_app"
DIRTY_APP_FIXTURE: Path = FIXTURES_DIR / "dirty_app"
AUDITOR_PATH: Path = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def clean_config() -> AgentConfig:
    """AgentConfig pointing at the real parent Arcane Auditor tool."""
    return AgentConfig(auditor_path=AUDITOR_PATH)


@pytest.fixture(scope="module")
def clean_result(clean_config: AgentConfig) -> ScanResult:
    """Run real parent tool against clean_app fixture once per module."""
    manifest = ScanManifest(root_path=CLEAN_APP_FIXTURE)
    return run_audit(manifest, clean_config)


@pytest.fixture(scope="module")
def dirty_result(clean_config: AgentConfig) -> ScanResult:
    """Run real parent tool against dirty_app fixture once per module."""
    manifest = ScanManifest(root_path=DIRTY_APP_FIXTURE)
    return run_audit(manifest, clean_config)


class TestRunAuditCleanApp:

    def test_returns_scan_result_instance(self, clean_result: ScanResult) -> None:
        assert isinstance(clean_result, ScanResult)

    def test_exit_code_is_clean(self, clean_result: ScanResult) -> None:
        assert clean_result.exit_code == ExitCode.CLEAN

    def test_findings_count_is_zero(self, clean_result: ScanResult) -> None:
        assert clean_result.findings_count == 0

    def test_findings_list_is_empty(self, clean_result: ScanResult) -> None:
        assert clean_result.findings == []

    def test_has_issues_is_false(self, clean_result: ScanResult) -> None:
        assert clean_result.has_issues is False

    def test_repo_field_matches_path(self, clean_result: ScanResult) -> None:
        assert str(CLEAN_APP_FIXTURE) in clean_result.repo


class TestRunAuditDirtyApp:

    def test_returns_scan_result_instance(self, dirty_result: ScanResult) -> None:
        assert isinstance(dirty_result, ScanResult)

    def test_exit_code_is_issues_found(self, dirty_result: ScanResult) -> None:
        assert dirty_result.exit_code == ExitCode.ISSUES_FOUND

    def test_has_issues_is_true(self, dirty_result: ScanResult) -> None:
        assert dirty_result.has_issues is True

    def test_findings_count_matches_findings_list_length(self, dirty_result: ScanResult) -> None:
        assert dirty_result.findings_count == len(dirty_result.findings)

    def test_findings_count_is_nine(self, dirty_result: ScanResult) -> None:
        assert dirty_result.findings_count == 9

    def test_contains_endpoint_fail_on_status_codes_finding(self, dirty_result: ScanResult) -> None:
        matches = [f for f in dirty_result.findings if f.rule_id == "EndpointFailOnStatusCodesRule"]
        assert len(matches) == 1
        assert matches[0].severity == Severity.ACTION
        assert matches[0].file_path == "dirtyPod.pod"

    def test_contains_hardcoded_workday_api_finding(self, dirty_result: ScanResult) -> None:
        matches = [f for f in dirty_result.findings if f.rule_id == "HardcodedWorkdayAPIRule"]
        assert len(matches) == 1
        assert matches[0].severity == Severity.ACTION
        assert matches[0].file_path == "dirtyPod.pod"

    def test_contains_widget_id_required_finding(self, dirty_result: ScanResult) -> None:
        matches = [f for f in dirty_result.findings if f.rule_id == "WidgetIdRequiredRule"]
        assert len(matches) == 1
        assert matches[0].severity == Severity.ACTION
        assert matches[0].file_path == "dirtyPage.pmd"

    def test_action_findings_count_is_three(self, dirty_result: ScanResult) -> None:
        assert dirty_result.action_count == 3

    def test_advice_findings_count_is_six(self, dirty_result: ScanResult) -> None:
        assert dirty_result.advice_count == 6

    def test_var_usage_findings_in_correct_files(self, dirty_result: ScanResult) -> None:
        matches = [f for f in dirty_result.findings if f.rule_id == "ScriptVarUsageRule"]
        assert len(matches) == 2
        file_paths = {f.file_path for f in matches}
        assert "dirtyPage.pmd" in file_paths
        assert "helpers.script" in file_paths

    def test_string_concat_finding_in_dirty_page(self, dirty_result: ScanResult) -> None:
        matches = [f for f in dirty_result.findings if f.rule_id == "ScriptStringConcatRule"]
        assert len(matches) == 1
        assert matches[0].severity == Severity.ADVICE
        assert matches[0].file_path == "dirtyPage.pmd"


class TestRunAuditTimeout:

    def test_timeout_raises_runner_error(self) -> None:
        manifest = ScanManifest(root_path=CLEAN_APP_FIXTURE)
        config = AgentConfig(auditor_path=AUDITOR_PATH)
        with patch("src.runner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="uv", timeout=300)
            with pytest.raises(RunnerError, match="timed out"):
                run_audit(manifest, config)

    def test_timeout_error_message_includes_path(self) -> None:
        manifest = ScanManifest(root_path=CLEAN_APP_FIXTURE)
        config = AgentConfig(auditor_path=AUDITOR_PATH)
        with patch("src.runner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="uv", timeout=300)
            with pytest.raises(RunnerError) as exc_info:
                run_audit(manifest, config)
            assert str(CLEAN_APP_FIXTURE) in str(exc_info.value)


class TestRunAuditInvalidPath:

    def test_exit_code_2_raises_runner_error(self) -> None:
        manifest = ScanManifest(root_path=Path("/nonexistent/fake/path"))
        config = AgentConfig(auditor_path=AUDITOR_PATH)
        with patch("src.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=2, stdout="Error: path not found", stderr="")
            with pytest.raises(RunnerError, match="usage error"):
                run_audit(manifest, config)

    def test_exit_code_2_error_message_includes_path(self) -> None:
        manifest = ScanManifest(root_path=Path("/nonexistent/fake/path"))
        config = AgentConfig(auditor_path=AUDITOR_PATH)
        with patch("src.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=2, stdout="Error: path not found", stderr="")
            with pytest.raises(RunnerError) as exc_info:
                run_audit(manifest, config)
            assert "/nonexistent/fake/path" in str(exc_info.value)

    def test_exit_code_2_with_stderr_message(self) -> None:
        manifest = ScanManifest(root_path=Path("/nonexistent/fake/path"))
        config = AgentConfig(auditor_path=AUDITOR_PATH)
        with patch("src.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="usage: main.py [OPTIONS]")
            with pytest.raises(RunnerError) as exc_info:
                run_audit(manifest, config)
            assert "usage: main.py [OPTIONS]" in str(exc_info.value)
