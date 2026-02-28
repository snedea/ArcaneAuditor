"""
Tests for POST /api/autofix endpoint.

All tests mock the Anthropic SDK so no real API calls are made.
"""
import anthropic
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from web.server import (
    app,
    compute_diff_warning,
    get_autofix_system_prompt,
    strip_code_fences,
    AUTOFIX_PROMPT_PATH,
)

client = TestClient(app)

SAMPLE_FILE_CONTENT = """{
  "id": "myPage",
  "endPoints": [
    {
      "baseUrlType": "https://api.workday.com/hardcoded"
    }
  ]
}"""

SAMPLE_FINDING = {
    "rule_id": "HardcodedWorkdayAPIRule",
    "severity": "ACTION",
    "message": "Hardcoded Workday API URL detected",
    "line": 5,
}

FIXED_FILE_CONTENT = """{
  "id": "myPage",
  "endPoints": [
    {
      "baseUrlType": "WORKDAY_COMMON"
    }
  ]
}"""


def _mock_api_response(text="fixed content"):
    """Return a mock Anthropic API response."""
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


class TestStripCodeFences:
    """Tests for strip_code_fences() helper."""

    def test_no_fences(self):
        assert strip_code_fences("hello world") == "hello world"

    def test_json_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        assert strip_code_fences(raw) == '{"key": "value"}'

    def test_plain_fences(self):
        raw = '```\nsome code\n```'
        assert strip_code_fences(raw) == "some code"

    def test_fences_with_whitespace(self):
        raw = '  ```json\n{"a": 1}\n```  '
        assert strip_code_fences(raw) == '{"a": 1}'

    def test_preserves_inner_content(self):
        raw = '```xml\n<root>\n  <child/>\n</root>\n```'
        result = strip_code_fences(raw)
        assert "<root>" in result
        assert "<child/>" in result


