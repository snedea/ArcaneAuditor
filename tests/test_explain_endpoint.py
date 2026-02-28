"""
Tests for POST /api/explain endpoint.

All tests mock the Anthropic SDK so no real API calls are made.
"""
import json
import anthropic
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from web.server import (
    app,
    get_explain_system_prompt,
    parse_structured_explanation,
    EXPLAIN_PROMPT_PATH,
)

client = TestClient(app)

SAMPLE_FINDINGS = {
    "findings": [
        {
            "rule_id": "HardcodedWorkdayAPIRule",
            "severity": "ACTION",
            "message": "Hardcoded Workday API URL detected",
            "file_path": "test.pod",
            "line": 7,
        }
    ],
    "summary": {"total_findings": 1, "by_severity": {"action": 1, "advice": 0}},
}

# A valid structured JSON response matching the new prompt format
STRUCTURED_RESPONSE = json.dumps([
    {
        "index": 0,
        "explanation": "Hardcoded URLs break when environments change.",
        "suggestion": "Use a configuration variable instead.",
        "priority": "high",
    }
])


def _mock_api_response(text="## Explanation\nLooks good."):
    """Return a mock Anthropic API response."""
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


class TestParseStructuredExplanation:
    """Tests for parse_structured_explanation() helper."""

    def test_valid_json_array(self):
        raw = '[{"index": 0, "explanation": "Bad", "suggestion": "Fix it", "priority": "high"}]'
        result = parse_structured_explanation(raw)
        assert result is not None
        assert len(result) == 1
        assert result[0]["priority"] == "high"

    def test_code_fenced_json(self):
        raw = '```json\n[{"index": 0, "explanation": "x", "suggestion": "y", "priority": "low"}]\n```'
        result = parse_structured_explanation(raw)
        assert result is not None
        assert result[0]["priority"] == "low"

    def test_preamble_before_json(self):
        raw = 'Here is my analysis:\n\n[{"index": 0, "explanation": "x", "suggestion": "y", "priority": "medium"}]'
        result = parse_structured_explanation(raw)
        assert result is not None
        assert result[0]["index"] == 0

    def test_truncated_json_returns_none(self):
        raw = '[{"index": 0, "explanation": "x", "suggestion": "y"'
        result = parse_structured_explanation(raw)
        assert result is None

    def test_non_json_returns_none(self):
        raw = "## Priority Findings\n\n1. Fix the hardcoded URL."
        result = parse_structured_explanation(raw)
        assert result is None

    def test_empty_string_returns_none(self):
        result = parse_structured_explanation("")
        assert result is None

    def test_empty_array(self):
        result = parse_structured_explanation("[]")
        assert result == []

    def test_json_object_not_array_returns_none(self):
        raw = '{"index": 0, "explanation": "x"}'
        result = parse_structured_explanation(raw)
        assert result is None

    def test_code_fenced_without_lang(self):
        raw = '```\n[{"index": 0, "explanation": "x", "suggestion": "y", "priority": "high"}]\n```'
        result = parse_structured_explanation(raw)
        assert result is not None

    def test_missing_required_field_returns_none(self):
        """Items missing any of index/explanation/suggestion/priority are rejected."""
        raw = '[{"index": 0, "explanation": "x", "suggestion": "y"}]'  # missing priority
        result = parse_structured_explanation(raw)
        assert result is None

    def test_extra_fields_accepted(self):
        """Items with extra fields beyond the required set are still accepted."""
        raw = '[{"index": 0, "explanation": "x", "suggestion": "y", "priority": "high", "extra": true}]'
        result = parse_structured_explanation(raw)
        assert result is not None
        assert result[0]["extra"] is True

    def test_non_dict_item_returns_none(self):
        """Array containing a non-dict item is rejected."""
        raw = '[{"index": 0, "explanation": "x", "suggestion": "y", "priority": "low"}, "oops"]'
        result = parse_structured_explanation(raw)
        assert result is None

    def test_wrong_index_type_returns_none(self):
        """index must be an int, not a string."""
        raw = '[{"index": "zero", "explanation": "x", "suggestion": "y", "priority": "high"}]'
        result = parse_structured_explanation(raw)
        assert result is None

    def test_wrong_explanation_type_returns_none(self):
        """explanation must be a string."""
        raw = '[{"index": 0, "explanation": 42, "suggestion": "y", "priority": "high"}]'
        result = parse_structured_explanation(raw)
        assert result is None

    def test_invalid_priority_value_returns_none(self):
        """priority must be high/medium/low."""
        raw = '[{"index": 0, "explanation": "x", "suggestion": "y", "priority": "urgent"}]'
        result = parse_structured_explanation(raw)
        assert result is None

    def test_valid_priorities_accepted(self):
        """All three valid priority values are accepted."""
        for p in ("high", "medium", "low"):
            raw = f'[{{"index": 0, "explanation": "x", "suggestion": "y", "priority": "{p}"}}]'
            result = parse_structured_explanation(raw)
            assert result is not None, f"priority={p} should be accepted"


