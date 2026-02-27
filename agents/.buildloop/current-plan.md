# Plan: P6.3

## Dependencies
- list: []
- commands: []  # no new dependencies; uses stdlib re, json, logging already in use

## File Operations (in execution order)

### 1. CREATE fix_templates/structure_fixes.py
- operation: CREATE
- reason: P6.3 requires three HIGH-confidence fix templates for structural Workday Extend violations

#### Imports / Dependencies
```python
from __future__ import annotations
import json
import logging
import re
from typing import Literal

from fix_templates.base import FixTemplate
from src.models import Confidence, Finding, FixResult
```

#### Module-level constants and helper
```python
logger = logging.getLogger(__name__)

_LOWER_CAMEL_RE: re.Pattern[str] = re.compile(r'^[a-z][a-zA-Z0-9]*$')
_PASCAL_RE: re.Pattern[str] = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
```

#### Helper function (module-level, private)
- signature: `def _to_lower_camel_case(value: str) -> str | None:`
  - purpose: Convert an identifier string to lowerCamelCase, returning None when the transformation is ambiguous or unsafe.
  - logic:
    1. If `value` is empty string, return `None`.
    2. If `'<%'` in `value`, return `None` (script syntax — skip).
    3. If `_LOWER_CAMEL_RE.match(value)` is truthy, return `value` as-is (already valid).
    4. If `'_'` in `value` or `'-'` in `value`: enter separator branch.
       a. Split `value.lower()` on regex `r'[_\-]+'` into `parts`.
       b. Filter empty strings: `non_empty = [p for p in parts if p]`.
       c. If `non_empty` is empty, return `None`.
       d. Verify each part in `non_empty` matches `r'^[a-z0-9]+$'`; if any does not match, return `None`.
       e. Build result: `non_empty[0] + ''.join(p.capitalize() for p in non_empty[1:])`.
       f. Return `result` if `_LOWER_CAMEL_RE.match(result)` else `None`.
    5. If `_PASCAL_RE.match(value)` is truthy (starts uppercase, rest alphanumeric, no separators):
       a. Check if any character in `value[1:]` is lowercase; assign to `has_lower`.
       b. If `not has_lower`, return `None` (ALL_CAPS without separators — ambiguous).
       c. Build `result = value[0].lower() + value[1:]`.
       d. Return `result` if `_LOWER_CAMEL_RE.match(result)` else `None`.
    6. Return `None` (starts with digit, contains non-alphanumeric other than handled separators, or other unhandled form).
  - returns: `str | None` — the lowerCamelCase form, or None if transformation is ambiguous.
  - error handling: no exceptions raised; all failure modes return None.

---

### Class 1: LowerCamelCaseWidgetId

#### Class definition
```python
class LowerCamelCaseWidgetId(FixTemplate):
    """Convert widget 'id' field values to lowerCamelCase.

    Operates on the line identified by finding.line in PMD and POD JSON files.
    Extracts the invalid ID from the finding message, computes the lowerCamelCase
    form, then substitutes the 'id' field value on that line using a targeted regex.

    Returns None when:
    - finding.line is 0 (no line info from parent tool)
    - finding.line exceeds the number of lines in source_content
    - the finding message does not match the expected format (cannot extract invalid ID)
    - the extracted invalid ID contains '<' (script syntax -- too complex to transform safely)
    - _to_lower_camel_case() returns None (ambiguous or unsafe transformation)
    - the 'id' field with the extracted invalid ID is not found on the target line
    """

    confidence: Literal["HIGH"] = "HIGH"

    _MSG_RE: re.Pattern[str] = re.compile(r"has invalid name '([^']+)'")
```

#### Functions
- signature: `def match(self, finding: Finding) -> bool:`
  - purpose: Return True if this template handles WidgetIdLowerCamelCaseRule violations.
  - logic:
    1. Return `finding.rule_id == "WidgetIdLowerCamelCaseRule"`.
  - returns: `bool`
  - error handling: none

