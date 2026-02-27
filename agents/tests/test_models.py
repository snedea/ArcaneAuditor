"""Tests for src/models.py -- Pydantic models, enums, and custom exceptions."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models import (
    AgentConfig,
    ArcaneAgentError,
    Confidence,
    ExitCode,
    Finding,
    FixerError,
    FixResult,
    ReportFormat,
    ReporterError,
    RunnerError,
    ScanError,
    ScanResult,
    Severity,
)


# --- Enum tests ---


class TestSeverity:
    def test_severity_values(self) -> None:
        assert Severity.ACTION.value == "ACTION"
        assert Severity.ADVICE.value == "ADVICE"


class TestReportFormat:
    def test_report_format_values(self) -> None:
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.SARIF.value == "sarif"
        assert ReportFormat.GITHUB_ISSUES.value == "github_issues"
        assert ReportFormat.PR_COMMENT.value == "pr_comment"


class TestConfidence:
    def test_confidence_values(self) -> None:
        assert Confidence.HIGH.value == "HIGH"
        assert Confidence.MEDIUM.value == "MEDIUM"
        assert Confidence.LOW.value == "LOW"


class TestExitCode:
    def test_exit_code_values(self) -> None:
        assert ExitCode.CLEAN.value == 0
        assert ExitCode.ISSUES_FOUND.value == 1
        assert ExitCode.USAGE_ERROR.value == 2
        assert ExitCode.RUNTIME_ERROR.value == 3


# --- Finding tests ---


class TestFinding:
    def test_finding_creation(self) -> None:
        f = Finding(
            rule_id="ScriptConsoleLogRule",
            severity=Severity.ACTION,
            message="Console.log statement found in script",
            file_path="myapp.pmd",
            line=42,
        )
        assert f.rule_id == "ScriptConsoleLogRule"
        assert f.severity == Severity.ACTION
        assert f.message == "Console.log statement found in script"
        assert f.file_path == "myapp.pmd"
        assert f.line == 42

    def test_finding_default_line(self) -> None:
        f = Finding(
            rule_id="TestRule",
            severity=Severity.ADVICE,
            message="test message",
            file_path="test.pmd",
        )
        assert f.line == 0

    def test_finding_frozen(self) -> None:
        f = Finding(
            rule_id="TestRule",
            severity=Severity.ACTION,
            message="test",
            file_path="test.pmd",
        )
        with pytest.raises(ValidationError):
            f.rule_id = "Changed"  # type: ignore[misc]

    def test_finding_from_parent_json(self) -> None:
        parent_json = {
            "rule_id": "ScriptConsoleLogRule",
            "severity": "ACTION",
            "message": "Console.log statement found in script",
            "file_path": "myapp.pmd",
            "line": 42,
        }
        f = Finding.model_validate(parent_json)
        assert f.rule_id == "ScriptConsoleLogRule"
        assert f.severity == Severity.ACTION
        assert f.message == "Console.log statement found in script"
        assert f.file_path == "myapp.pmd"
        assert f.line == 42

    def test_finding_invalid_severity(self) -> None:
        with pytest.raises(ValidationError):
            Finding(
                rule_id="TestRule",
                severity="INVALID",  # type: ignore[arg-type]
                message="test",
                file_path="test.pmd",
            )

    def test_finding_description_property(self) -> None:
        f = Finding(
            rule_id="TestRule",
            severity=Severity.ACTION,
            message="the message",
            file_path="test.pmd",
        )
        assert f.description == "the message"


# --- ScanResult tests ---


class TestScanResult:
    def _make_findings(self) -> list[Finding]:
        return [
            Finding(
                rule_id="Rule1",
                severity=Severity.ACTION,
                message="action finding",
                file_path="a.pmd",
                line=1,
            ),
            Finding(
                rule_id="Rule2",
                severity=Severity.ADVICE,
                message="advice finding",
                file_path="b.pmd",
                line=2,
            ),
            Finding(
                rule_id="Rule3",
                severity=Severity.ACTION,
                message="another action",
                file_path="c.pmd",
                line=3,
            ),
        ]

    def test_scan_result_creation(self) -> None:
        findings = self._make_findings()
        sr = ScanResult(
            repo="owner/repo",
            findings_count=3,
            findings=findings,
            exit_code=ExitCode.ISSUES_FOUND,
        )
        assert sr.repo == "owner/repo"
        assert sr.findings_count == 3
        assert len(sr.findings) == 3
        assert sr.exit_code == ExitCode.ISSUES_FOUND

    def test_scan_result_timestamp_default(self) -> None:
        before = datetime.now(UTC)
        sr = ScanResult(
            repo="test/repo",
            findings_count=0,
            findings=[],
            exit_code=ExitCode.CLEAN,
        )
        after = datetime.now(UTC)
        assert isinstance(sr.timestamp, datetime)
        assert before <= sr.timestamp <= after

    def test_scan_result_has_issues_property(self) -> None:
        sr_issues = ScanResult(
            repo="test/repo",
            findings_count=1,
            findings=[],
            exit_code=ExitCode.ISSUES_FOUND,
        )
        assert sr_issues.has_issues is True

        sr_clean = ScanResult(
            repo="test/repo",
            findings_count=0,
            findings=[],
            exit_code=ExitCode.CLEAN,
        )
        assert sr_clean.has_issues is False

    def test_scan_result_action_advice_counts(self) -> None:
        findings = self._make_findings()
        sr = ScanResult(
            repo="test/repo",
            findings_count=3,
            findings=findings,
            exit_code=ExitCode.ISSUES_FOUND,
        )
        assert sr.action_count == 2
        assert sr.advice_count == 1


# --- FixResult tests ---


class TestFixResult:
    def _make_finding(self) -> Finding:
        return Finding(
            rule_id="TestRule",
            severity=Severity.ACTION,
            message="test finding",
            file_path="test.pmd",
            line=10,
        )

    def test_fix_result_creation(self) -> None:
        finding = self._make_finding()
        fr = FixResult(
            finding=finding,
            original_content="console.log('bad');",
            fixed_content="// removed console.log",
            confidence=Confidence.HIGH,
        )
        assert fr.finding == finding
        assert fr.original_content == "console.log('bad');"
        assert fr.fixed_content == "// removed console.log"
        assert fr.confidence == Confidence.HIGH

    def test_fix_result_is_auto_applicable(self) -> None:
        finding = self._make_finding()
        for confidence, expected in [
            (Confidence.HIGH, True),
            (Confidence.MEDIUM, False),
            (Confidence.LOW, False),
        ]:
            fr = FixResult(
                finding=finding,
                original_content="old",
                fixed_content="new",
                confidence=confidence,
            )
            assert fr.is_auto_applicable is expected


# --- AgentConfig tests ---


class TestAgentConfig:
    def test_agent_config_defaults(self) -> None:
        cfg = AgentConfig()
        assert cfg.repos == []
        assert cfg.config_preset is None
        assert cfg.output_format == ReportFormat.JSON
        assert cfg.github_token is None

    def test_agent_config_with_token(self) -> None:
        cfg = AgentConfig(github_token="ghp_test123")  # type: ignore[arg-type]
        assert cfg.github_token is not None
        assert cfg.github_token.get_secret_value() == "ghp_test123"
        # SecretStr masks the value in string representation
        assert "ghp_test123" not in str(cfg.github_token)

    def test_agent_config_auditor_path(self) -> None:
        cfg = AgentConfig(auditor_path=Path("/custom/path"))
        assert cfg.auditor_path == Path("/custom/path")


# --- Exception tests ---


class TestExceptions:
    def test_exceptions_inherit_from_base(self) -> None:
        assert issubclass(ScanError, ArcaneAgentError)
        assert issubclass(RunnerError, ArcaneAgentError)
        assert issubclass(ReporterError, ArcaneAgentError)
        assert issubclass(FixerError, ArcaneAgentError)

    def test_exceptions_inherit_from_exception(self) -> None:
        assert issubclass(ArcaneAgentError, Exception)

    def test_exception_messages(self) -> None:
        for exc_class in [ScanError, RunnerError, ReporterError, FixerError]:
            msg = f"{exc_class.__name__} occurred"
            with pytest.raises(exc_class, match=msg):
                raise exc_class(msg)

    def test_catch_all_base_exception(self) -> None:
        with pytest.raises(ArcaneAgentError):
            raise ScanError("should be caught by base")
