from __future__ import annotations

import json

import pytest

from fix_templates.base import FixTemplate, FixTemplateRegistry
from fix_templates.structure_fixes import (
    AddFailOnStatusCodes,
    LowerCamelCaseEndpointName,
    LowerCamelCaseWidgetId,
)
from src.models import Confidence, Finding, FixResult, Severity


def _finding(
    rule_id: str,
    line: int = 1,
    message: str = "test",
    file_path: str = "test.pmd",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=Severity.ACTION,
        message=message,
        file_path=file_path,
        line=line,
    )


class TestLowerCamelCaseWidgetId:
    def test_match_true_for_WidgetIdLowerCamelCaseRule(self) -> None:
        assert LowerCamelCaseWidgetId().match(_finding("WidgetIdLowerCamelCaseRule", 1)) is True

    def test_match_false_for_other_rule(self) -> None:
        assert LowerCamelCaseWidgetId().match(_finding("EndpointNameLowerCamelCaseRule", 1)) is False

    def test_apply_converts_PascalCase_id_to_lowerCamelCase(self) -> None:
        source = '{"id": "MyWidget", "type": "text"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MyWidget'")
        result = LowerCamelCaseWidgetId().apply(finding, source)
        assert result is not None
        assert '"id": "myWidget"' in result.fixed_content
        assert result.confidence == Confidence.HIGH

    def test_apply_converts_snake_case_id_to_lowerCamelCase(self) -> None:
        source = '{"id": "my_widget", "type": "text"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'my_widget'")
        result = LowerCamelCaseWidgetId().apply(finding, source)
        assert result is not None
        assert '"id": "myWidget"' in result.fixed_content

    def test_apply_converts_kebab_case_id_to_lowerCamelCase(self) -> None:
        source = '{"id": "my-widget", "type": "text"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'my-widget'")
        result = LowerCamelCaseWidgetId().apply(finding, source)
        assert result is not None
        assert '"id": "myWidget"' in result.fixed_content

    def test_apply_returns_none_when_line_zero(self) -> None:
        finding = _finding("WidgetIdLowerCamelCaseRule", 0, message="Widget has invalid name 'MyWidget'")
        assert LowerCamelCaseWidgetId().apply(finding, '{"id": "MyWidget"}\n') is None

    def test_apply_returns_none_when_line_exceeds_content(self) -> None:
        finding = _finding("WidgetIdLowerCamelCaseRule", 99, message="Widget has invalid name 'MyWidget'")
        assert LowerCamelCaseWidgetId().apply(finding, '{"id": "MyWidget"}\n') is None

    def test_apply_returns_none_when_message_does_not_match(self) -> None:
        source = '{"id": "MyWidget"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="some unrelated message")
        assert LowerCamelCaseWidgetId().apply(finding, source) is None

    def test_apply_returns_none_when_invalid_id_contains_angle_bracket(self) -> None:
        source = '{"id": "<% widget.id %>"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name '<% widget.id %>'")
        assert LowerCamelCaseWidgetId().apply(finding, source) is None

    def test_apply_returns_none_when_all_caps_no_separator(self) -> None:
        source = '{"id": "MYWIDGET"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MYWIDGET'")
        assert LowerCamelCaseWidgetId().apply(finding, source) is None

    def test_apply_returns_none_when_id_field_not_on_line(self) -> None:
        source = '"type": "text"\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MyWidget'")
        assert LowerCamelCaseWidgetId().apply(finding, source) is None

    def test_apply_returns_none_when_id_already_lower_camel(self) -> None:
        source = '{"id": "myWidget"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'myWidget'")
        assert LowerCamelCaseWidgetId().apply(finding, source) is None

    def test_apply_fix_result_fields(self) -> None:
        source = '{"id": "MyWidget"}\n'
        finding = _finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MyWidget'")
        result = LowerCamelCaseWidgetId().apply(finding, source)
        assert isinstance(result, FixResult)
        assert result.finding == finding
        assert result.original_content == source
        assert result.confidence == Confidence.HIGH