- signature: `def apply(self, finding: Finding, source_content: str) -> FixResult | None:`
  - purpose: Replace the invalid widget 'id' value on finding.line with its lowerCamelCase form.
  - logic:
    1. If `finding.line == 0`, return `None`.
    2. Split `source_content` into `lines` via `source_content.splitlines(keepends=True)`.
    3. If `finding.line > len(lines)`, return `None`.
    4. Assign `target_idx = finding.line - 1`.
    5. Assign `target_line = lines[target_idx]`.
    6. Match `self._MSG_RE` against `finding.message`; assign to `msg_match`. If `msg_match` is `None`, return `None`.
    7. Assign `invalid_id = msg_match.group(1)`.
    8. If `'<'` in `invalid_id`, return `None` (script syntax).
    9. Call `_to_lower_camel_case(invalid_id)`; assign to `fixed_id`. If `fixed_id` is `None`, return `None`.
    10. If `fixed_id == invalid_id`, return `None` (no change needed).
    11. Build `field_re = re.compile(r'"id"\s*:\s*"' + re.escape(invalid_id) + r'"')`.
    12. Apply `field_re.sub(f'"id": "{fixed_id}"', target_line)`; assign to `modified_line`.
    13. If `modified_line == target_line`, return `None` (pattern not found on this line).
    14. Assign `lines[target_idx] = modified_line`.
    15. Return `FixResult(finding=finding, original_content=source_content, fixed_content="".join(lines), confidence=Confidence.HIGH)`.
  - returns: `FixResult | None`
  - error handling: no exceptions raised; all failure modes return None.

---

### Class 2: LowerCamelCaseEndpointName

#### Class definition
```python
class LowerCamelCaseEndpointName(FixTemplate):
    """Convert endpoint 'name' field values to lowerCamelCase.

    Operates on the line identified by finding.line in PMD and POD JSON files.
    Extracts the invalid endpoint name from the finding message, computes the
    lowerCamelCase form, then substitutes the 'name' field value on that line.

    Returns None when:
    - finding.line is 0 (no line info from parent tool)
    - finding.line exceeds the number of lines in source_content
    - the finding message does not match the expected format (cannot extract name)
    - _to_lower_camel_case() returns None (ambiguous or unsafe transformation)
    - the 'name' field with the extracted invalid name is not found on the target line
    """

    confidence: Literal["HIGH"] = "HIGH"

    _MSG_RE: re.Pattern[str] = re.compile(r"^[^']*'([^']+)' doesn't follow naming conventions")
```

#### Functions
- signature: `def match(self, finding: Finding) -> bool:`
  - purpose: Return True if this template handles EndpointNameLowerCamelCaseRule violations.
  - logic:
    1. Return `finding.rule_id == "EndpointNameLowerCamelCaseRule"`.
  - returns: `bool`
  - error handling: none

- signature: `def apply(self, finding: Finding, source_content: str) -> FixResult | None:`
  - purpose: Replace the invalid endpoint 'name' value on finding.line with its lowerCamelCase form.
  - logic:
    1. If `finding.line == 0`, return `None`.
    2. Split `source_content` into `lines` via `source_content.splitlines(keepends=True)`.
    3. If `finding.line > len(lines)`, return `None`.
    4. Assign `target_idx = finding.line - 1`.
    5. Assign `target_line = lines[target_idx]`.
    6. Match `self._MSG_RE` against `finding.message`; assign to `msg_match`. If `None`, return `None`.
    7. Assign `invalid_name = msg_match.group(1)`.
    8. Call `_to_lower_camel_case(invalid_name)`; assign to `fixed_name`. If `None`, return `None`.
    9. If `fixed_name == invalid_name`, return `None`.
    10. Build `field_re = re.compile(r'"name"\s*:\s*"' + re.escape(invalid_name) + r'"')`.
    11. Apply `field_re.sub(f'"name": "{fixed_name}"', target_line)`; assign to `modified_line`.
    12. If `modified_line == target_line`, return `None`.
    13. Assign `lines[target_idx] = modified_line`.
    14. Return `FixResult(finding=finding, original_content=source_content, fixed_content="".join(lines), confidence=Confidence.HIGH)`.
  - returns: `FixResult | None`
  - error handling: no exceptions raised; all failure modes return None.

