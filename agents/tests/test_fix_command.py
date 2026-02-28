"""Tests for the fix command in src/cli module."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from github import GithubException
from typer.testing import CliRunner

from src.cli import _create_fix_pr, app
from src.models import (
    AgentConfig,
    ExitCode,
    Finding,
    FixerError,
    FixResult,
    Confidence,
    ScanManifest,
    ScanResult,
    Severity,
)

runner = CliRunner()


def _make_config(tmp_path: Path) -> AgentConfig:
    """Return an AgentConfig whose auditor_path points to a temp stub."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")
    return AgentConfig(auditor_path=auditor_dir)


def _make_manifest(tmp_path: Path) -> ScanManifest:
    """Return a minimal ScanManifest for use in mocked pipelines."""
    return ScanManifest(root_path=tmp_path)


def _make_scan_result(exit_code: ExitCode = ExitCode.ISSUES_FOUND) -> ScanResult:
    """Return a ScanResult with one finding (default: ISSUES_FOUND)."""
    return ScanResult(
        repo="test/repo",
        timestamp=datetime.now(UTC),
        findings_count=1,
        findings=[
            Finding(
                rule_id="ScriptVarUsageRule",
                severity=Severity.ACTION,
                message="Use let/const",
                file_path="app/test.script",
                line=1,
            )
        ],
        exit_code=exit_code,
    )


def _make_fix_results() -> list[FixResult]:
    """Return a single FixResult for the standard test finding."""
    return [
        FixResult(
            finding=Finding(
                rule_id="ScriptVarUsageRule",
                severity=Severity.ACTION,
                message="Use let/const",
                file_path="app/test.script",
                line=1,
            ),
            original_content="var x = 1;",
            fixed_content="let x = 1;",
            confidence=Confidence.HIGH,
        )
    ]


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestFixArgumentValidation:

    def test_no_path_no_repo_exits_2(self, tmp_path: Path) -> None:
        """Omitting both PATH and --repo exits with code 2."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, ["fix"])
        assert result.exit_code == 2
        assert "Must specify either PATH or --repo" in result.output

    def test_path_and_repo_together_exits_2(self, tmp_path: Path) -> None:
        """Providing both PATH and --repo exits with code 2."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, ["fix", str(tmp_path), "--repo", "owner/repo"])
        assert result.exit_code == 2
        assert "Cannot specify both PATH and --repo" in result.output

    def test_create_pr_without_repo_exits_2(self, tmp_path: Path) -> None:
        """--create-pr without --repo exits with code 2."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, ["fix", str(tmp_path), "--create-pr"])
        assert result.exit_code == 2
        assert "--create-pr requires --repo" in result.output

    def test_create_pr_without_token_exits_2(self, tmp_path: Path) -> None:
        """--create-pr with --repo but no token exits with code 2."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, ["fix", "--repo", "owner/repo", "--create-pr"])
        assert result.exit_code == 2
        assert "GITHUB_TOKEN" in result.output

    def test_target_dir_and_create_pr_exits_2(self, tmp_path: Path) -> None:
        """--target-dir and --create-pr together exits with code 2."""
        auditor_dir = tmp_path / "auditor"
        auditor_dir.mkdir()
        (auditor_dir / "main.py").write_text("# stub")
        config = AgentConfig(auditor_path=auditor_dir, github_token="fake-token")
        with patch("src.cli.load_config", return_value=config):
            result = runner.invoke(app, ["fix", "--repo", "owner/repo", "--target-dir", str(tmp_path), "--create-pr"])
        assert result.exit_code == 2
        assert "Cannot specify both --target-dir and --create-pr" in result.output

    def test_repo_without_create_pr_and_target_dir_exits_2(self, tmp_path: Path) -> None:
        """--repo without --create-pr and without --target-dir exits with code 2 (fixes would be lost)."""
        with patch("src.cli.load_config", return_value=_make_config(tmp_path)):
            result = runner.invoke(app, ["fix", "--repo", "owner/repo"])
        assert result.exit_code == 2
        assert "--repo requires --create-pr or --target-dir" in result.output


# ---------------------------------------------------------------------------
# Pipeline -- local path
# ---------------------------------------------------------------------------


