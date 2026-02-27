from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.fixer import apply_fixes, fix_findings
from src.models import (
    Confidence,
    ExitCode,
    Finding,
    FixerError,
    FixResult,
    ScanResult,
    Severity,
)


def _finding(
    rule_id: str = "ScriptVarUsageRule",
    line: int = 1,
    file_path: str = "test.script",
    message: str = "test",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=Severity.ACTION,
        message=message,
        file_path=file_path,
        line=line,
    )


def _scan_result(findings: list[Finding]) -> ScanResult:
    return ScanResult(
        repo="test-repo",
        findings_count=len(findings),
        findings=findings,
        exit_code=ExitCode.ISSUES_FOUND if findings else ExitCode.CLEAN,
    )


def _fix_result(
    file_path: str = "test.script",
    original: str = "var x = 1;\n",
    fixed: str = "const x = 1;\n",
) -> FixResult:
    return FixResult(
        finding=_finding(file_path=file_path),
        original_content=original,
        fixed_content=fixed,
        confidence=Confidence.HIGH,
    )


class TestFixFindings:
    def test_returns_empty_list_for_empty_findings(self, tmp_path: Path) -> None:
        result = fix_findings(_scan_result([]), tmp_path)
        assert result == []

    def test_skips_finding_when_file_not_found(self, tmp_path: Path) -> None:
        finding = _finding(file_path="nonexistent.script")
        result = fix_findings(_scan_result([finding]), tmp_path)
        assert result == []

    def test_skips_finding_with_no_matching_template(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\n", encoding="utf-8")
        finding = _finding(rule_id="UnknownRuleWithNoTemplate", file_path="test.script", line=1)
        result = fix_findings(_scan_result([finding]), tmp_path)
        assert result == []

    def test_applies_high_confidence_template_and_returns_fix_result(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\nreturn x;\n", encoding="utf-8")
        finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)
        result = fix_findings(_scan_result([finding]), tmp_path)
        assert len(result) == 1
        assert isinstance(result[0], FixResult)
        assert "const x = 1;" in result[0].fixed_content
        assert result[0].confidence == Confidence.HIGH

    def test_does_not_modify_file_on_disk(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\n", encoding="utf-8")
        finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)
        fix_findings(_scan_result([finding]), tmp_path)
        content = (tmp_path / "test.script").read_text(encoding="utf-8")
        assert content == "var x = 1;\n"

    def test_does_not_apply_non_high_confidence_template(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\n", encoding="utf-8")
        finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)
        mock_template = MagicMock()
        mock_template.confidence = "MEDIUM"
        mock_template.match.return_value = True
        mock_registry = MagicMock()
        mock_registry.find_matching.return_value = [mock_template]
        with patch("src.fixer.FixTemplateRegistry", return_value=mock_registry):
            result = fix_findings(_scan_result([finding]), tmp_path)
        assert result == []
        mock_template.apply.assert_not_called()

    def test_exception_in_apply_is_suppressed(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\n", encoding="utf-8")
        finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)
        mock_template = MagicMock()
        mock_template.confidence = "HIGH"
        mock_template.match.return_value = True
        mock_template.apply.side_effect = RuntimeError("boom")
        mock_registry = MagicMock()
        mock_registry.find_matching.return_value = [mock_template]
        with patch("src.fixer.FixTemplateRegistry", return_value=mock_registry):
            result = fix_findings(_scan_result([finding]), tmp_path)
        assert result == []

    def test_apply_returning_none_is_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\n", encoding="utf-8")
        finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)
        mock_template = MagicMock()
        mock_template.confidence = "HIGH"
        mock_template.match.return_value = True
        mock_template.apply.return_value = None
        mock_registry = MagicMock()
        mock_registry.find_matching.return_value = [mock_template]
        with patch("src.fixer.FixTemplateRegistry", return_value=mock_registry):
            result = fix_findings(_scan_result([finding]), tmp_path)
        assert result == []

    def test_multiple_findings_multiple_fixes(self, tmp_path: Path) -> None:
        (tmp_path / "a.script").write_text("var x = 1;\n", encoding="utf-8")
        (tmp_path / "b.script").write_text("var y = 2;\n", encoding="utf-8")
        finding_a = _finding(rule_id="ScriptVarUsageRule", file_path="a.script", line=1)
        finding_b = _finding(rule_id="ScriptVarUsageRule", file_path="b.script", line=1)
        result = fix_findings(_scan_result([finding_a, finding_b]), tmp_path)
        assert len(result) == 2


class TestApplyFixes:
    def test_returns_empty_list_for_empty_input(self, tmp_path: Path) -> None:
        result = apply_fixes([], tmp_path)
        assert result == []

    def test_writes_fixed_content_to_target_dir(self, tmp_path: Path) -> None:
        fr = _fix_result(file_path="test.script", fixed="const x = 1;\n")
        written = apply_fixes([fr], tmp_path)
        assert len(written) == 1
        assert written[0] == tmp_path / "test.script"
        assert (tmp_path / "test.script").read_text(encoding="utf-8") == "const x = 1;\n"

    def test_creates_nested_parent_directories(self, tmp_path: Path) -> None:
        fr = _fix_result(file_path="subdir/nested/test.script", fixed="let z = 3;\n")
        apply_fixes([fr], tmp_path)
        assert (tmp_path / "subdir" / "nested" / "test.script").exists()
        assert (tmp_path / "subdir" / "nested" / "test.script").read_text(encoding="utf-8") == "let z = 3;\n"

    def test_returns_list_of_written_paths(self, tmp_path: Path) -> None:
        fr_a = _fix_result(file_path="a.script", fixed="const a = 1;\n")
        fr_b = _fix_result(file_path="b.script", fixed="const b = 2;\n")
        written = apply_fixes([fr_a, fr_b], tmp_path)
        assert len(written) == 2
        assert tmp_path / "a.script" in written
        assert tmp_path / "b.script" in written

    def test_deduplication_first_fix_wins(self, tmp_path: Path) -> None:
        fr_first = _fix_result(file_path="dup.script", original="var x=1;\n", fixed="const x=1;\n")
        fr_second = _fix_result(file_path="dup.script", original="var x=1;\n", fixed="let x=1;\n")
        written = apply_fixes([fr_first, fr_second], tmp_path)
        assert len(written) == 1
        assert (tmp_path / "dup.script").read_text(encoding="utf-8") == "const x=1;\n"

    def test_raises_FixerError_for_absolute_path(self, tmp_path: Path) -> None:
        fr = _fix_result(file_path="/etc/passwd", fixed="bad\n")
        with pytest.raises(FixerError):
            apply_fixes([fr], tmp_path)

    def test_raises_FixerError_for_path_traversal(self, tmp_path: Path) -> None:
        fr = _fix_result(file_path="../outside.script", fixed="bad\n")
        with pytest.raises(FixerError):
            apply_fixes([fr], tmp_path)

    def test_raises_FixerError_on_write_failure(self, tmp_path: Path) -> None:
        fr = _fix_result(file_path="test.script", fixed="const x=1;\n")
        with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
            with pytest.raises(FixerError):
                apply_fixes([fr], tmp_path)