---

### Class 3: AddFailOnStatusCodes

#### Class definition
```python
class AddFailOnStatusCodes(FixTemplate):
    """Add or complete the 'failOnStatusCodes' field on endpoints missing codes 400 and/or 403.

    Uses JSON parsing (not regex) to locate the endpoint by name in any of:
    - top-level 'inboundEndpoints' array (PMD)
    - top-level 'outboundEndpoints' array (PMD)
    - 'seed.endPoints' array (POD)

    Handles two finding subtypes:
    1. Missing entire field: message contains "is missing required 'failOnStatusCodes' field"
       => adds failOnStatusCodes with codes 400 and 403.
    2. Missing specific codes: message contains "is missing required status codes: <N, ...>"
       => adds only the listed missing codes to the existing array.

    Serializes the modified JSON with json.dumps(data, indent=2) + newline, which
    normalizes whitespace. This is acceptable for Workday Extend JSON files.

    Returns None when:
    - source_content cannot be parsed as JSON (json.JSONDecodeError)
    - the finding message matches neither expected format (cannot extract endpoint name)
    - the endpoint name is not found in any endpoint array in the parsed JSON
    - the fixed content is identical to source_content (nothing changed)
    """

    confidence: Literal["HIGH"] = "HIGH"

    _MISSING_FIELD_RE: re.Pattern[str] = re.compile(
        r"endpoint '([^']+)' is missing required 'failOnStatusCodes' field"
    )
    _MISSING_CODES_RE: re.Pattern[str] = re.compile(
        r"endpoint '([^']+)' is missing required status codes: ([0-9, ]+)\."
    )
```

#### Functions
- signature: `def match(self, finding: Finding) -> bool:`
  - purpose: Return True if this template handles EndpointFailOnStatusCodesRule violations.
  - logic:
    1. Return `finding.rule_id == "EndpointFailOnStatusCodesRule"`.
  - returns: `bool`
  - error handling: none

- signature: `def _extract_endpoint_and_codes(self, message: str) -> tuple[str, set[int]] | None:`
  - purpose: Parse the finding message to extract the endpoint name and the set of codes that need to be added.
  - logic:
    1. Try matching `self._MISSING_FIELD_RE` against `message`; assign to `m1`.
    2. If `m1` is not None:
       a. Assign `endpoint_name = m1.group(1)`.
       b. Assign `missing_codes = {400, 403}`.
       c. Return `(endpoint_name, missing_codes)`.
    3. Try matching `self._MISSING_CODES_RE` against `message`; assign to `m2`.
    4. If `m2` is not None:
       a. Assign `endpoint_name = m2.group(1)`.
       b. Split `m2.group(2)` on `r'[,\s]+'` and strip; filter non-empty strings; convert each to int. Assign to `missing_codes` as a `set[int]`.
       c. If `missing_codes` is empty, return `None`.
       d. Return `(endpoint_name, missing_codes)`.
    5. Return `None` (neither pattern matched).
  - returns: `tuple[str, set[int]] | None`
  - error handling: if `int(code_str)` raises ValueError, skip that token.

- signature: `def _fix_endpoint_in_data(self, data: dict, endpoint_name: str, missing_codes: set[int]) -> bool:`
  - purpose: Traverse all endpoint arrays in the parsed JSON dict, find the endpoint by name, and add missing codes. Returns True if any modification was made.
  - logic:
    1. For each key in `("inboundEndpoints", "outboundEndpoints")`:
       a. Assign `ep_list = data.get(key)`.
       b. If `ep_list` is not a list, continue.
       c. For each `ep` in `ep_list`:
          - If not isinstance(ep, dict), continue.
          - If `ep.get("name") != endpoint_name`, continue.
          - Call `self._add_missing_codes(ep, missing_codes)`.
          - Return `True`.
    2. Assign `seed = data.get("seed")`.
    3. If `seed` is a dict:
       a. Assign `ep_list = seed.get("endPoints")`.
       b. If `ep_list` is a list:
          - For each `ep` in `ep_list`:
            - If not isinstance(ep, dict), continue.
            - If `ep.get("name") != endpoint_name`, continue.
            - Call `self._add_missing_codes(ep, missing_codes)`.
            - Return `True`.
    4. Return `False` (endpoint not found in any array).
  - returns: `bool`
  - error handling: none; uses only safe attribute access.

