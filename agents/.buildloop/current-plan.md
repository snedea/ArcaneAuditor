# Plan: P6.3

## Status
`fix_templates/structure_fixes.py` already exists and is fully implemented (WIP commit 8d54c17).
The only deliverable for P6.3 is: **CREATE** `tests/test_structure_fixes.py`.

## Dependencies
- list: [] (no new packages required; pytest already in dev dependencies)
- commands: [] (no install commands needed)

## File Operations (in execution order)

### 1. CREATE tests/test_structure_fixes.py
- operation: CREATE
- reason: Every module needs a test file per CLAUDE.md. `test_script_fixes.py` exists for P6.2; the equivalent for P6.3 does not exist yet.

#### Imports / Dependencies
```python
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
```

#### Helper Function
```python
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
```

#### Class: TestLowerCamelCaseWidgetId

- signature: `class TestLowerCamelCaseWidgetId`

  **test_match_true_for_WidgetIdLowerCamelCaseRule**
  - logic:
    1. Create `LowerCamelCaseWidgetId()`.
    2. Call `match(_finding("WidgetIdLowerCamelCaseRule", 1))`.
    3. Assert result is `True`.

  **test_match_false_for_other_rule**
  - logic:
    1. Create `LowerCamelCaseWidgetId()`.
    2. Call `match(_finding("EndpointNameLowerCamelCaseRule", 1))`.
    3. Assert result is `False`.

  **test_apply_converts_PascalCase_id_to_lowerCamelCase**
  - logic:
    1. source = `'{"id": "MyWidget", "type": "text"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MyWidget'")`
    3. result = `LowerCamelCaseWidgetId().apply(finding, source)`
    4. Assert `result is not None`.
    5. Assert `'"id": "myWidget"'` is in `result.fixed_content`.
    6. Assert `result.confidence == Confidence.HIGH`.

  **test_apply_converts_snake_case_id_to_lowerCamelCase**
  - logic:
    1. source = `'{"id": "my_widget", "type": "text"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'my_widget'")`
    3. result = `LowerCamelCaseWidgetId().apply(finding, source)`
    4. Assert `result is not None`.
    5. Assert `'"id": "myWidget"'` is in `result.fixed_content`.

  **test_apply_converts_kebab_case_id_to_lowerCamelCase**
  - logic:
    1. source = `'{"id": "my-widget", "type": "text"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'my-widget'")`
    3. result = `LowerCamelCaseWidgetId().apply(finding, source)`
    4. Assert `result is not None`.
    5. Assert `'"id": "myWidget"'` is in `result.fixed_content`.

  **test_apply_returns_none_when_line_zero**
  - logic:
    1. finding = `_finding("WidgetIdLowerCamelCaseRule", 0, message="Widget has invalid name 'MyWidget'")`
    2. Assert `LowerCamelCaseWidgetId().apply(finding, '{"id": "MyWidget"}\n') is None`.

  **test_apply_returns_none_when_line_exceeds_content**
  - logic:
    1. finding = `_finding("WidgetIdLowerCamelCaseRule", 99, message="Widget has invalid name 'MyWidget'")`
    2. Assert `LowerCamelCaseWidgetId().apply(finding, '{"id": "MyWidget"}\n') is None`.

  **test_apply_returns_none_when_message_does_not_match**
  - logic:
    1. source = `'{"id": "MyWidget"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="some unrelated message")`
    3. Assert `LowerCamelCaseWidgetId().apply(finding, source) is None`.

  **test_apply_returns_none_when_invalid_id_contains_angle_bracket**
  - logic:
    1. source = `'{"id": "<% widget.id %>"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name '<% widget.id %>'")`
    3. Assert `LowerCamelCaseWidgetId().apply(finding, source) is None`.
    - reason: `"<"` in invalid_id triggers early return None.

  **test_apply_returns_none_when_all_caps_no_separator**
  - logic:
    1. source = `'{"id": "MYWIDGET"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MYWIDGET'")`
    3. Assert `LowerCamelCaseWidgetId().apply(finding, source) is None`.
    - reason: `_to_lower_camel_case("MYWIDGET")` returns None (matches `_PASCAL_RE` but `has_lower` is False).

  **test_apply_returns_none_when_id_field_not_on_line**
  - logic:
    1. source = `'"type": "text"\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MyWidget'")`
    3. Assert `LowerCamelCaseWidgetId().apply(finding, source) is None`.
    - reason: The compiled `field_re` for `"id": "MyWidget"` does not match the target line, so `modified_line == target_line`.

  **test_apply_returns_none_when_id_already_lower_camel**
  - logic:
    1. source = `'{"id": "myWidget"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'myWidget'")`
    3. Assert `LowerCamelCaseWidgetId().apply(finding, source) is None`.
    - reason: `_to_lower_camel_case("myWidget")` returns `"myWidget"` (already matches `_LOWER_CAMEL_RE`), so `fixed_id == invalid_id` triggers return None.

  **test_apply_fix_result_fields**
  - logic:
    1. source = `'{"id": "MyWidget"}\n'`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1, message="Widget has invalid name 'MyWidget'")`
    3. result = `LowerCamelCaseWidgetId().apply(finding, source)`
    4. Assert `isinstance(result, FixResult)`.
    5. Assert `result.finding == finding`.
    6. Assert `result.original_content == source`.
    7. Assert `result.confidence == Confidence.HIGH`.

#### Class: TestLowerCamelCaseEndpointName

- signature: `class TestLowerCamelCaseEndpointName`

  **test_match_true_for_EndpointNameLowerCamelCaseRule**
  - logic:
    1. Create `LowerCamelCaseEndpointName()`.
    2. Call `match(_finding("EndpointNameLowerCamelCaseRule", 1))`.
    3. Assert result is `True`.

  **test_match_false_for_other_rule**
  - logic:
    1. Create `LowerCamelCaseEndpointName()`.
    2. Call `match(_finding("WidgetIdLowerCamelCaseRule", 1))`.
    3. Assert result is `False`.

  **test_apply_converts_PascalCase_name_to_lowerCamelCase**
  - logic:
    1. source = `'  {"name": "GetUser", "type": "inbound"}\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'GetUser' doesn't follow naming conventions")`
    3. result = `LowerCamelCaseEndpointName().apply(finding, source)`
    4. Assert `result is not None`.
    5. Assert `'"name": "getUser"'` is in `result.fixed_content`.
    6. Assert `result.confidence == Confidence.HIGH`.

  **test_apply_converts_snake_case_name_to_lowerCamelCase**
  - logic:
    1. source = `'  {"name": "get_user"}\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'get_user' doesn't follow naming conventions")`
    3. result = `LowerCamelCaseEndpointName().apply(finding, source)`
    4. Assert `result is not None`.
    5. Assert `'"name": "getUser"'` is in `result.fixed_content`.

  **test_apply_converts_kebab_case_name_to_lowerCamelCase**
  - logic:
    1. source = `'  {"name": "get-user"}\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="'get-user' doesn't follow naming conventions")`
    3. result = `LowerCamelCaseEndpointName().apply(finding, source)`
    4. Assert `result is not None`.
    5. Assert `'"name": "getUser"'` is in `result.fixed_content`.

  **test_apply_returns_none_when_line_zero**
  - logic:
    1. finding = `_finding("EndpointNameLowerCamelCaseRule", 0, message="'GetUser' doesn't follow naming conventions")`
    2. Assert `LowerCamelCaseEndpointName().apply(finding, '{"name": "GetUser"}\n') is None`.

  **test_apply_returns_none_when_line_exceeds_content**
  - logic:
    1. finding = `_finding("EndpointNameLowerCamelCaseRule", 99, message="'GetUser' doesn't follow naming conventions")`
    2. Assert `LowerCamelCaseEndpointName().apply(finding, '{"name": "GetUser"}\n') is None`.

  **test_apply_returns_none_when_message_does_not_match**
  - logic:
    1. source = `'{"name": "GetUser"}\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="some unrelated message")`
    3. Assert `LowerCamelCaseEndpointName().apply(finding, source) is None`.

  **test_apply_returns_none_when_name_field_not_on_line**
  - logic:
    1. source = `'"type": "inbound"\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'GetUser' doesn't follow naming conventions")`
    3. Assert `LowerCamelCaseEndpointName().apply(finding, source) is None`.
    - reason: `field_re` for `"name": "GetUser"` does not match the target line.

  **test_apply_returns_none_when_all_caps_no_separator**
  - logic:
    1. source = `'{"name": "GETUSER"}\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="'GETUSER' doesn't follow naming conventions")`
    3. Assert `LowerCamelCaseEndpointName().apply(finding, source) is None`.
    - reason: `_to_lower_camel_case("GETUSER")` returns None.

  **test_apply_returns_none_when_name_already_lower_camel**
  - logic:
    1. source = `'{"name": "getUser"}\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="'getUser' doesn't follow naming conventions")`
    3. Assert `LowerCamelCaseEndpointName().apply(finding, source) is None`.
    - reason: `fixed_name == invalid_name` triggers return None.

  **test_apply_fix_result_fields**
  - logic:
    1. source = `'{"name": "GetUser"}\n'`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1, message="Endpoint 'GetUser' doesn't follow naming conventions")`
    3. result = `LowerCamelCaseEndpointName().apply(finding, source)`
    4. Assert `isinstance(result, FixResult)`.
    5. Assert `result.finding == finding`.
    6. Assert `result.original_content == source`.
    7. Assert `result.confidence == Confidence.HIGH`.

#### Class: TestAddFailOnStatusCodes

- signature: `class TestAddFailOnStatusCodes`

  **test_match_true_for_EndpointFailOnStatusCodesRule**
  - logic:
    1. Create `AddFailOnStatusCodes()`.
    2. Call `match(_finding("EndpointFailOnStatusCodesRule", 1))`.
    3. Assert result is `True`.

  **test_match_false_for_other_rule**
  - logic:
    1. Create `AddFailOnStatusCodes()`.
    2. Call `match(_finding("WidgetIdLowerCamelCaseRule", 1))`.
    3. Assert result is `False`.

  **test_apply_adds_field_to_inbound_endpoint_when_missing**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Assert `result is not None`.
    5. Parse `result.fixed_content` as JSON. Call `data`.
    6. ep = `data["inboundEndpoints"][0]`
    7. Assert `"failOnStatusCodes"` in `ep`.
    8. codes = `{e["code"] for e in ep["failOnStatusCodes"]}`
    9. Assert `codes == {400, 403}`.
    10. Assert `result.confidence == Confidence.HIGH`.

  **test_apply_adds_field_to_outbound_endpoint_when_missing**
  - logic:
    1. source_content = `json.dumps({"outboundEndpoints": [{"name": "saveRecord"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'saveRecord' is missing required 'failOnStatusCodes' field")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Assert `result is not None`.
    5. Parse `result.fixed_content` as JSON.
    6. ep = `data["outboundEndpoints"][0]`
    7. Assert `"failOnStatusCodes"` in ep.
    8. codes = `{e["code"] for e in ep["failOnStatusCodes"]}`
    9. Assert `codes == {400, 403}`.

  **test_apply_adds_field_to_seed_endpoint_when_missing**
  - logic:
    1. source_content = `json.dumps({"seed": {"endPoints": [{"name": "fetchData"}]}}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'fetchData' is missing required 'failOnStatusCodes' field")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Assert `result is not None`.
    5. Parse `result.fixed_content` as JSON.
    6. ep = `data["seed"]["endPoints"][0]`
    7. Assert `"failOnStatusCodes"` in ep.
    8. codes = `{e["code"] for e in ep["failOnStatusCodes"]}`
    9. Assert `codes == {400, 403}`.

  **test_apply_adds_missing_single_code_to_existing_field**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser", "failOnStatusCodes": [{"code": 400}]}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required status codes: 403.")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Assert `result is not None`.
    5. Parse `result.fixed_content` as JSON.
    6. ep = `data["inboundEndpoints"][0]`
    7. codes = `{e["code"] for e in ep["failOnStatusCodes"]}`
    8. Assert `codes == {400, 403}`.

  **test_apply_adds_multiple_missing_codes_via_codes_pattern**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required status codes: 400, 403.")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Assert `result is not None`.
    5. Parse `result.fixed_content` as JSON.
    6. codes = `{e["code"] for e in data["inboundEndpoints"][0]["failOnStatusCodes"]}`
    7. Assert `codes == {400, 403}`.

  **test_apply_returns_none_when_json_invalid**
  - logic:
    1. source_content = `"not valid json"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")`
    3. Assert `AddFailOnStatusCodes().apply(finding, source_content) is None`.

  **test_apply_returns_none_when_message_matches_neither_pattern**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="something completely unrelated")`
    3. Assert `AddFailOnStatusCodes().apply(finding, source_content) is None`.

  **test_apply_returns_none_when_endpoint_name_not_found_in_json**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'notExist' is missing required 'failOnStatusCodes' field")`
    3. Assert `AddFailOnStatusCodes().apply(finding, source_content) is None`.

  **test_apply_output_is_indented_with_2_spaces_and_trailing_newline**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Assert `result is not None`.
    5. Assert `result.fixed_content.endswith("\n")`.
    6. lines = `result.fixed_content.splitlines()`
    7. Assert any line that is not the first/last starts with `"  "` (2-space indent).
    - note: confirm by checking `lines[1].startswith("  ")` is True.

  **test_apply_codes_are_sorted_ascending_in_output**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Parse `result.fixed_content` as JSON.
    5. codes_list = `[e["code"] for e in data["inboundEndpoints"][0]["failOnStatusCodes"]]`
    6. Assert `codes_list == sorted(codes_list)`.
    7. Assert `codes_list == [400, 403]`.

  **test_apply_fix_result_fields**
  - logic:
    1. source_content = `json.dumps({"inboundEndpoints": [{"name": "getUser"}]}, indent=2) + "\n"`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1, message="endpoint 'getUser' is missing required 'failOnStatusCodes' field")`
    3. result = `AddFailOnStatusCodes().apply(finding, source_content)`
    4. Assert `isinstance(result, FixResult)`.
    5. Assert `result.finding == finding`.
    6. Assert `result.original_content == source_content`.
    7. Assert `result.confidence == Confidence.HIGH`.

#### Class: TestFixTemplateRegistryStructureFixes

- signature: `class TestFixTemplateRegistryStructureFixes`

  **test_registry_discovers_all_three_structure_fix_templates**
  - logic:
    1. registry = `FixTemplateRegistry()`
    2. types = `{type(t).__name__ for t in registry.templates}`
    3. Assert `"LowerCamelCaseWidgetId"` in types.
    4. Assert `"LowerCamelCaseEndpointName"` in types.
    5. Assert `"AddFailOnStatusCodes"` in types.

  **test_registry_find_matching_returns_lower_camel_case_widget_id**
  - logic:
    1. registry = `FixTemplateRegistry()`
    2. finding = `_finding("WidgetIdLowerCamelCaseRule", 1)`
    3. matches = `registry.find_matching(finding)`
    4. Assert `len(matches) == 1`.
    5. Assert `isinstance(matches[0], LowerCamelCaseWidgetId)`.

  **test_registry_find_matching_returns_lower_camel_case_endpoint_name**
  - logic:
    1. registry = `FixTemplateRegistry()`
    2. finding = `_finding("EndpointNameLowerCamelCaseRule", 1)`
    3. matches = `registry.find_matching(finding)`
    4. Assert `len(matches) == 1`.
    5. Assert `isinstance(matches[0], LowerCamelCaseEndpointName)`.

  **test_registry_find_matching_returns_add_fail_on_status_codes**
  - logic:
    1. registry = `FixTemplateRegistry()`
    2. finding = `_finding("EndpointFailOnStatusCodesRule", 1)`
    3. matches = `registry.find_matching(finding)`
    4. Assert `len(matches) == 1`.
    5. Assert `isinstance(matches[0], AddFailOnStatusCodes)`.

  **test_registry_find_matching_returns_empty_for_unknown_rule**
  - logic:
    1. registry = `FixTemplateRegistry()`
    2. finding = `_finding("UnknownRule", 1)`
    3. matches = `registry.find_matching(finding)`
    4. Assert `matches == []`.

#### Class: TestFixTemplateABC

- signature: `class TestFixTemplateABC`

  **test_all_structure_fix_templates_are_FixTemplate_subclasses**
  - logic:
    1. For each cls in `[LowerCamelCaseWidgetId, LowerCamelCaseEndpointName, AddFailOnStatusCodes]`:
    2. Assert `issubclass(cls, FixTemplate) is True`.

  **test_all_structure_fix_templates_have_HIGH_confidence**
  - logic:
    1. For each cls in `[LowerCamelCaseWidgetId, LowerCamelCaseEndpointName, AddFailOnStatusCodes]`:
    2. instance = `cls()`
    3. Assert `instance.confidence == "HIGH"`.

#### Wiring / Integration
- The test file imports directly from `fix_templates.structure_fixes` and `fix_templates.base`.
- `pythonpath = ["."]` is already set in `pyproject.toml` so imports resolve from `agents/`.
- No changes required in any other file.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from fix_templates.structure_fixes import LowerCamelCaseWidgetId, LowerCamelCaseEndpointName, AddFailOnStatusCodes; print('import ok')"`
- lint: (no lint config present; skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_structure_fixes.py -v`
- smoke: Run the test above; all tests must pass with 0 failures.

## Constraints
- Do NOT modify `fix_templates/structure_fixes.py` -- it is already fully implemented.
- Do NOT modify `fix_templates/base.py`, `fix_templates/__init__.py`, `src/models.py`, or any other existing file.
- Do NOT modify `IMPL_PLAN.md`, `ARCHITECTURE.md`, or `CLAUDE.md`.
- Do NOT add new dependencies to `pyproject.toml`.
- The only file to create is `tests/test_structure_fixes.py`.
- Use `json.dumps(..., indent=2) + "\n"` (not raw strings) to construct source_content for AddFailOnStatusCodes tests -- this ensures the test JSON format exactly matches what the apply() method will compare against.
- The `_finding()` helper in this test file must include a `message` parameter (default `"test"`) so structure_fixes tests can pass custom messages. Do not reuse the signature from `test_script_fixes.py` (that file's helper has no message parameter).
