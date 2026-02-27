from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import ScanError, ScanManifest
from src.scanner import EXTEND_EXTENSIONS, scan_github, scan_local


class TestScanLocal:

    def test_nonexistent_path_raises_scan_error(self, tmp_path: Path) -> None:
        with pytest.raises(ScanError, match="does not exist"):
            scan_local(tmp_path / "does_not_exist")

    def test_file_path_raises_scan_error(self, tmp_path: Path) -> None:
        f = tmp_path / "file.pmd"
        f.write_text("x")
        with pytest.raises(ScanError, match="not a directory"):
            scan_local(f)

    def test_empty_directory_returns_zero_total(self, tmp_path: Path) -> None:
        result = scan_local(tmp_path)
        assert result.total_count == 0
        assert result.root_path == tmp_path
        assert result.files_by_type == {"pmd": [], "pod": [], "script": [], "amd": [], "smd": []}

    def test_flat_directory_finds_all_extension_types(self, tmp_path: Path) -> None:
        (tmp_path / "a.pmd").write_text("x")
        (tmp_path / "b.pod").write_text("x")
        (tmp_path / "c.script").write_text("x")
        (tmp_path / "d.amd").write_text("x")
        (tmp_path / "e.smd").write_text("x")
        result = scan_local(tmp_path)
        assert result.total_count == 5
        assert len(result.files_by_type["pmd"]) == 1
        assert len(result.files_by_type["pod"]) == 1
        assert len(result.files_by_type["script"]) == 1
        assert len(result.files_by_type["amd"]) == 1
        assert len(result.files_by_type["smd"]) == 1

    def test_nested_directories_are_traversed(self, tmp_path: Path) -> None:
        sub = tmp_path / "level1" / "level2"
        sub.mkdir(parents=True)
        (tmp_path / "top.pmd").write_text("x")
        (sub / "deep.pmd").write_text("x")
        result = scan_local(tmp_path)
        assert result.total_count == 2
        assert len(result.files_by_type["pmd"]) == 2

    def test_non_extend_files_are_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "readme.md").write_text("x")
        (tmp_path / "config.json").write_text("{}")
        (tmp_path / "app.pmd").write_text("x")
        result = scan_local(tmp_path)
        assert result.total_count == 1
        assert len(result.files_by_type["pmd"]) == 1

    def test_returns_scan_manifest_instance(self, tmp_path: Path) -> None:
        result = scan_local(tmp_path)
        assert isinstance(result, ScanManifest)

    def test_multiple_files_per_type(self, tmp_path: Path) -> None:
        (tmp_path / "a.pmd").write_text("x")
        (tmp_path / "b.pmd").write_text("x")
        (tmp_path / "c.pmd").write_text("x")
        result = scan_local(tmp_path)
        assert result.total_count == 3
        assert len(result.files_by_type["pmd"]) == 3

    def test_extend_extensions_constant_contains_all_types(self) -> None:
        assert ".pmd" in EXTEND_EXTENSIONS
        assert ".pod" in EXTEND_EXTENSIONS
        assert ".script" in EXTEND_EXTENSIONS
        assert ".amd" in EXTEND_EXTENSIONS
        assert ".smd" in EXTEND_EXTENSIONS
        assert len(EXTEND_EXTENSIONS) == 5


class TestScanGithub:

    def test_invalid_repo_format_raises_scan_error(self) -> None:
        with pytest.raises(ScanError, match="Invalid repo format"):
            scan_github("noslash", "main", "tok")

    def test_invalid_repo_empty_owner_raises_scan_error(self) -> None:
        with pytest.raises(ScanError, match="Invalid repo format"):
            scan_github("/repo", "main", "tok")

    def test_invalid_repo_empty_name_raises_scan_error(self) -> None:
        with pytest.raises(ScanError, match="Invalid repo format"):
            scan_github("owner/", "main", "tok")

    @patch("src.scanner.subprocess.run")
    def test_git_clone_failure_raises_scan_error(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=128, stderr="fatal: repo not found")
        with pytest.raises(ScanError, match="git clone failed") as exc_info:
            scan_github("owner/repo", "main", "tok")
        assert "tok" not in str(exc_info.value)

    @patch("src.scanner.subprocess.run")
    def test_git_clone_timeout_raises_scan_error(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=120)
        with pytest.raises(ScanError, match="timed out"):
            scan_github("owner/repo", "main", "tok")

    @patch("src.scanner.scan_local")
    @patch("src.scanner.subprocess.run")
    def test_successful_clone_returns_manifest(self, mock_run: MagicMock, mock_scan_local: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_scan_local.return_value = ScanManifest(
            root_path=tmp_path,
            files_by_type={"pmd": [], "pod": [], "script": [], "amd": [], "smd": []},
        )
        manifest = scan_github("owner/repo", "main", "mytoken")
        assert manifest.repo == "owner/repo"
        assert manifest.branch == "main"
        assert manifest.temp_dir is not None
        assert isinstance(manifest, ScanManifest)
        shutil.rmtree(manifest.temp_dir, ignore_errors=True)

    @patch("src.scanner.scan_local")
    @patch("src.scanner.subprocess.run")
    def test_token_passed_via_askpass_not_in_url(self, mock_run: MagicMock, mock_scan_local: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        mock_scan_local.return_value = ScanManifest(root_path=tmp_path)
        manifest = scan_github("owner/repo", "main", "mytoken123")
        cmd_list = mock_run.call_args[0][0]
        # Token must NOT appear in argv (argv is visible to all local users via ps aux)
        assert not any("mytoken123" in arg for arg in cmd_list)
        # Clone URL must be the unauthenticated form
        assert "https://github.com/owner/repo.git" in cmd_list
        # Credentials are passed via GIT_ASKPASS env var instead
        env_passed = mock_run.call_args[1].get("env", {})
        assert "GIT_ASKPASS" in env_passed
        shutil.rmtree(manifest.temp_dir, ignore_errors=True)

    @patch("src.scanner.scan_local")
    @patch("src.scanner.subprocess.run")
    def test_empty_token_uses_unauthenticated_url(self, mock_run: MagicMock, mock_scan_local: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        mock_scan_local.return_value = ScanManifest(root_path=tmp_path)
        manifest = scan_github("owner/repo", "main", "")
        cmd_list = mock_run.call_args[0][0]
        assert "https://github.com/owner/repo.git" in cmd_list
        assert not any("@" in arg for arg in cmd_list if "github.com" in arg)
        shutil.rmtree(manifest.temp_dir, ignore_errors=True)

    @patch("src.scanner.scan_local")
    @patch("src.scanner.subprocess.run")
    def test_temp_dir_set_on_manifest_and_exists_after_call(self, mock_run: MagicMock, mock_scan_local: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_scan_local.return_value = ScanManifest(root_path=tmp_path)
        manifest = scan_github("owner/repo", "main", "")
        assert manifest.temp_dir is not None
        assert manifest.temp_dir.exists()
        shutil.rmtree(manifest.temp_dir, ignore_errors=True)

    @patch("src.scanner.scan_local")
    @patch("src.scanner.subprocess.run")
    def test_scan_local_error_propagates_as_scan_error(self, mock_run: MagicMock, mock_scan_local: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_scan_local.side_effect = ScanError("no Extend files")
        with pytest.raises(ScanError, match="no Extend files"):
            scan_github("owner/repo", "main", "")
