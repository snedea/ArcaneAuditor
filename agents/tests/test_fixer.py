from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.fixer import apply_fixes, fix_findings
from src.models import (
    AgentConfig,
    Confidence,
    ExitCode,
    Finding,
    FixerError,
    FixResult,
    ScanManifest,
    ScanResult,
    Severity,
)
from src.runner import run_audit
from fix_templates.script_fixes import RemoveConsoleLog, TemplateLiteralFix, VarToLetConst
from fix_templates.structure_fixes import (
    AddFailOnStatusCodes,
    LowerCamelCaseEndpointName,
    LowerCamelCaseWidgetId,
)

AUDITOR_PATH: Path = Path(__file__).parent.parent.parent


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


def _make_auditor_config() -> AgentConfig:
    return AgentConfig(auditor_path=AUDITOR_PATH)


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


class TestLowConfidenceNotAutoApplied:
    def test_low_confidence_template_is_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\n", encoding="utf-8")
        finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)
        mock_template = MagicMock()
        mock_template.confidence = "LOW"
        mock_template.match.return_value = True
        mock_registry = MagicMock()
        mock_registry.find_matching.return_value = [mock_template]
        with patch("src.fixer.FixTemplateRegistry", return_value=mock_registry):
            result = fix_findings(_scan_result([finding]), tmp_path)
        assert result == []
        mock_template.apply.assert_not_called()

    def test_medium_and_low_templates_both_skipped_leaving_no_results(self, tmp_path: Path) -> None:
        (tmp_path / "test.script").write_text("var x = 1;\n", encoding="utf-8")
        finding = _finding(rule_id="ScriptVarUsageRule", file_path="test.script", line=1)
        mock_low = MagicMock()
        mock_low.confidence = "LOW"
        mock_low.match.return_value = True
        mock_med = MagicMock()
        mock_med.confidence = "MEDIUM"
        mock_med.match.return_value = True
        mock_registry = MagicMock()
        mock_registry.find_matching.return_value = [mock_low, mock_med]
        with patch("src.fixer.FixTemplateRegistry", return_value=mock_registry):
            result = fix_findings(_scan_result([finding]), tmp_path)
        assert result == []
        mock_low.apply.assert_not_called()
        mock_med.apply.assert_not_called()


@pytest.fixture(scope="module")
def var_to_let_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:
    config = _make_auditor_config()
    source_dir = tmp_path_factory.mktemp("var_to_let")
    violation_file = source_dir / "test.script"
    violation_file.write_text("var testCount = 0;\n{\n  \"count\": testCount\n}\n", encoding="utf-8")
    manifest = ScanManifest(root_path=source_dir)
    initial_result = run_audit(manifest, config)
    findings = [f for f in initial_result.findings if f.rule_id == "ScriptVarUsageRule"]
    assert len(findings) >= 1, "ScriptVarUsageRule finding not found in initial scan"
    finding = findings[0]
    content = violation_file.read_text(encoding="utf-8")
    template = VarToLetConst()
    fix_result = template.apply(finding, content)
    assert fix_result is not None, "VarToLetConst.apply() returned None"
    violation_file.write_text(fix_result.fixed_content, encoding="utf-8")
    fixed_result = run_audit(manifest, config)
    return (initial_result, fixed_result, "ScriptVarUsageRule")