class TestFixPipelineLocal:

    def test_clean_scan_exits_0(self, tmp_path: Path) -> None:
        """Clean scan exits with code 0."""
        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", return_value=_make_manifest(tmp_path)),
            patch("src.cli.run_audit", return_value=_make_scan_result(ExitCode.CLEAN)),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert result.exit_code == 0

    def test_clean_scan_prints_no_findings(self, tmp_path: Path) -> None:
        """Clean scan prints 'No findings to fix'."""
        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", return_value=_make_manifest(tmp_path)),
            patch("src.cli.run_audit", return_value=_make_scan_result(ExitCode.CLEAN)),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert "No findings to fix" in result.output

    def test_fix_findings_called_when_issues_found(self, tmp_path: Path) -> None:
        """fix_findings is called with scan_result and root_path."""
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)
        reaudit_manifest = _make_manifest(tmp_path)

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=[manifest, reaudit_manifest]),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=_make_fix_results()) as mock_fix,
            patch("src.cli.apply_fixes", return_value=[Path("app/test.script")]),
        ):
            runner.invoke(app, ["fix", str(tmp_path)])

        mock_fix.assert_called_once_with(scan_result, tmp_path)

    def test_no_fixable_findings_prints_message(self, tmp_path: Path) -> None:
        """Empty fix results prints 'No auto-fixable findings' and exits 1."""
        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", return_value=_make_manifest(tmp_path)),
            patch("src.cli.run_audit", return_value=_make_scan_result(ExitCode.ISSUES_FOUND)),
            patch("src.cli.fix_findings", return_value=[]),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert "No auto-fixable findings" in result.output
        assert result.exit_code == 1

    def test_apply_fixes_called_with_target_dir(self, tmp_path: Path) -> None:
        """apply_fixes is called with target_dir when --target-dir is given."""
        target = tmp_path / "output"
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        fix_results = _make_fix_results()
        reaudit_manifest = _make_manifest(target)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=[manifest, reaudit_manifest]),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=fix_results),
            patch("src.cli.apply_fixes", return_value=[Path("app/test.script")]) as mock_apply,
        ):
            runner.invoke(app, ["fix", str(tmp_path), "--target-dir", str(target)])

        mock_apply.assert_called_once_with(fix_results, target)

    def test_apply_fixes_called_with_source_dir_when_no_target(self, tmp_path: Path) -> None:
        """apply_fixes is called with manifest.root_path when no --target-dir."""
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        fix_results = _make_fix_results()
        reaudit_manifest = _make_manifest(tmp_path)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=[manifest, reaudit_manifest]),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=fix_results),
            patch("src.cli.apply_fixes", return_value=[Path("app/test.script")]) as mock_apply,
        ):
            runner.invoke(app, ["fix", str(tmp_path)])

        mock_apply.assert_called_once_with(fix_results, tmp_path)

    def test_reaudit_runs_after_fix(self, tmp_path: Path) -> None:
        """run_audit is called exactly 2 times (initial + re-audit)."""
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        reaudit_manifest = _make_manifest(tmp_path)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=[manifest, reaudit_manifest]),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]) as mock_audit,
            patch("src.cli.fix_findings", return_value=_make_fix_results()),
            patch("src.cli.apply_fixes", return_value=[Path("app/test.script")]),
        ):
            runner.invoke(app, ["fix", str(tmp_path)])

        assert mock_audit.call_count == 2


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------


class TestFixExitCodes:

    def test_reaudit_clean_exits_0(self, tmp_path: Path) -> None:
        """Re-audit returning CLEAN exits with code 0."""
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        reaudit_manifest = _make_manifest(tmp_path)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=[manifest, reaudit_manifest]),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=_make_fix_results()),
            patch("src.cli.apply_fixes", return_value=[Path("app/test.script")]),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert result.exit_code == 0

    def test_reaudit_still_issues_exits_1(self, tmp_path: Path) -> None:
        """Re-audit returning ISSUES_FOUND exits with code 1."""
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        reaudit_manifest = _make_manifest(tmp_path)
        reaudit_result = _make_scan_result(ExitCode.ISSUES_FOUND)

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=[manifest, reaudit_manifest]),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=_make_fix_results()),
            patch("src.cli.apply_fixes", return_value=[Path("app/test.script")]),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert result.exit_code == 1

    def test_scan_error_exits_2(self, tmp_path: Path) -> None:
        """ScanError from scan_local exits with code 2."""
        from src.models import ScanError

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=ScanError("not found")),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert result.exit_code == 2

    def test_runner_error_exits_3(self, tmp_path: Path) -> None:
        """RunnerError from run_audit exits with code 3."""
        from src.models import RunnerError

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", return_value=_make_manifest(tmp_path)),
            patch("src.cli.run_audit", side_effect=RunnerError("crash")),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert result.exit_code == 3

    def test_fixer_error_exits_3(self, tmp_path: Path) -> None:
        """FixerError from fix_findings exits with code 3."""
        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", return_value=_make_manifest(tmp_path)),
            patch("src.cli.run_audit", return_value=_make_scan_result(ExitCode.ISSUES_FOUND)),
            patch("src.cli.fix_findings", side_effect=FixerError("write fail")),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path)])
        assert result.exit_code == 3


