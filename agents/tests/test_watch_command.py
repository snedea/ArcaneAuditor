from __future__ import annotations

import signal
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli import _list_open_prs, _load_watch_state, _process_single_pr, _save_watch_state, app
from src.models import (
    AgentConfig,
    ExitCode,
    Finding,
    RunnerError,
    ScanError,
    ScanManifest,
    ScanResult,
    Severity,
    WatchError,
    WatchState,
)

runner = CliRunner()


def _make_config(tmp_path: Path) -> AgentConfig:
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")
    return AgentConfig(auditor_path=auditor_dir, github_token="ghp_fake_test_token")


def _make_scan_result(exit_code: ExitCode = ExitCode.ISSUES_FOUND) -> ScanResult:
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


def test_watch_state_fresh() -> None:
    state = WatchState(repo="owner/repo")
    assert state.seen_prs == {}
    assert state.has_seen(1) is False


def test_watch_state_mark_and_check() -> None:
    state = WatchState(repo="owner/repo")
    state.mark_seen(42, "https://github.com/owner/repo/pull/42#comment-1")
    assert state.has_seen(42) is True
    assert state.has_seen(43) is False
    assert state.seen_prs[42].pr_number == 42
    assert state.seen_prs[42].comment_url == "https://github.com/owner/repo/pull/42#comment-1"


def test_watch_state_roundtrip() -> None:
    state = WatchState(repo="owner/repo")
    state.mark_seen(10, "https://github.com/owner/repo/pull/10#comment-1")
    raw = state.model_dump_json(indent=2)
    loaded = WatchState.model_validate_json(raw)
    assert loaded.repo == state.repo
    assert loaded.has_seen(10) is True


def test_load_watch_state_no_file(tmp_path: Path) -> None:
    state = _load_watch_state(tmp_path / "missing.json", "owner/repo")
    assert state.repo == "owner/repo"
    assert state.seen_prs == {}


def test_load_watch_state_valid_file(tmp_path: Path) -> None:
    state = WatchState(repo="owner/repo")
    state.mark_seen(5, "https://github.com/owner/repo/pull/5#comment-1")
    (tmp_path / "state.json").write_text(state.model_dump_json(), encoding="utf-8")
    loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")
    assert loaded.has_seen(5) is True


def test_load_watch_state_corrupt_file(tmp_path: Path) -> None:
    (tmp_path / "state.json").write_text("not valid json {{{", encoding="utf-8")
    loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")
    assert loaded.repo == "owner/repo"
    assert loaded.seen_prs == {}


def test_load_watch_state_repo_mismatch(tmp_path: Path) -> None:
    state = WatchState(repo="other/repo")
    state.mark_seen(1, "https://github.com/other/repo/pull/1#comment-1")
    (tmp_path / "state.json").write_text(state.model_dump_json(), encoding="utf-8")
    loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")
    assert loaded.repo == "owner/repo"
    assert loaded.seen_prs == {}


def test_save_watch_state(tmp_path: Path) -> None:
    state = WatchState(repo="owner/repo")
    state.mark_seen(7, "https://github.com/owner/repo/pull/7#comment-1")
    _save_watch_state(state, tmp_path / "state.json")
    assert (tmp_path / "state.json").exists()
    loaded = _load_watch_state(tmp_path / "state.json", "owner/repo")
    assert loaded.has_seen(7) is True


@patch("src.cli.Github")
def test_list_open_prs_success(mock_github_cls: MagicMock) -> None:
    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.head.ref = "feature-a"
    mock_pr2 = MagicMock()
    mock_pr2.number = 2
    mock_pr2.head.ref = "feature-b"

    mock_gh = MagicMock()
    mock_github_cls.return_value.__enter__ = MagicMock(return_value=mock_gh)
    mock_github_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_gh.get_repo.return_value.get_pulls.return_value = [mock_pr1, mock_pr2]

    result = _list_open_prs("owner/repo", "fake-token")
    assert result == [(1, "feature-a"), (2, "feature-b")]


@patch("src.cli.Github")
def test_list_open_prs_github_error(mock_github_cls: MagicMock) -> None:
    from github import GithubException

    mock_gh = MagicMock()
    mock_github_cls.return_value.__enter__ = MagicMock(return_value=mock_gh)
    mock_github_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_gh.get_repo.side_effect = GithubException(500, "error", {})

    with pytest.raises(WatchError):
        _list_open_prs("owner/repo", "fake-token")


