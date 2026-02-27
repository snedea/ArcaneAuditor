"""Tests for src/cli module -- argument validation, pipeline wiring, exit codes."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.models import AgentConfig, ExitCode, ScanManifest, ScanResult

runner = CliRunner()


def _make_config(tmp_path: Path) -> AgentConfig:
    """Return an AgentConfig whose auditor_path points to a temp stub."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")
    return AgentConfig(auditor_path=auditor_dir)


def _make_scan_result(exit_code: ExitCode = ExitCode.CLEAN) -> ScanResult:
    """Return a minimal ScanResult for use in mocked pipelines."""
    return ScanResult(
        repo="test/repo",
        timestamp=datetime.now(UTC),
        findings_count=0,
        findings=[],
        exit_code=exit_code,
    )


def _make_manifest(tmp_path: Path) -> ScanManifest:
    """Return a minimal ScanManifest for use in mocked pipelines."""
    return ScanManifest(root_path=tmp_path)


# ---------------------------------------------------------------------------
# Argument validation -- mutual exclusion and dependency checks
# ---------------------------------------------------------------------------


class TestArgumentValidation:

    def test_no_path_no_repo_exits_2(self, tmp_path: Path) -> None:
        """Omitting both PATH and --repo exits with code 2 (USAGE_ERROR)."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [])
        assert result.exit_code == 2

    def test_no_path_no_repo_prints_error(self, tmp_path: Path) -> None:
        """Error message is emitted when neither PATH nor --repo is given."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [])
        assert "Must specify either PATH or --repo" in result.output

    def test_path_and_repo_together_exits_2(self, tmp_path: Path) -> None:
        """Providing both PATH and --repo exits with code 2 (USAGE_ERROR)."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [str(tmp_path), "--repo", "owner/repo"])
        assert result.exit_code == 2

    def test_path_and_repo_together_prints_error(self, tmp_path: Path) -> None:
        """Error message is emitted when both PATH and --repo are supplied."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [str(tmp_path), "--repo", "owner/repo"])
        assert "Cannot specify both PATH and --repo" in result.output

    def test_pr_without_repo_exits_2(self, tmp_path: Path) -> None:
        """--pr without --repo exits with code 2 (USAGE_ERROR)."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [str(tmp_path), "--pr", "42"])
        assert result.exit_code == 2

    def test_pr_without_repo_prints_error(self, tmp_path: Path) -> None:
        """Error message is emitted when --pr is given without --repo."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [str(tmp_path), "--pr", "42"])
        assert "--pr requires --repo" in result.output

    def test_github_issues_format_without_repo_exits_2(self, tmp_path: Path) -> None:
        """--format github-issues without --repo exits with code 2."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [str(tmp_path), "--format", "github-issues"])
        assert result.exit_code == 2

    def test_pr_comment_format_without_repo_exits_2(self, tmp_path: Path) -> None:
        """--format pr-comment without --repo exits with code 2."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, [str(tmp_path), "--format", "pr-comment"])
        assert result.exit_code == 2

    def test_pr_comment_format_without_pr_exits_2(self, tmp_path: Path) -> None:
        """--format pr-comment with --repo but without --pr exits with code 2."""
        config = _make_config(tmp_path)
        with patch("src.cli.load_config", return_value=config):
            result = runner.invoke(
                app, ["--repo", "owner/repo", "--format", "pr-comment"]
            )
        assert result.exit_code == 2

    def test_pr_comment_format_without_pr_prints_error(self, tmp_path: Path) -> None:
        """Error message is emitted for pr-comment without --pr."""
        config = _make_config(tmp_path)
        with patch("src.cli.load_config", return_value=config):
            result = runner.invoke(
                app, ["--repo", "owner/repo", "--format", "pr-comment"]
            )
        assert "--format pr-comment requires --pr" in result.output

    def test_github_issues_without_token_exits_2(self, tmp_path: Path) -> None:
        """--format github-issues with --repo but no GITHUB_TOKEN exits with code 2."""
        config = _make_config(tmp_path)  # github_token is None by default
        with patch("src.cli.load_config", return_value=config):
            result = runner.invoke(
                app, ["--repo", "owner/repo", "--format", "github-issues"]
            )
        assert result.exit_code == 2

    def test_github_issues_without_token_prints_error(self, tmp_path: Path) -> None:
        """Token-required error message is emitted when token is absent."""
        config = _make_config(tmp_path)
        with patch("src.cli.load_config", return_value=config):
            result = runner.invoke(
                app, ["--repo", "owner/repo", "--format", "github-issues"]
            )
        assert "GITHUB_TOKEN" in result.output


# ---------------------------------------------------------------------------
# Config error handling
# ---------------------------------------------------------------------------


class TestConfigError:

    def test_config_error_exits_2(self) -> None:
        """ConfigError raised by load_config() exits with code 2."""
        from src.models import ConfigError

        with patch("src.cli.load_config", side_effect=ConfigError("bad config")):
            result = runner.invoke(app, ["--repo", "owner/repo"])
        assert result.exit_code == 2

    def test_config_error_message_emitted(self) -> None:
        """ConfigError message appears in output."""
        from src.models import ConfigError

        with patch("src.cli.load_config", side_effect=ConfigError("bad config")):
            result = runner.invoke(app, ["--repo", "owner/repo"])
        assert "bad config" in result.output