class TestEndToEndVarToLetConst:
    def test_violation_present_in_initial_scan(self, var_to_let_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, _, rule_id = var_to_let_results
        matches = [f for f in initial_result.findings if f.rule_id == rule_id]
        assert len(matches) >= 1

    def test_violation_absent_after_fix(self, var_to_let_results: tuple[ScanResult, ScanResult, str]) -> None:
        _, fixed_result, rule_id = var_to_let_results
        matches = [f for f in fixed_result.findings if f.rule_id == rule_id]
        assert len(matches) == 0

    def test_fix_does_not_introduce_new_violations(self, var_to_let_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, fixed_result, _ = var_to_let_results
        assert fixed_result.findings_count <= initial_result.findings_count


@pytest.fixture(scope="module")
def remove_console_log_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:
    config = AgentConfig(auditor_path=AUDITOR_PATH, config_preset="production-ready")
    source_dir = tmp_path_factory.mktemp("remove_console_log")
    violation_file = source_dir / "test.script"
    violation_file.write_text("console.info('debug');\n{\n  \"result\": null\n}\n", encoding="utf-8")
    manifest = ScanManifest(root_path=source_dir)
    initial_result = run_audit(manifest, config)
    findings = [f for f in initial_result.findings if f.rule_id == "ScriptConsoleLogRule"]
    assert len(findings) >= 1, "ScriptConsoleLogRule finding not found in initial scan"
    finding = findings[0]
    content = violation_file.read_text(encoding="utf-8")
    template = RemoveConsoleLog()
    fix_result = template.apply(finding, content)
    assert fix_result is not None, "RemoveConsoleLog.apply() returned None"
    violation_file.write_text(fix_result.fixed_content, encoding="utf-8")
    fixed_result = run_audit(manifest, config)
    return (initial_result, fixed_result, "ScriptConsoleLogRule")


class TestEndToEndRemoveConsoleLog:
    def test_violation_present_in_initial_scan(self, remove_console_log_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, _, rule_id = remove_console_log_results
        matches = [f for f in initial_result.findings if f.rule_id == rule_id]
        assert len(matches) >= 1

    def test_violation_absent_after_fix(self, remove_console_log_results: tuple[ScanResult, ScanResult, str]) -> None:
        _, fixed_result, rule_id = remove_console_log_results
        matches = [f for f in fixed_result.findings if f.rule_id == rule_id]
        assert len(matches) == 0

    def test_fix_does_not_introduce_new_violations(self, remove_console_log_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, fixed_result, _ = remove_console_log_results
        assert fixed_result.findings_count <= initial_result.findings_count


@pytest.fixture(scope="module")
def template_literal_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:
    config = _make_auditor_config()
    source_dir = tmp_path_factory.mktemp("template_literal")
    violation_file = source_dir / "test.pmd"
    violation_file.write_text(
        '{\n  "id": "testPage",\n  "securityDomains": ["Everyone"],\n  "script": "<% const greeting = \'Hello \' + name; %>",\n  "presentation": {\n    "body": {\n      "type": "section",\n      "id": "bodySection",\n      "children": []\n    }\n  }\n}\n',
        encoding="utf-8",
    )
    manifest = ScanManifest(root_path=source_dir)
    initial_result = run_audit(manifest, config)
    findings = [f for f in initial_result.findings if f.rule_id == "ScriptStringConcatRule"]
    assert len(findings) >= 1, "ScriptStringConcatRule finding not found in initial scan"
    finding = findings[0]
    content = violation_file.read_text(encoding="utf-8")
    template = TemplateLiteralFix()
    fix_result = template.apply(finding, content)
    assert fix_result is not None, "TemplateLiteralFix.apply() returned None"
    violation_file.write_text(fix_result.fixed_content, encoding="utf-8")
    fixed_result = run_audit(manifest, config)
    return (initial_result, fixed_result, "ScriptStringConcatRule")


class TestEndToEndTemplateLiteralFix:
    def test_violation_present_in_initial_scan(self, template_literal_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, _, rule_id = template_literal_results
        matches = [f for f in initial_result.findings if f.rule_id == rule_id]
        assert len(matches) >= 1

    def test_violation_absent_after_fix(self, template_literal_results: tuple[ScanResult, ScanResult, str]) -> None:
        _, fixed_result, rule_id = template_literal_results
        matches = [f for f in fixed_result.findings if f.rule_id == rule_id]
        assert len(matches) == 0

    def test_fix_does_not_introduce_new_violations(self, template_literal_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, fixed_result, _ = template_literal_results
        assert fixed_result.findings_count <= initial_result.findings_count


@pytest.fixture(scope="module")
def widget_id_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:
    config = _make_auditor_config()
    source_dir = tmp_path_factory.mktemp("widget_id")
    violation_file = source_dir / "test.pmd"
    violation_file.write_text(
        '{\n  "id": "testPage",\n  "securityDomains": ["Everyone"],\n  "presentation": {\n    "body": {\n      "type": "section",\n      "id": "MyWidget",\n      "children": []\n    }\n  }\n}\n',
        encoding="utf-8",
    )
    manifest = ScanManifest(root_path=source_dir)
    initial_result = run_audit(manifest, config)
    findings = [f for f in initial_result.findings if f.rule_id == "WidgetIdLowerCamelCaseRule"]
    assert len(findings) >= 1, "WidgetIdLowerCamelCaseRule finding not found in initial scan"
    finding = findings[0]
    content = violation_file.read_text(encoding="utf-8")
    template = LowerCamelCaseWidgetId()
    fix_result = template.apply(finding, content)
    assert fix_result is not None, "LowerCamelCaseWidgetId.apply() returned None"
    violation_file.write_text(fix_result.fixed_content, encoding="utf-8")
    fixed_result = run_audit(manifest, config)
    return (initial_result, fixed_result, "WidgetIdLowerCamelCaseRule")


class TestEndToEndLowerCamelCaseWidgetId:
    def test_violation_present_in_initial_scan(self, widget_id_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, _, rule_id = widget_id_results
        matches = [f for f in initial_result.findings if f.rule_id == rule_id]
        assert len(matches) >= 1

    def test_violation_absent_after_fix(self, widget_id_results: tuple[ScanResult, ScanResult, str]) -> None:
        _, fixed_result, rule_id = widget_id_results
        matches = [f for f in fixed_result.findings if f.rule_id == rule_id]
        assert len(matches) == 0

    def test_fix_does_not_introduce_new_violations(self, widget_id_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, fixed_result, _ = widget_id_results
        assert fixed_result.findings_count <= initial_result.findings_count


@pytest.fixture(scope="module")
def endpoint_name_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:
    config = _make_auditor_config()
    source_dir = tmp_path_factory.mktemp("endpoint_name")
    violation_file = source_dir / "test.pod"
    violation_file.write_text(
        '{\n  "podId": "testPod",\n  "seed": {\n    "endPoints": [\n      {\n        "name": "GetHrData",\n        "url": "https://example.com/api",\n        "failOnStatusCodes": [{"code": 400}, {"code": 403}]\n      }\n    ]\n  }\n}\n',
        encoding="utf-8",
    )
    manifest = ScanManifest(root_path=source_dir)
    initial_result = run_audit(manifest, config)
    findings = [f for f in initial_result.findings if f.rule_id == "EndpointNameLowerCamelCaseRule"]
    assert len(findings) >= 1, "EndpointNameLowerCamelCaseRule finding not found in initial scan"
    finding = findings[0]
    content = violation_file.read_text(encoding="utf-8")
    template = LowerCamelCaseEndpointName()
    fix_result = template.apply(finding, content)
    assert fix_result is not None, "LowerCamelCaseEndpointName.apply() returned None"
    violation_file.write_text(fix_result.fixed_content, encoding="utf-8")
    fixed_result = run_audit(manifest, config)
    return (initial_result, fixed_result, "EndpointNameLowerCamelCaseRule")


class TestEndToEndLowerCamelCaseEndpointName:
    def test_violation_present_in_initial_scan(self, endpoint_name_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, _, rule_id = endpoint_name_results
        matches = [f for f in initial_result.findings if f.rule_id == rule_id]
        assert len(matches) >= 1

    def test_violation_absent_after_fix(self, endpoint_name_results: tuple[ScanResult, ScanResult, str]) -> None:
        _, fixed_result, rule_id = endpoint_name_results
        matches = [f for f in fixed_result.findings if f.rule_id == rule_id]
        assert len(matches) == 0

    def test_fix_does_not_introduce_new_violations(self, endpoint_name_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, fixed_result, _ = endpoint_name_results
        assert fixed_result.findings_count <= initial_result.findings_count


@pytest.fixture(scope="module")
def fail_on_status_codes_results(tmp_path_factory: pytest.TempPathFactory) -> tuple[ScanResult, ScanResult, str]:
    config = _make_auditor_config()
    source_dir = tmp_path_factory.mktemp("fail_on_status_codes")
    violation_file = source_dir / "test.pod"
    violation_file.write_text(
        '{\n  "podId": "testPod",\n  "seed": {\n    "endPoints": [\n      {\n        "name": "testEndpoint",\n        "url": "https://example.com/api"\n      }\n    ]\n  }\n}\n',
        encoding="utf-8",
    )
    manifest = ScanManifest(root_path=source_dir)
    initial_result = run_audit(manifest, config)
    findings = [f for f in initial_result.findings if f.rule_id == "EndpointFailOnStatusCodesRule"]
    assert len(findings) >= 1, "EndpointFailOnStatusCodesRule finding not found in initial scan"
    finding = findings[0]
    content = violation_file.read_text(encoding="utf-8")
    template = AddFailOnStatusCodes()
    fix_result = template.apply(finding, content)
    assert fix_result is not None, "AddFailOnStatusCodes.apply() returned None"
    violation_file.write_text(fix_result.fixed_content, encoding="utf-8")
    fixed_result = run_audit(manifest, config)
    return (initial_result, fixed_result, "EndpointFailOnStatusCodesRule")


class TestEndToEndAddFailOnStatusCodes:
    def test_violation_present_in_initial_scan(self, fail_on_status_codes_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, _, rule_id = fail_on_status_codes_results
        matches = [f for f in initial_result.findings if f.rule_id == rule_id]
        assert len(matches) >= 1

    def test_violation_absent_after_fix(self, fail_on_status_codes_results: tuple[ScanResult, ScanResult, str]) -> None:
        _, fixed_result, rule_id = fail_on_status_codes_results
        matches = [f for f in fixed_result.findings if f.rule_id == rule_id]
        assert len(matches) == 0

    def test_fix_does_not_introduce_new_violations(self, fail_on_status_codes_results: tuple[ScanResult, ScanResult, str]) -> None:
        initial_result, fixed_result, _ = fail_on_status_codes_results
        assert fixed_result.findings_count <= initial_result.findings_count