@patch("src.cli.format_pr_comment", return_value="https://github.com/owner/repo/pull/1#comment-1")
@patch("src.cli.run_audit")
@patch("src.cli.scan_github")
def test_process_single_pr_success(
    mock_scan_github: MagicMock,
    mock_run_audit: MagicMock,
    mock_format_pr_comment: MagicMock,
    tmp_path: Path,
) -> None:
    agent_config = _make_config(tmp_path)
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    mock_scan_github.return_value = ScanManifest(root_path=tmp_path, temp_dir=clone_dir)
    scan_result = _make_scan_result()
    mock_run_audit.return_value = scan_result

    url = _process_single_pr("owner/repo", 1, "feature-a", "fake-token", agent_config, False)
    assert url == "https://github.com/owner/repo/pull/1#comment-1"
    mock_scan_github.assert_called_once_with("owner/repo", "feature-a", "fake-token")
    mock_format_pr_comment.assert_called_once_with(scan_result, "owner/repo", 1, "fake-token")


@patch("src.cli.scan_github", side_effect=ScanError("clone failed"))
def test_process_single_pr_scan_error_propagates(mock_scan_github: MagicMock, tmp_path: Path) -> None:
    agent_config = _make_config(tmp_path)
    with pytest.raises(ScanError):
        _process_single_pr("owner/repo", 1, "feature-a", "fake-token", agent_config, False)


@patch("src.cli.load_config")
def test_watch_missing_token(mock_load_config: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    mock_load_config.return_value = AgentConfig(auditor_path=tmp_path)
    result = runner.invoke(app, ["watch", "--repo", "owner/repo"])
    assert result.exit_code == 2
    assert "GitHub token" in result.output


@patch("src.cli.load_config")
def test_watch_invalid_interval(mock_load_config: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_load_config.return_value = _make_config(tmp_path)
    result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "0"])
    assert result.exit_code == 2
    assert "--interval must be >= 1" in result.output


@patch("src.cli.time.sleep")
@patch("src.cli._process_single_pr", return_value="https://comment-url")
@patch("src.cli._list_open_prs")
@patch("src.cli.load_config")
def test_watch_processes_new_pr_and_skips_seen(
    mock_load_config: MagicMock,
    mock_list_prs: MagicMock,
    mock_process_pr: MagicMock,
    mock_sleep: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_file = tmp_path / "state.json"
    mock_load_config.return_value = _make_config(tmp_path)

    call_count = [0]

    def _list_side_effect(repo: str, token: str) -> list[tuple[int, str]]:
        call_count[0] += 1
        if call_count[0] >= 2:
            signal.raise_signal(signal.SIGINT)
        return [(1, "feature-a")]

    mock_list_prs.side_effect = _list_side_effect

    result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "1", "--state-file", str(state_file)])
    assert result.exit_code == 0
    assert mock_process_pr.call_count == 1
    assert state_file.exists()
    loaded = WatchState.model_validate_json(state_file.read_text(encoding="utf-8"))
    assert loaded.has_seen(1) is True


@patch("src.cli.time.sleep")
@patch("src.cli._process_single_pr")
@patch("src.cli._list_open_prs")
@patch("src.cli.load_config")
def test_watch_continues_on_pr_processing_error(
    mock_load_config: MagicMock,
    mock_list_prs: MagicMock,
    mock_process_pr: MagicMock,
    mock_sleep: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_load_config.return_value = _make_config(tmp_path)

    call_count = [0]

    def _list_side_effect(repo: str, token: str) -> list[tuple[int, str]]:
        call_count[0] += 1
        if call_count[0] >= 2:
            signal.raise_signal(signal.SIGINT)
        return [(1, "feat-a"), (2, "feat-b")]

    mock_list_prs.side_effect = _list_side_effect
    mock_process_pr.side_effect = [RunnerError("audit failed"), "https://comment-url"]

    result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "1", "--state-file", str(tmp_path / "state.json")])
    assert result.exit_code == 0
    loaded = WatchState.model_validate_json((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert 1 not in loaded.seen_prs
    assert loaded.has_seen(2) is True


@patch("src.cli.time.sleep")
@patch("src.cli._list_open_prs")
@patch("src.cli.load_config")
def test_watch_graceful_shutdown_message(
    mock_load_config: MagicMock,
    mock_list_prs: MagicMock,
    mock_sleep: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_load_config.return_value = _make_config(tmp_path)

    def _list_side_effect(repo: str, token: str) -> list[tuple[int, str]]:
        signal.raise_signal(signal.SIGINT)
        return []

    mock_list_prs.side_effect = _list_side_effect

    result = runner.invoke(app, ["watch", "--repo", "owner/repo", "--interval", "1", "--state-file", str(tmp_path / "state.json")])
    assert result.exit_code == 0
    assert "Watch stopped." in result.output