class TestAutofixEndpoint:
    """Tests for /api/autofix."""

    @patch("web.server._get_anthropic_client")
    def test_successful_autofix(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(FIXED_FILE_CONTENT)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["file_path"] == "test.pod"
        assert "WORKDAY_COMMON" in body["fixed_content"]

    @patch("web.server._get_anthropic_client")
    def test_api_called_with_temperature_zero(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(FIXED_FILE_CONTENT)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 0
        assert "HardcodedWorkdayAPIRule" in call_kwargs["messages"][0]["content"]
        assert "test.pod" in call_kwargs["messages"][0]["content"]

    def test_empty_content_rejected(self):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": "   ",
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 400
        assert "Empty file content" in resp.json()["detail"]

    def test_empty_finding_rejected(self):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": {},
        })
        assert resp.status_code == 400
        assert "No finding" in resp.json()["detail"]

    def test_missing_fields_422(self):
        resp = client.post("/api/autofix", json={"file_path": "test.pod"})
        assert resp.status_code == 422

    @patch("web.server._get_anthropic_client")
    def test_empty_ai_response(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response("")
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 502
        assert "empty response" in resp.json()["detail"]

    @patch("web.server._get_anthropic_client")
    def test_auth_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="invalid key", response=MagicMock(status_code=401), body={}
        )
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 503
        assert "API key" in resp.json()["detail"]

    @patch("web.server._get_anthropic_client")
    def test_timeout(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APITimeoutError(request=MagicMock())
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 504
        assert "timed out" in resp.json()["detail"]

    @patch("web.server._get_anthropic_client")
    def test_code_fence_stripping(self, mock_get_client):
        """LLM wraps output in code fences — they should be stripped."""
        fenced = '```json\n{"id": "fixed"}\n```'
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(fenced)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["fixed_content"] == '{"id": "fixed"}'
        assert "```" not in body["fixed_content"]

    @patch("web.server._get_anthropic_client")
    def test_model_env_override(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response()
        mock_get_client.return_value = mock_client

        with patch.dict("os.environ", {"LLM_MODEL": "claude-haiku-4-5"}):
            resp = client.post("/api/autofix", json={
                "file_path": "test.pod",
                "file_content": SAMPLE_FILE_CONTENT,
                "finding": SAMPLE_FINDING,
            })
        assert resp.status_code == 200
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5"


class TestAutofixPromptLoading:
    """Tests for autofix prompt file loading."""

    def test_loads_from_file(self):
        prompt = get_autofix_system_prompt()
        assert "code fixer" in prompt.lower() or "corrected" in prompt.lower()

    def test_prompt_file_exists(self):
        assert AUTOFIX_PROMPT_PATH.exists(), f"Prompt file missing: {AUTOFIX_PROMPT_PATH}"

    def test_fallback_on_missing_file(self):
        with patch.object(AUTOFIX_PROMPT_PATH.__class__, "stat", side_effect=FileNotFoundError):
            prompt = get_autofix_system_prompt()
            assert "code fixer" in prompt.lower()

    @patch("web.server._get_anthropic_client")
    def test_prompt_passed_to_api(self, mock_get_client):
        """Verify the file-loaded prompt reaches the API call."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response()
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        call_kwargs = mock_client.messages.create.call_args[1]
        assert len(call_kwargs["system"]) > 20

    def test_prompt_includes_lowercamelcase_rule(self):
        """Verify the prompt mandates lowerCamelCase for variables."""
        prompt = get_autofix_system_prompt()
        assert "lowerCamelCase" in prompt

    def test_prompt_includes_failonstatus_format(self):
        """Verify the prompt mandates dict format for failOnStatusCodes."""
        prompt = get_autofix_system_prompt()
        assert "failOnStatusCodes" in prompt
        assert '"code"' in prompt


class TestSequentialAutofix:
    """Tests simulating sequential Fix-All behavior (multiple fixes on same file)."""

    @patch("web.server._get_anthropic_client")
    def test_sequential_fixes_use_updated_content(self, mock_get_client):
        """Each fix call should accept the file content from the prior fix."""
        first_fix = '{"id": "myPage", "fixed": "first"}'
        second_fix = '{"id": "myPage", "fixed": "second"}'

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            _mock_api_response(first_fix),
            _mock_api_response(second_fix),
        ]
        mock_get_client.return_value = mock_client

        # First fix: original content → first_fix
        resp1 = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp1.status_code == 200
        assert resp1.json()["fixed_content"] == first_fix

        # Second fix: pass first_fix as input → second_fix
        resp2 = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": first_fix,
            "finding": {"rule_id": "AnotherRule", "severity": "ADVICE",
                        "message": "Another issue", "line": 1},
        })
        assert resp2.status_code == 200
        assert resp2.json()["fixed_content"] == second_fix

        # Verify both calls used different input content
        calls = mock_client.messages.create.call_args_list
        call1_msg = calls[0][1]["messages"][0]["content"]
        call2_msg = calls[1][1]["messages"][0]["content"]
        assert "hardcoded" in call1_msg  # original content
        assert "first" in call2_msg      # updated content

    @patch("web.server._get_anthropic_client")
    def test_fix_failure_midway_does_not_corrupt(self, mock_get_client):
        """If one fix in a batch fails, earlier fixes remain valid."""
        good_fix = '{"id": "myPage", "fixed": true}'

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            _mock_api_response(good_fix),
            anthropic.APIStatusError(
                message="rate limited",
                response=MagicMock(status_code=429),
                body={},
            ),
        ]
        mock_get_client.return_value = mock_client

        # First fix succeeds
        resp1 = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp1.status_code == 200
        assert resp1.json()["fixed_content"] == good_fix

        # Second fix fails
        resp2 = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": good_fix,
            "finding": {"rule_id": "AnotherRule", "severity": "ADVICE",
                        "message": "Another issue", "line": 1},
        })
        assert resp2.status_code == 500


class TestDiffWarning:
    """Tests for compute_diff_warning() and its integration into the autofix endpoint."""

    def test_no_warning_clean_fix(self):
        """Only the targeted finding line changes → None."""
        original = 'var myVar = "hello";\nvar x = 42;\nvar y = 100;'
        fixed = 'var myVar = "hello";\nconst MAGIC_NUM = 42;\nvar y = 100;'
        assert compute_diff_warning(original, fixed) is None

    def test_warning_on_unrelated_removal(self):
        """Extra function removed → warning with count."""
        original = (
            "function doStuff() { return 1; }\n"
            "function helper() { return 2; }\n"
            "var x = 42;\n"
        )
        fixed = "function doStuff() { return 1; }\nconst MAGIC = 42;\n"
        result = compute_diff_warning(original, fixed)
        assert result is not None
        assert result["removed_line_count"] == 1
        assert any("helper" in line for line in result["removed_lines"])

    def test_no_warning_on_comment_removal(self):
        """Comment-only lines removed → None."""
        original = "// This is a comment\n/* block */\nvar x = 1;"
        fixed = "var x = 1;"
        assert compute_diff_warning(original, fixed) is None

    def test_no_warning_on_blank_line_removal(self):
        """Blank/whitespace lines removed → None."""
        original = "var x = 1;\n\n   \n\nvar y = 2;"
        fixed = "var x = 1;\nvar y = 2;"
        assert compute_diff_warning(original, fixed) is None

    def test_no_warning_on_reformatted_line(self):
        """Line modified (high similarity) → None."""
        original = 'var myVariable = "hello world";'
        fixed = 'const myVariable = "hello world";'
        assert compute_diff_warning(original, fixed) is None

    def test_no_warning_on_short_lines(self):
        """Closing braces/parens removed → None."""
        original = "function foo() {\n  return 1;\n}\n}\n)"
        fixed = "function foo() {\n  return 1;\n}"
        assert compute_diff_warning(original, fixed) is None

    @patch("web.server._get_anthropic_client")
    def test_endpoint_includes_diff_warning(self, mock_get_client):
        """Integration: LLM returns content with extra removals → response has diff_warning."""
        # LLM removes the helper function
        fixed_with_removal = '{\n  "id": "myPage"\n}'
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(fixed_with_removal)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "diff_warning" in body
        # SAMPLE_FILE_CONTENT has endPoints block removed → should trigger warning
        assert body["diff_warning"] is not None
        assert body["diff_warning"]["removed_line_count"] >= 1

    @patch("web.server._get_anthropic_client")
    def test_endpoint_null_diff_warning_when_clean(self, mock_get_client):
        """Integration: clean fix → diff_warning is None."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_api_response(FIXED_FILE_CONTENT)
        mock_get_client.return_value = mock_client

        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "diff_warning" in body
        assert body["diff_warning"] is None

    def test_no_warning_on_python_comment_removal(self):
        """Python/shell # comments removed → None."""
        original = "# This is a Python comment\nimport os\n# Another comment"
        fixed = "import os"
        assert compute_diff_warning(original, fixed) is None

    def test_no_warning_on_sql_comment_removal(self):
        """SQL/Lua -- comments removed → None."""
        original = "-- SQL comment\nSELECT 1;\n-- another"
        fixed = "SELECT 1;"
        assert compute_diff_warning(original, fixed) is None

    def test_no_warning_on_html_comment_removal(self):
        """XML/HTML <!-- --> comment markers removed → None."""
        original = "<!-- start -->\n<div>hi</div>\n-->"
        fixed = "<div>hi</div>"
        assert compute_diff_warning(original, fixed) is None

    def test_consumed_match_prevents_double_pairing(self):
        """Each added line can only pair with one removed line.

        Two removed lines that are both similar to a single added line:
        the second one should be flagged because the added line is consumed.
        """
        original = (
            "function alpha() { return 1; }\n"
            "function bravo() { return 2; }\n"
            "function charlie() { return 3; }\n"
        )
        # Only one added line that could match either bravo or charlie
        fixed = (
            "function alpha() { return 1; }\n"
            "function bravoUpdated() { return 2; }\n"
        )
        result = compute_diff_warning(original, fixed)
        # bravo matches bravoUpdated (consumed), charlie has no match → warning
        assert result is not None
        assert result["removed_line_count"] == 1
        assert any("charlie" in line for line in result["removed_lines"])
