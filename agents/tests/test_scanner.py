from __future__ import annotations

from pathlib import Path

import pytest

from src.models import ScanError, ScanManifest
from src.scanner import EXTEND_EXTENSIONS, scan_local


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