class TestLowerCamelCaseEndpointName:
    def test_match_true_for_EndpointNameLowerCamelCaseRule(self) -> None:
        assert LowerCamelCaseEndpointName().match(_finding("EndpointNameLowerCamelCaseRule", 1)) is True

    def test_match_false_for_other_rule(self) -> None:
        assert LowerCamelCaseEndpointName().match(_finding("WidgetIdLowerCamelCaseRule", 1)) is False

    def test_apply_converts_PascalCase_name_to_lowerCamelCase(self) -> None:
        source = '  {"name": "GetUser", "type": "inbound"}\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'GetUser' doesn't follow naming conventions")
        result = LowerCamelCaseEndpointName().apply(finding, source)
        assert result is not None
        assert '"name": "getUser"' in result.fixed_content
        assert result.confidence == Confidence.HIGH

    def test_apply_converts_snake_case_name_to_lowerCamelCase(self) -> None:
        source = '  {"name": "get_user"}\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'get_user' doesn't follow naming conventions")
        result = LowerCamelCaseEndpointName().apply(finding, source)
        assert result is not None
        assert '"name": "getUser"' in result.fixed_content

    def test_apply_converts_kebab_case_name_to_lowerCamelCase(self) -> None:
        source = '  {"name": "get-user"}\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="'get-user' doesn't follow naming conventions")
        result = LowerCamelCaseEndpointName().apply(finding, source)
        assert result is not None
        assert '"name": "getUser"' in result.fixed_content

    def test_apply_returns_none_when_line_zero(self) -> None:
        finding = _finding("EndpointNameLowerCamelCaseRule", 0, message="'GetUser' doesn't follow naming conventions")
        assert LowerCamelCaseEndpointName().apply(finding, '{"name": "GetUser"}\n') is None

    def test_apply_returns_none_when_line_exceeds_content(self) -> None:
        finding = _finding("EndpointNameLowerCamelCaseRule", 99, message="'GetUser' doesn't follow naming conventions")
        assert LowerCamelCaseEndpointName().apply(finding, '{"name": "GetUser"}\n') is None

    def test_apply_returns_none_when_message_does_not_match(self) -> None:
        source = '{"name": "GetUser"}\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="some unrelated message")
        assert LowerCamelCaseEndpointName().apply(finding, source) is None

    def test_apply_returns_none_when_name_field_not_on_line(self) -> None:
        source = '"type": "inbound"\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'GetUser' doesn't follow naming conventions")
        assert LowerCamelCaseEndpointName().apply(finding, source) is None

    def test_apply_returns_none_when_all_caps_no_separator(self) -> None:
        source = '{"name": "GETUSER"}\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="'GETUSER' doesn't follow naming conventions")
        assert LowerCamelCaseEndpointName().apply(finding, source) is None

    def test_apply_returns_none_when_name_already_lower_camel(self) -> None:
        source = '{"name": "getUser"}\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="'getUser' doesn't follow naming conventions")
        assert LowerCamelCaseEndpointName().apply(finding, source) is None

    def test_apply_fix_result_fields(self) -> None:
        source = '{"name": "GetUser"}\n'
        finding = _finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'GetUser' doesn't follow naming conventions")
        result = LowerCamelCaseEndpointName().apply(finding, source)
        assert isinstance(result, FixResult)
        assert result.finding == finding
        assert result.original_content == source
        assert result.confidence == Confidence.HIGH