# ---------------------------------------------------------------------------
# Pipeline wiring -- local path scan
# ---------------------------------------------------------------------------


class TestPipelineLocalPath:

    def test_scan_local_called_with_path(self, tmp_path: Path) -> None:
        """scan_local() is invoked with the supplied PATH argument."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest) as mock_scan,
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", return_value="{}"),
        ):
            runner.invoke(app, [str(tmp_path)])

        mock_scan.assert_called_once_with(tmp_path)

    def test_run_audit_called_with_manifest_and_config(self, tmp_path: Path) -> None:
        """run_audit() is invoked with the manifest returned by scan_local."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result) as mock_audit,
            patch("src.cli.report_findings", return_value="{}"),
        ):
            runner.invoke(app, [str(tmp_path)])

        mock_audit.assert_called_once_with(manifest, config)

    def test_report_findings_called_for_json_format(self, tmp_path: Path) -> None:
        """report_findings() is called when --format json (default)."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", return_value="{}") as mock_report,
        ):
            runner.invoke(app, [str(tmp_path)])

        mock_report.assert_called_once()

    def test_output_written_to_file(self, tmp_path: Path) -> None:
        """--output writes formatted content to the given file path."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()
        out_file = tmp_path / "out.json"

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", return_value='{"findings": []}'),
        ):
            runner.invoke(app, [str(tmp_path), "--output", str(out_file)])

        assert out_file.exists()
        assert out_file.read_text(encoding="utf-8") == '{"findings": []}'


# ---------------------------------------------------------------------------
# Exit code propagation
# ---------------------------------------------------------------------------


class TestExitCodePropagation:

    def test_exit_code_clean_is_0(self, tmp_path: Path) -> None:
        """scan_result.exit_code == CLEAN propagates as exit code 0."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", return_value="{}"),
        ):
            result = runner.invoke(app, [str(tmp_path)])

        assert result.exit_code == 0

    def test_exit_code_issues_found_is_1(self, tmp_path: Path) -> None:
        """scan_result.exit_code == ISSUES_FOUND propagates as exit code 1."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", return_value="{}"),
        ):
            result = runner.invoke(app, [str(tmp_path)])

        assert result.exit_code == 1

    def test_scan_error_exits_2(self, tmp_path: Path) -> None:
        """ScanError raised by scan_local() exits with code 2."""
        from src.models import ScanError

        config = _make_config(tmp_path)

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", side_effect=ScanError("not found")),
        ):
            result = runner.invoke(app, [str(tmp_path)])

        assert result.exit_code == 2

    def test_runner_error_exits_3(self, tmp_path: Path) -> None:
        """RunnerError raised by run_audit() exits with code 3."""
        from src.models import RunnerError

        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", side_effect=RunnerError("crash")),
        ):
            result = runner.invoke(app, [str(tmp_path)])

        assert result.exit_code == 3

    def test_reporter_error_exits_3(self, tmp_path: Path) -> None:
        """ReporterError raised by report_findings() exits with code 3."""
        from src.models import ReporterError

        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", side_effect=ReporterError("fmt err")),
        ):
            result = runner.invoke(app, [str(tmp_path)])

        assert result.exit_code == 3


# ---------------------------------------------------------------------------
# Quiet flag
# ---------------------------------------------------------------------------


class TestQuietFlag:

    def test_quiet_suppresses_output_written_message(self, tmp_path: Path) -> None:
        """--quiet suppresses 'Output written to' info message."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()
        out_file = tmp_path / "out.json"

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", return_value="{}"),
        ):
            result = runner.invoke(
                app, [str(tmp_path), "--output", str(out_file), "--quiet"]
            )

        assert "Output written to" not in result.output

    def test_without_quiet_output_written_message_present(self, tmp_path: Path) -> None:
        """Without --quiet, 'Output written to' message is emitted."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()
        out_file = tmp_path / "out.json"

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result),
            patch("src.cli.report_findings", return_value="{}"),
        ):
            result = runner.invoke(
                app, [str(tmp_path), "--output", str(out_file)]
            )

        assert "Output written to" in result.output


# ---------------------------------------------------------------------------
# --config preset propagation
# ---------------------------------------------------------------------------


class TestConfigPreset:

    def test_config_preset_applied_to_agent_config(self, tmp_path: Path) -> None:
        """--config preset name is stored in agent_config.config_preset passed to run_audit."""
        config = _make_config(tmp_path)
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result()

        with (
            patch("src.cli.load_config", return_value=config),
            patch("src.cli.scan_local", return_value=manifest),
            patch("src.cli.run_audit", return_value=scan_result) as mock_audit,
            patch("src.cli.report_findings", return_value="{}"),
        ):
            runner.invoke(app, [str(tmp_path), "--config", "production-ready"])

        called_config: AgentConfig = mock_audit.call_args[0][1]
        assert called_config.config_preset == "production-ready"