class TestExplainEndpoint:
    """Tests for /api/explain."""

    @patch("web.server._get_anthropic_client")
    def test_structured_response(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(STRUCTURED_RESPONSE)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "structured"
        assert "explanations" in body
        assert len(body["explanations"]) == 1
        assert body["explanations"][0]["priority"] == "high"
        assert "findings_order" in body
        assert body["findings_order"][0]["rule_id"] == "HardcodedWorkdayAPIRule"

    @patch("web.server._get_anthropic_client")
    def test_markdown_fallback(self, mock_get_client):
        """Non-JSON output falls back to markdown format."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response("## Explanation\nLooks good.")
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "markdown"
        assert "explanation" in body
        assert "Explanation" in body["explanation"]

    @patch("web.server._get_anthropic_client")
    def test_api_called_with_correct_params(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(STRUCTURED_RESPONSE)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 1.0
        assert "Finding #0" in call_kwargs["messages"][0]["content"]
        assert len(call_kwargs["system"]) > 20

    @patch("web.server._get_anthropic_client")
    def test_model_env_override(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(STRUCTURED_RESPONSE)
        mock_get_client.return_value = mock_client

        with patch.dict("os.environ", {"LLM_MODEL": "claude-haiku-4-5"}):
            resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5"

    def test_empty_findings_rejected(self):
        resp = client.post("/api/explain", json={"findings": {}})
        assert resp.status_code == 400
        assert "No findings" in resp.json()["detail"]

    def test_missing_findings_field(self):
        resp = client.post("/api/explain", json={})
        assert resp.status_code == 422  # Pydantic validation error

    @patch("web.server._get_anthropic_client")
    def test_empty_response(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response("")
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 502
        assert "empty response" in resp.json()["detail"]

    @patch("web.server._get_anthropic_client")
    def test_auth_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="invalid key", response=MagicMock(status_code=401), body={}
        )
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 503
        assert "API key" in resp.json()["detail"]

    @patch("web.server._get_anthropic_client")
    def test_timeout(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APITimeoutError(request=MagicMock())
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 504
        assert "timed out" in resp.json()["detail"]

    @patch("web.server._get_anthropic_client")
    def test_markdown_response_is_stripped(self, mock_get_client):
        """Verify leading/trailing whitespace is stripped from markdown fallback."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response("\n\n  Some explanation  \n\n")
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "markdown"
        assert body["explanation"] == "Some explanation"

    @patch("web.server._get_anthropic_client")
    def test_format_field_always_present(self, mock_get_client):
        """Both structured and markdown responses include a format field."""
        mock_client = MagicMock()

        # Markdown case
        mock_client.messages.create.return_value = _mock_api_response("## Explanation\nLooks good.")
        mock_get_client.return_value = mock_client
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert "format" in resp.json()

        # Structured case
        mock_client.messages.create.return_value = _mock_api_response(STRUCTURED_RESPONSE)
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert "format" in resp.json()


class TestPromptLoading:
    """Tests for mtime-cached prompt file loading."""

    def test_loads_from_file(self):
        prompt = get_explain_system_prompt()
        assert "Workday Extend" in prompt
        assert "JSON" in prompt  # new prompt mentions JSON

    def test_prompt_file_exists(self):
        assert EXPLAIN_PROMPT_PATH.exists(), f"Prompt file missing: {EXPLAIN_PROMPT_PATH}"

    def test_fallback_on_missing_file(self):
        with patch.object(EXPLAIN_PROMPT_PATH.__class__, "stat", side_effect=FileNotFoundError):
            prompt = get_explain_system_prompt()
            assert "code reviewer" in prompt  # fallback prompt
            assert "JSON" in prompt  # fallback now also requests JSON

    @patch("web.server._get_anthropic_client")
    def test_prompt_passed_to_api(self, mock_get_client):
        """Verify the file-loaded prompt reaches the API call."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(STRUCTURED_RESPONSE)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "JSON" in call_kwargs["system"]