- signature: `def _add_missing_codes(self, ep: dict, missing_codes: set[int]) -> None:`
  - purpose: Add missing status codes to the endpoint dict's failOnStatusCodes list in place.
  - logic:
    1. If `"failOnStatusCodes"` not in `ep`, assign `ep["failOnStatusCodes"] = []`.
    2. Build `existing_codes` as a set: iterate `ep["failOnStatusCodes"]`; for each entry that is a dict with key `"code"`, try `int(entry["code"])` and add to the set; skip on ValueError/TypeError.
    3. For each `code` in `sorted(missing_codes)`:
       a. If `code` not in `existing_codes`, append `{"code": code}` to `ep["failOnStatusCodes"]`.
    4. Sort `ep["failOnStatusCodes"]` by `lambda entry: entry.get("code", 0)`.
  - returns: `None`
  - error handling: int conversion errors on existing codes are silently skipped.

- signature: `def apply(self, finding: Finding, source_content: str) -> FixResult | None:`
  - purpose: Parse the JSON file, locate the endpoint, add the missing failOnStatusCodes entries, and return the fixed content.
  - logic:
    1. Try `data = json.loads(source_content)`; if `json.JSONDecodeError` is raised, log a warning and return `None`.
    2. Call `self._extract_endpoint_and_codes(finding.message)`; assign to `extracted`. If `None`, return `None`.
    3. Assign `endpoint_name, missing_codes = extracted`.
    4. Call `self._fix_endpoint_in_data(data, endpoint_name, missing_codes)`; assign to `modified`. If `not modified`, return `None`.
    5. Assign `fixed_content = json.dumps(data, indent=2) + "\n"`.
    6. If `fixed_content == source_content`, return `None`.
    7. Return `FixResult(finding=finding, original_content=source_content, fixed_content=fixed_content, confidence=Confidence.HIGH)`.
  - returns: `FixResult | None`
  - error handling: catches `json.JSONDecodeError` in step 1 only; logs a warning with `logger.warning(...)` before returning None.

---

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from fix_templates.structure_fixes import LowerCamelCaseWidgetId, LowerCamelCaseEndpointName, AddFailOnStatusCodes; print('imports OK')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run ruff check fix_templates/structure_fixes.py`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -q`
- smoke: Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
from fix_templates.base import FixTemplateRegistry
r = FixTemplateRegistry()
names = [type(t).__name__ for t in r.templates]
assert 'LowerCamelCaseWidgetId' in names, names
assert 'LowerCamelCaseEndpointName' in names, names
assert 'AddFailOnStatusCodes' in names, names
print('registry OK:', names)
"` and expect no assertion errors.

## Constraints
- Do NOT modify fix_templates/__init__.py, fix_templates/base.py, fix_templates/script_fixes.py, or any file in src/.
- Do NOT add any new package dependencies.
- Do NOT use json.dumps for LowerCamelCaseWidgetId or LowerCamelCaseEndpointName — those use line-targeted regex replacement to preserve source formatting.
- AddFailOnStatusCodes MUST use json.loads / json.dumps (not regex) for structural JSON modification.
- All three classes MUST have confidence: Literal["HIGH"] = "HIGH" as a class-level attribute.
- The module-level helper _to_lower_camel_case must NOT be a method on any class.
- Use [^']+ (not .*?) in all message-extraction regexes to avoid matching across single-quotes.
- The "id" field regex in LowerCamelCaseWidgetId must use re.escape(invalid_id) to handle special chars in the ID value.
- The "name" field regex in LowerCamelCaseEndpointName must use re.escape(invalid_name).
- Do NOT create a test file in this task — tests are deferred to P6.5.