# ---------------------------------------------------------------------------
# Quiet flag
# ---------------------------------------------------------------------------


class TestFixQuietFlag:

    def test_quiet_suppresses_info_messages(self, tmp_path: Path) -> None:
        """--quiet suppresses Applied and Re-audit messages."""
        manifest = _make_manifest(tmp_path)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        reaudit_manifest = _make_manifest(tmp_path)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=_make_config(tmp_path)),
            patch("src.cli.scan_local", side_effect=[manifest, reaudit_manifest]),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=_make_fix_results()),
            patch("src.cli.apply_fixes", return_value=[Path("app/test.script")]),
        ):
            result = runner.invoke(app, ["fix", str(tmp_path), "--quiet"])
        assert "Applied" not in result.output
        assert "Re-audit" not in result.output


# ---------------------------------------------------------------------------
# --create-pr CLI path (lines 364-371)
# ---------------------------------------------------------------------------


def _make_config_with_token(tmp_path: Path) -> AgentConfig:
    """Return an AgentConfig with a fake GitHub token."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir(exist_ok=True)
    (auditor_dir / "main.py").write_text("# stub")
    return AgentConfig(auditor_path=auditor_dir, github_token="fake-token")


class TestFixCreatePr:
    """CLI-level tests for the --create-pr path (cli.py:364-371)."""

    def test_create_pr_happy_path_echoes_url(self, tmp_path: Path) -> None:
        """--create-pr path echoes the PR URL and exits 0 on success."""
        clone_dir = tmp_path / "clone"
        clone_dir.mkdir()
        manifest = ScanManifest(root_path=clone_dir, temp_dir=clone_dir)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        reaudit_manifest = _make_manifest(clone_dir)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=_make_config_with_token(tmp_path)),
            patch("src.cli.scan_github", return_value=manifest),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=_make_fix_results()),
            patch("src.cli.apply_fixes", return_value=[clone_dir / "app/test.script"]),
            patch("src.cli.scan_local", return_value=reaudit_manifest),
            patch("src.cli._create_fix_pr", return_value="https://github.com/owner/repo/pull/1"),
        ):
            result = runner.invoke(app, ["fix", "--repo", "owner/repo", "--create-pr"])

        assert result.exit_code == 0
        assert "https://github.com/owner/repo/pull/1" in result.output

    def test_create_pr_fixer_error_exits_3(self, tmp_path: Path) -> None:
        """FixerError from _create_fix_pr exits with code 3 and prints error."""
        clone_dir = tmp_path / "clone"
        clone_dir.mkdir()
        manifest = ScanManifest(root_path=clone_dir, temp_dir=clone_dir)
        scan_result = _make_scan_result(ExitCode.ISSUES_FOUND)
        reaudit_manifest = _make_manifest(clone_dir)
        reaudit_result = _make_scan_result(ExitCode.CLEAN)

        with (
            patch("src.cli.load_config", return_value=_make_config_with_token(tmp_path)),
            patch("src.cli.scan_github", return_value=manifest),
            patch("src.cli.run_audit", side_effect=[scan_result, reaudit_result]),
            patch("src.cli.fix_findings", return_value=_make_fix_results()),
            patch("src.cli.apply_fixes", return_value=[clone_dir / "app/test.script"]),
            patch("src.cli.scan_local", return_value=reaudit_manifest),
            patch("src.cli._create_fix_pr", side_effect=FixerError("git push failed: auth error")),
        ):
            result = runner.invoke(app, ["fix", "--repo", "owner/repo", "--create-pr"])

        assert result.exit_code == 3
        assert "git push failed" in result.output

    def test_create_pr_with_target_dir_uses_target(self, tmp_path: Path) -> None:
        """--create-pr is mutually exclusive with --target-dir; this just confirms the guard fires."""
        with patch("src.cli.load_config", return_value=_make_config_with_token(tmp_path)):
            result = runner.invoke(
                app, ["fix", "--repo", "owner/repo", "--target-dir", str(tmp_path), "--create-pr"]
            )
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# _create_fix_pr unit tests (subprocess + GitHub API)
# ---------------------------------------------------------------------------


class TestCreateFixPrFunction:
    """Unit tests for _create_fix_pr covering each subprocess and GitHub API failure branch."""

    def _success(self) -> MagicMock:
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        return m

    def _failure(self, stderr: str = "error") -> MagicMock:
        m = MagicMock()
        m.returncode = 1
        m.stderr = stderr
        return m

    def _github_mock(self, pr_url: str = "https://github.com/owner/repo/pull/42") -> MagicMock:
        mock_pr = MagicMock()
        mock_pr.html_url = pr_url
        mock_repo = MagicMock()
        mock_repo.default_branch = "main"
        mock_repo.create_pull.return_value = mock_pr
        mock_gh = MagicMock()
        mock_gh.__enter__.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo
        return mock_gh

    def test_happy_path_returns_pr_url(self, tmp_path: Path) -> None:
        """All git commands succeed and PR is created; function returns PR HTML URL."""
        scan_result = _make_scan_result()
        mock_gh = self._github_mock()

        with (
            patch("src.cli.subprocess.run", return_value=self._success()),
            patch("src.cli.Github", return_value=mock_gh),
        ):
            url = _create_fix_pr("owner/repo", "tok", tmp_path, [tmp_path / "f.pmd"], scan_result, False)

        assert url == "https://github.com/owner/repo/pull/42"

    def test_git_checkout_failure_raises_fixer_error(self, tmp_path: Path) -> None:
        """git checkout -b failure raises FixerError with descriptive message."""
        with patch("src.cli.subprocess.run", return_value=self._failure("already exists")):
            with pytest.raises(FixerError, match="git checkout -b failed"):
                _create_fix_pr("owner/repo", "tok", tmp_path, [], _make_scan_result(), False)

    def test_git_add_failure_raises_fixer_error(self, tmp_path: Path) -> None:
        """git add failure raises FixerError."""
        with patch("src.cli.subprocess.run", side_effect=[self._success(), self._failure("path error")]):
            with pytest.raises(FixerError, match="git add failed"):
                _create_fix_pr("owner/repo", "tok", tmp_path, [], _make_scan_result(), False)

    def test_git_commit_failure_raises_fixer_error(self, tmp_path: Path) -> None:
        """git commit failure raises FixerError."""
        success = self._success()
        with patch("src.cli.subprocess.run", side_effect=[success, success, self._failure("nothing to commit")]):
            with pytest.raises(FixerError, match="git commit failed"):
                _create_fix_pr("owner/repo", "tok", tmp_path, [], _make_scan_result(), False)

    def test_git_push_failure_raises_fixer_error(self, tmp_path: Path) -> None:
        """git push failure raises FixerError; GIT_ASKPASS temp file is still cleaned up."""
        success = self._success()
        with patch("src.cli.subprocess.run", side_effect=[success, success, success, self._failure("auth error")]):
            with pytest.raises(FixerError, match="git push failed"):
                _create_fix_pr("owner/repo", "tok", tmp_path, [], _make_scan_result(), False)

    def test_github_api_error_raises_fixer_error(self, tmp_path: Path) -> None:
        """GithubException from create_pull is wrapped and re-raised as FixerError."""
        mock_repo = MagicMock()
        mock_repo.create_pull.side_effect = GithubException(422, "base not found", None)
        mock_gh = MagicMock()
        mock_gh.__enter__.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo

        with (
            patch("src.cli.subprocess.run", return_value=self._success()),
            patch("src.cli.Github", return_value=mock_gh),
        ):
            with pytest.raises(FixerError, match="GitHub API error"):
                _create_fix_pr("owner/repo", "tok", tmp_path, [], _make_scan_result(), False)
