"""
Tests for POST /api/explain endpoint.

All tests mock subprocess.run so no real Claude CLI is needed.
"""
import json
import subprocess
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


def _mock_completed(stdout="## Explanation\nLooks good.", returncode=0, stderr=""):
    """Return a mock CompletedProcess for subprocess.run."""
    cp = MagicMock(spec=subprocess.CompletedProcess)
    cp.stdout = stdout
    cp.stderr = stderr
    cp.returncode = returncode
    return cp


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

    @patch("web.server.subprocess.run", return_value=_mock_completed(stdout=STRUCTURED_RESPONSE))
    def test_structured_response(self, mock_run):
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "structured"
        assert "explanations" in body
        assert len(body["explanations"]) == 1
        assert body["explanations"][0]["priority"] == "high"
        assert "findings_order" in body
        assert body["findings_order"][0]["rule_id"] == "HardcodedWorkdayAPIRule"

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_markdown_fallback(self, mock_run):
        """Non-JSON output falls back to markdown format."""
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "markdown"
        assert "explanation" in body
        assert "Explanation" in body["explanation"]

    @patch("web.server.subprocess.run", return_value=_mock_completed(stdout=STRUCTURED_RESPONSE))
    def test_subprocess_called_correctly(self, mock_run):
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200

        # Verify subprocess was called with correct args
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == "claude"
        assert "--print" in cmd
        assert "--max-turns" in cmd
        assert "--system-prompt" in cmd
        assert kwargs["input"] is not None
        assert "Finding #0" in kwargs["input"]  # numbered format
        assert kwargs["timeout"] == 120

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_model_env_override(self, mock_run):
        with patch.dict("os.environ", {"LLM_MODEL": "claude-haiku-4-5"}):
            resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        cmd = mock_run.call_args[0][0]
        assert "claude-haiku-4-5" in cmd

    def test_empty_findings_rejected(self):
        resp = client.post("/api/explain", json={"findings": {}})
        assert resp.status_code == 400
        assert "No findings" in resp.json()["detail"]

    def test_missing_findings_field(self):
        resp = client.post("/api/explain", json={})
        assert resp.status_code == 422  # Pydantic validation error

    @patch(
        "web.server.subprocess.run",
        return_value=_mock_completed(returncode=1, stderr="auth failed"),
    )
    def test_nonzero_exit_code(self, mock_run):
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 502
        assert "auth failed" in resp.json()["detail"]

    @patch(
        "web.server.subprocess.run",
        return_value=_mock_completed(stdout="", returncode=0),
    )
    def test_empty_response(self, mock_run):
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 502
        assert "empty response" in resp.json()["detail"]

    @patch(
        "web.server.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=120),
    )
    def test_timeout(self, mock_run):
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 504
        assert "timed out" in resp.json()["detail"]

    @patch("web.server.subprocess.run", side_effect=FileNotFoundError())
    def test_cli_not_found(self, mock_run):
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 503
        assert "not available" in resp.json()["detail"]

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_markdown_response_is_stripped(self, mock_run):
        """Verify leading/trailing whitespace is stripped from markdown fallback."""
        mock_run.return_value = _mock_completed(stdout="\n\n  Some explanation  \n\n")
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "markdown"
        assert body["explanation"] == "Some explanation"

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_format_field_always_present(self, mock_run):
        """Both structured and markdown responses include a format field."""
        # Markdown case
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert "format" in resp.json()

        # Structured case
        mock_run.return_value = _mock_completed(stdout=STRUCTURED_RESPONSE)
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

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_prompt_passed_to_subprocess(self, mock_run):
        """Verify the file-loaded prompt reaches the subprocess command."""
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        cmd = mock_run.call_args[0][0]
        # Find the --system-prompt value
        sp_idx = cmd.index("--system-prompt")
        prompt_arg = cmd[sp_idx + 1]
        assert "JSON" in prompt_arg