class TestAddFailOnStatusCodes:
    def test_match_true_for_EndpointFailOnStatusCodesRule(self) -> None:
        assert AddFailOnStatusCodes().match(_finding("EndpointFailOnStatusCodesRule", 1)) is True

    def test_match_false_for_other_rule(self) -> None:
        assert AddFailOnStatusCodes().match(_finding("WidgetIdLowerCamelCaseRule", 1)) is False

    def test_apply_adds_field_to_inbound_endpoint_when_missing(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        assert result is not None
        data = json.loads(result.fixed_content)
        ep = data["inboundEndpoints"][0]
        assert "failOnStatusCodes" in ep
        codes = {e["code"] for e in ep["failOnStatusCodes"]}
        assert codes == {400, 403}
        assert result.confidence == Confidence.HIGH

    def test_apply_adds_field_to_outbound_endpoint_when_missing(self) -> None:
        source_content = json.dumps({"outboundEndpoints": [{"name": "saveRecord"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'saveRecord' is missing required 'failOnStatusCodes' field")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        assert result is not None
        data = json.loads(result.fixed_content)
        ep = data["outboundEndpoints"][0]
        assert "failOnStatusCodes" in ep
        codes = {e["code"] for e in ep["failOnStatusCodes"]}
        assert codes == {400, 403}

    def test_apply_adds_field_to_seed_endpoint_when_missing(self) -> None:
        source_content = json.dumps({"seed": {"endPoints": [{"name": "fetchData"}]}}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'fetchData' is missing required 'failOnStatusCodes' field")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        assert result is not None
        data = json.loads(result.fixed_content)
        ep = data["seed"]["endPoints"][0]
        assert "failOnStatusCodes" in ep
        codes = {e["code"] for e in ep["failOnStatusCodes"]}
        assert codes == {400, 403}

    def test_apply_adds_missing_single_code_to_existing_field(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser", "failOnStatusCodes": [{"code": 400}]}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required status codes: 403.")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        assert result is not None
        data = json.loads(result.fixed_content)
        ep = data["inboundEndpoints"][0]
        codes = {e["code"] for e in ep["failOnStatusCodes"]}
        assert codes == {400, 403}

    def test_apply_adds_multiple_missing_codes_via_codes_pattern(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required status codes: 400, 403.")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        assert result is not None
        data = json.loads(result.fixed_content)
        codes = {e["code"] for e in data["inboundEndpoints"][0]["failOnStatusCodes"]}
        assert codes == {400, 403}

    def test_apply_returns_none_when_json_invalid(self) -> None:
        source_content = "not valid json"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")
        assert AddFailOnStatusCodes().apply(finding, source_content) is None

    def test_apply_returns_none_when_message_matches_neither_pattern(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="something completely unrelated")
        assert AddFailOnStatusCodes().apply(finding, source_content) is None

    def test_apply_returns_none_when_endpoint_name_not_found_in_json(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'notExist' is missing required 'failOnStatusCodes' field")
        assert AddFailOnStatusCodes().apply(finding, source_content) is None

    def test_apply_output_is_indented_with_2_spaces_and_trailing_newline(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        assert result is not None
        assert result.fixed_content.endswith("\n")
        lines = result.fixed_content.splitlines()
        assert lines[1].startswith("  ")

    def test_apply_codes_are_sorted_ascending_in_output(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        data = json.loads(result.fixed_content)
        codes_list = [e["code"] for e in data["inboundEndpoints"][0]["failOnStatusCodes"]]
        assert codes_list == sorted(codes_list)
        assert codes_list == [400, 403]

    def test_apply_fix_result_fields(self) -> None:
        source_content = json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"
        finding = _finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")
        result = AddFailOnStatusCodes().apply(finding, source_content)
        assert isinstance(result, FixResult)
        assert result.finding == finding
        assert result.original_content == source_content
        assert result.confidence == Confidence.HIGH


class TestFixTemplateRegistryStructureFixes:
    def test_registry_discovers_all_three_structure_fix_templates(self) -> None:
        registry = FixTemplateRegistry()
        types = {type(t).__name__ for t in registry.templates}
        assert "LowerCamelCaseWidgetId" in types
        assert "LowerCamelCaseEndpointName" in types
        assert "AddFailOnStatusCodes" in types

    def test_registry_find_matching_returns_lower_camel_case_widget_id(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("WidgetIdLowerCamelCaseRule", 1)
        matches = registry.find_matching(finding)
        assert len(matches) == 1
        assert isinstance(matches[0], LowerCamelCaseWidgetId)

    def test_registry_find_matching_returns_lower_camel_case_endpoint_name(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("EndpointNameLowerCamelCaseRule", 1)
        matches = registry.find_matching(finding)
        assert len(matches) == 1
        assert isinstance(matches[0], LowerCamelCaseEndpointName)

    def test_registry_find_matching_returns_add_fail_on_status_codes(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("EndpointFailOnStatusCodesRule", 1)
        matches = registry.find_matching(finding)
        assert len(matches) == 1
        assert isinstance(matches[0], AddFailOnStatusCodes)

    def test_registry_find_matching_returns_empty_for_unknown_rule(self) -> None:
        registry = FixTemplateRegistry()
        finding = _finding("UnknownRule", 1)
        matches = registry.find_matching(finding)
        assert matches == []


class TestFixTemplateABC:
    def test_all_structure_fix_templates_are_FixTemplate_subclasses(self) -> None:
        for cls in [LowerCamelCaseWidgetId, LowerCamelCaseEndpointName, AddFailOnStatusCodes]:
            assert issubclass(cls, FixTemplate) is True

    def test_all_structure_fix_templates_have_HIGH_confidence(self) -> None:
        for cls in [LowerCamelCaseWidgetId, LowerCamelCaseEndpointName, AddFailOnStatusCodes]:
            instance = cls()
            assert instance.confidence == "HIGH"
