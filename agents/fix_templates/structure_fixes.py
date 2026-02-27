"""HIGH-confidence fix templates for Workday Extend structural violations."""

from __future__ import annotations

import json
import logging
import re
from typing import Literal

from fix_templates.base import FixTemplate
from src.models import Confidence, Finding, FixResult

logger = logging.getLogger(__name__)

_LOWER_CAMEL_RE: re.Pattern[str] = re.compile(r'^[a-z][a-zA-Z0-9]*$')
_PASCAL_RE: re.Pattern[str] = re.compile(r'^[A-Z][a-zA-Z0-9]*$')


def _to_lower_camel_case(value: str) -> str | None:
    """Convert an identifier string to lowerCamelCase.

    Args:
        value: The identifier to convert.

    Returns:
        The lowerCamelCase form, or None if the transformation cannot be applied safely.

    Returns None when:
    - value is an empty string
    - value contains '<' (e.g. '<% ... %>' template syntax)
    - value contains separators ('_' or '-') but a part after splitting contains
      non-alphanumeric characters
    - value is all-uppercase with no separators (e.g. 'MYWIDGET')
    - value starts with a digit (the lowerCamelCase result would fail _LOWER_CAMEL_RE)
    - value matches no recognized form (no separators, not PascalCase, not already lowerCamelCase)

    Note: for separator-containing values, the entire value is lowercased before
    splitting, so intermediate camelCase is discarded. For example,
    'myWidget_extra' becomes 'mywidgetExtra' (the 'W' in Widget is lost).
    """
    if value == "":
        return None
    if "<%" in value:
        return None
    if _LOWER_CAMEL_RE.match(value):
        return value
    if "_" in value or "-" in value:
        parts = re.split(r'[_\-]+', value.lower())
        non_empty = [p for p in parts if p]
        if not non_empty:
            return None
        for p in non_empty:
            if not re.match(r'^[a-z0-9]+$', p):
                return None
        result = non_empty[0] + "".join(p.capitalize() for p in non_empty[1:])
        return result if _LOWER_CAMEL_RE.match(result) else None
    if _PASCAL_RE.match(value):
        has_lower = any(c.islower() for c in value[1:])
        if not has_lower:
            return None
        result = value[0].lower() + value[1:]
        return result if _LOWER_CAMEL_RE.match(result) else None
    return None


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

    def match(self, finding: Finding) -> bool:
        """Return True if this template handles WidgetIdLowerCamelCaseRule violations."""
        return finding.rule_id == "WidgetIdLowerCamelCaseRule"

    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Replace the invalid widget 'id' value on finding.line with its lowerCamelCase form."""
        if finding.line == 0:
            return None
        lines: list[str] = source_content.splitlines(keepends=True)
        if finding.line > len(lines):
            return None
        target_idx: int = finding.line - 1
        target_line: str = lines[target_idx]
        msg_match = self._MSG_RE.search(finding.message)
        if msg_match is None:
            return None
        invalid_id: str = msg_match.group(1)
        if "<" in invalid_id:
            return None
        fixed_id = _to_lower_camel_case(invalid_id)
        if fixed_id is None:
            return None
        if fixed_id == invalid_id:
            return None
        field_re = re.compile(r'"id"\s*:\s*"' + re.escape(invalid_id) + r'"')
        modified_line: str = field_re.sub(f'"id": "{fixed_id}"', target_line)
        if modified_line == target_line:
            return None
        lines[target_idx] = modified_line
        return FixResult(
            finding=finding,
            original_content=source_content,
            fixed_content="".join(lines),
            confidence=Confidence.HIGH,
        )


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

    def match(self, finding: Finding) -> bool:
        """Return True if this template handles EndpointNameLowerCamelCaseRule violations."""
        return finding.rule_id == "EndpointNameLowerCamelCaseRule"

    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Replace the invalid endpoint 'name' value on finding.line with its lowerCamelCase form."""
        if finding.line == 0:
            return None
        lines: list[str] = source_content.splitlines(keepends=True)
        if finding.line > len(lines):
            return None
        target_idx: int = finding.line - 1
        target_line: str = lines[target_idx]
        msg_match = self._MSG_RE.search(finding.message)
        if msg_match is None:
            return None
        invalid_name: str = msg_match.group(1)
        fixed_name = _to_lower_camel_case(invalid_name)
        if fixed_name is None:
            return None
        if fixed_name == invalid_name:
            return None
        field_re = re.compile(r'"name"\s*:\s*"' + re.escape(invalid_name) + r'"')
        modified_line: str = field_re.sub(f'"name": "{fixed_name}"', target_line)
        if modified_line == target_line:
            return None
        lines[target_idx] = modified_line
        return FixResult(
            finding=finding,
            original_content=source_content,
            fixed_content="".join(lines),
            confidence=Confidence.HIGH,
        )


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

    def match(self, finding: Finding) -> bool:
        """Return True if this template handles EndpointFailOnStatusCodesRule violations."""
        return finding.rule_id == "EndpointFailOnStatusCodesRule"

    def _extract_endpoint_and_codes(self, message: str) -> tuple[str, set[int]] | None:
        """Parse the finding message to extract the endpoint name and missing codes.

        Args:
            message: The finding message string.

        Returns:
            A tuple of (endpoint_name, missing_codes) or None if neither pattern matched.
        """
        m1 = self._MISSING_FIELD_RE.search(message)
        if m1 is not None:
            endpoint_name: str = m1.group(1)
            missing_codes: set[int] = {400, 403}
            return (endpoint_name, missing_codes)
        m2 = self._MISSING_CODES_RE.search(message)
        if m2 is not None:
            endpoint_name = m2.group(1)
            tokens = re.split(r'[,\s]+', m2.group(2).strip())
            missing_codes = set()
            for token in tokens:
                if not token:
                    continue
                try:
                    missing_codes.add(int(token))
                except ValueError:
                    continue
            if not missing_codes:
                return None
            return (endpoint_name, missing_codes)
        return None

    def _fix_endpoint_in_data(self, data: dict, endpoint_name: str, missing_codes: set[int]) -> bool:
        """Traverse all endpoint arrays in the parsed JSON, find the endpoint, and add missing codes.

        Args:
            data: The parsed JSON dict.
            endpoint_name: The endpoint name to find.
            missing_codes: The set of status codes to add.

        Returns:
            True if any modification was made, False otherwise.
        """
        for key in ("inboundEndpoints", "outboundEndpoints"):
            ep_list = data.get(key)
            if not isinstance(ep_list, list):
                continue
            for ep in ep_list:
                if not isinstance(ep, dict):
                    continue
                if ep.get("name") != endpoint_name:
                    continue
                self._add_missing_codes(ep, missing_codes)
                return True
        seed = data.get("seed")
        if isinstance(seed, dict):
            ep_list = seed.get("endPoints")
            if isinstance(ep_list, list):
                for ep in ep_list:
                    if not isinstance(ep, dict):
                        continue
                    if ep.get("name") != endpoint_name:
                        continue
                    self._add_missing_codes(ep, missing_codes)
                    return True
        return False

    def _add_missing_codes(self, ep: dict, missing_codes: set[int]) -> None:
        """Add missing status codes to the endpoint dict's failOnStatusCodes list in place.

        Args:
            ep: The endpoint dict to modify.
            missing_codes: The set of status codes to add.
        """
        if "failOnStatusCodes" not in ep:
            ep["failOnStatusCodes"] = []
        existing_codes: set[int] = set()
        for entry in ep["failOnStatusCodes"]:
            if isinstance(entry, dict) and "code" in entry:
                try:
                    existing_codes.add(int(entry["code"]))
                except (ValueError, TypeError):
                    continue
        for code in sorted(missing_codes):
            if code not in existing_codes:
                ep["failOnStatusCodes"].append({"code": code})
        ep["failOnStatusCodes"].sort(key=lambda e: int(e.get("code", 0)) if isinstance(e, dict) else 0)

    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Parse the JSON file, locate the endpoint, add missing failOnStatusCodes entries."""
        try:
            data = json.loads(source_content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON for failOnStatusCodes fix: %s", finding.file_path)
            return None
        extracted = self._extract_endpoint_and_codes(finding.message)
        if extracted is None:
            return None
        endpoint_name, missing_codes = extracted
        modified = self._fix_endpoint_in_data(data, endpoint_name, missing_codes)
        if not modified:
            return None
        fixed_content = json.dumps(data, indent=2) + "\n"
        if fixed_content == source_content:
            return None
        return FixResult(
            finding=finding,
            original_content=source_content,
            fixed_content=fixed_content,
            confidence=Confidence.HIGH,
        )
