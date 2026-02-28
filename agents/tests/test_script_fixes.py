from __future__ import annotations

import pytest

from fix_templates.base import FixTemplate, FixTemplateRegistry
from fix_templates.script_fixes import RemoveConsoleLog, TemplateLiteralFix, VarToLetConst
from src.models import Confidence, Finding, FixResult, Severity


def _finding(rule_id: str, line: int, file_path: str = "test.pmd") -> Finding:
    return Finding(rule_id=rule_id, severity=Severity.ACTION, message="test", file_path=file_path, line=line)


class TestVarToLetConst:
    def test_match_true_for_ScriptVarUsageRule(self) -> None:
        template = VarToLetConst()
        assert template.match(_finding("ScriptVarUsageRule", 1)) is True

    def test_match_false_for_other_rule(self) -> None:
        template = VarToLetConst()
        assert template.match(_finding("ScriptConsoleLogRule", 1)) is False

    def test_apply_var_becomes_const_when_no_reassignment(self) -> None:
        source = "var x = 1;\nreturn x;\n"
        finding = _finding("ScriptVarUsageRule", 1)
        result = VarToLetConst().apply(finding, source)
        assert result is not None
        assert result.fixed_content == "const x = 1;\nreturn x;\n"
        assert result.confidence == Confidence.HIGH

    def test_apply_var_becomes_let_when_reassigned_below(self) -> None:
        source = "var x = 1;\nx = 2;\nreturn x;\n"
        finding = _finding("ScriptVarUsageRule", 1)
        result = VarToLetConst().apply(finding, source)
        assert result is not None
        assert result.fixed_content == "let x = 1;\nx = 2;\nreturn x;\n"

    def test_apply_var_becomes_let_when_incremented(self) -> None:
        source = "var i = 0;\ni++;\nreturn i;\n"
        finding = _finding("ScriptVarUsageRule", 1)
        result = VarToLetConst().apply(finding, source)
        assert result is not None
        assert result.fixed_content == "let i = 0;\ni++;\nreturn i;\n"

    def test_apply_returns_none_when_line_zero(self) -> None:
        finding = _finding("ScriptVarUsageRule", 0)
        result = VarToLetConst().apply(finding, "var x = 1;\n")
        assert result is None

    def test_apply_returns_none_when_line_exceeds_content(self) -> None:
        finding = _finding("ScriptVarUsageRule", 99)
        result = VarToLetConst().apply(finding, "var x = 1;\n")
        assert result is None

    def test_apply_returns_none_when_no_var_on_line(self) -> None:
        source = "let x = 1;\n"
        finding = _finding("ScriptVarUsageRule", 1)
        result = VarToLetConst().apply(finding, source)
        assert result is None

    def test_apply_multi_var_const_when_none_reassigned(self) -> None:
        source = "var x = 1, y = 2;\nreturn x + y;\n"
        finding = _finding("ScriptVarUsageRule", 1)
        result = VarToLetConst().apply(finding, source)
        assert result is not None
        assert result.fixed_content == "const x = 1, y = 2;\nreturn x + y;\n"

    def test_apply_multi_var_let_when_extra_var_reassigned(self) -> None:
        source = "var x = 1, y = 2;\ny = 3;\nreturn x + y;\n"
        finding = _finding("ScriptVarUsageRule", 1)
        result = VarToLetConst().apply(finding, source)
        assert result is not None
        assert result.fixed_content == "let x = 1, y = 2;\ny = 3;\nreturn x + y;\n"

    def test_apply_fix_result_fields(self) -> None:
        source = "var n = 5;\n"
        finding = _finding("ScriptVarUsageRule", 1)
        result = VarToLetConst().apply(finding, source)
        assert isinstance(result, FixResult)
        assert result.finding == finding
        assert result.original_content == source
        assert result.confidence == Confidence.HIGH


class TestRemoveConsoleLog:
    def test_match_true_for_ScriptConsoleLogRule(self) -> None:
        template = RemoveConsoleLog()
        assert template.match(_finding("ScriptConsoleLogRule", 1)) is True

    def test_match_false_for_other_rule(self) -> None:
        template = RemoveConsoleLog()
        assert template.match(_finding("ScriptVarUsageRule", 1)) is False

    def test_apply_removes_console_log_only_line(self) -> None:
        source = "doSomething();\nconsole.log('debug');\nreturn 1;\n"
        finding = _finding("ScriptConsoleLogRule", 2)
        result = RemoveConsoleLog().apply(finding, source)
        assert result is not None
        assert result.fixed_content == "doSomething();\nreturn 1;\n"
        assert result.confidence == Confidence.HIGH

    def test_apply_removes_console_warn(self) -> None:
        source = "console.warn('x');\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        result = RemoveConsoleLog().apply(finding, source)
        assert result is not None
        assert result.fixed_content == ""

    def test_apply_removes_console_error(self) -> None:
        source = "console.error('x');\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        result = RemoveConsoleLog().apply(finding, source)
        assert result is not None
        assert result.fixed_content == ""

    def test_apply_removes_console_info(self) -> None:
        source = "console.info('x');\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        result = RemoveConsoleLog().apply(finding, source)
        assert result is not None
        assert result.fixed_content == ""

    def test_apply_removes_console_debug(self) -> None:
        source = "console.debug('x');\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        result = RemoveConsoleLog().apply(finding, source)
        assert result is not None
        assert result.fixed_content == ""

    def test_apply_keeps_line_when_other_code_present(self) -> None:
        source = "foo(); console.log('x');\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        result = RemoveConsoleLog().apply(finding, source)
        assert result is not None
        assert "console.log" not in result.fixed_content
        assert "foo()" in result.fixed_content

    def test_apply_returns_none_when_line_zero(self) -> None:
        finding = _finding("ScriptConsoleLogRule", 0)
        assert RemoveConsoleLog().apply(finding, "console.log('x');\n") is None

    def test_apply_returns_none_when_line_exceeds_content(self) -> None:
        finding = _finding("ScriptConsoleLogRule", 99)
        assert RemoveConsoleLog().apply(finding, "console.log('x');\n") is None

    def test_apply_returns_none_when_no_console_on_line(self) -> None:
        source = "doSomething();\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        assert RemoveConsoleLog().apply(finding, source) is None

    def test_apply_returns_none_when_nested_console_remains(self) -> None:
        source = "console.log(console.error('x'));\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        result = RemoveConsoleLog().apply(finding, source)
        assert result is None

    def test_apply_fix_result_fields(self) -> None:
        source = "console.log('x');\n"
        finding = _finding("ScriptConsoleLogRule", 1)
        result = RemoveConsoleLog().apply(finding, source)
        assert isinstance(result, FixResult)
        assert result.finding == finding
        assert result.original_content == source
        assert result.confidence == Confidence.HIGH


class TestTemplateLiteralFix:
    def test_match_true_for_ScriptStringConcatRule(self) -> None:
        template = TemplateLiteralFix()
        assert template.match(_finding("ScriptStringConcatRule", 1)) is True

    def test_match_false_for_other_rule(self) -> None:
        template = TemplateLiteralFix()
        assert template.match(_finding("ScriptVarUsageRule", 1)) is False

    def test_apply_string_plus_var_to_template_literal(self) -> None:
        source = "var msg = 'Hello ' + name;\n"
        finding = _finding("ScriptStringConcatRule", 1)
        result = TemplateLiteralFix().apply(finding, source)
        assert result is not None
        assert "`Hello ${name}`" in result.fixed_content
        assert result.confidence == Confidence.HIGH

    def test_apply_var_plus_string_to_template_literal(self) -> None:
        source = "var msg = name + ' world';\n"
        finding = _finding("ScriptStringConcatRule", 1)
        result = TemplateLiteralFix().apply(finding, source)
        assert result is not None
        assert "`${name} world`" in result.fixed_content

    def test_apply_returns_none_for_function_call_not_var(self) -> None:
        source = "var msg = 'Hello ' + getName();\n"
        finding = _finding("ScriptStringConcatRule", 1)
        result = TemplateLiteralFix().apply(finding, source)
        assert result is None

    def test_apply_returns_none_for_property_access_plus_string(self) -> None:
        source = "var msg = arr.length + ' items';\n"
        finding = _finding("ScriptStringConcatRule", 1)
        result = TemplateLiteralFix().apply(finding, source)
        assert result is None

    def test_apply_returns_none_when_both_patterns_present(self) -> None:
        source = "var x = 'a' + b + c + 'd';\n"
        finding = _finding("ScriptStringConcatRule", 1)
        result = TemplateLiteralFix().apply(finding, source)
        assert result is None

    def test_apply_returns_none_when_line_zero(self) -> None:
        finding = _finding("ScriptStringConcatRule", 0)
        assert TemplateLiteralFix().apply(finding, "'a' + b;\n") is None

    def test_apply_returns_none_when_line_exceeds_content(self) -> None:
        finding = _finding("ScriptStringConcatRule", 99)
        assert TemplateLiteralFix().apply(finding, "'a' + b;\n") is None

    def test_apply_returns_none_when_no_concat_on_line(self) -> None:
        source = "var x = 'hello';\n"
        finding = _finding("ScriptStringConcatRule", 1)
        assert TemplateLiteralFix().apply(finding, source) is None

    def test_apply_fix_result_fields(self) -> None:
        source = "var msg = 'Hi ' + user;\n"
        finding = _finding("ScriptStringConcatRule", 1)
        result = TemplateLiteralFix().apply(finding, source)
        assert isinstance(result, FixResult)
        assert result.finding == finding
        assert result.original_content == source
        assert result.confidence == Confidence.HIGH


class TestFixTemplateRegistryScriptFixes:
    def test_registry_discovers_all_three_script_fix_templates(self) -> None:
        registry = FixTemplateRegistry()
        types = {type(t).__name__ for t in registry.templates}
        assert "VarToLetConst" in types
        assert "RemoveConsoleLog" in types
        assert "TemplateLiteralFix" in types

    def test_registry_find_matching_returns_var_to_let_const(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("ScriptVarUsageRule", 1)
        matches = registry.find_matching(finding)
        assert len(matches) == 1
        assert isinstance(matches[0], VarToLetConst)

    def test_registry_find_matching_returns_remove_console_log(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("ScriptConsoleLogRule", 1)
        matches = registry.find_matching(finding)
        assert len(matches) == 1
        assert isinstance(matches[0], RemoveConsoleLog)

    def test_registry_find_matching_returns_template_literal_fix(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("ScriptStringConcatRule", 1)
        matches = registry.find_matching(finding)
        assert len(matches) == 1
        assert isinstance(matches[0], TemplateLiteralFix)

    def test_registry_find_matching_returns_empty_for_unknown_rule(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("UnknownRule", 1)
        matches = registry.find_matching(finding)
        assert matches == []


class TestFixTemplateABC:
    def test_all_script_fix_templates_are_FixTemplate_subclasses(self) -> None:
        for cls in [VarToLetConst, RemoveConsoleLog, TemplateLiteralFix]:
            assert issubclass(cls, FixTemplate) is True

    def test_all_script_fix_templates_have_HIGH_confidence(self) -> None:
        for cls in [VarToLetConst, RemoveConsoleLog, TemplateLiteralFix]:
            instance = cls()
            assert instance.confidence == "HIGH"
