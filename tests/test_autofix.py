"""
Tests for POST /api/autofix endpoint.

All tests mock subprocess.run so no real Claude CLI is needed.
"""
import subprocess
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from web.server import (
    app,
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


def _mock_completed(stdout="fixed content", returncode=0, stderr=""):
    """Return a mock CompletedProcess for subprocess.run."""
    cp = MagicMock(spec=subprocess.CompletedProcess)
    cp.stdout = stdout
    cp.stderr = stderr
    cp.returncode = returncode
    return cp


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

    @patch("web.server.subprocess.run", return_value=_mock_completed(stdout=FIXED_FILE_CONTENT))
    def test_successful_autofix(self, mock_run):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["file_path"] == "test.pod"
        assert "WORKDAY_COMMON" in body["fixed_content"]

    @patch("web.server.subprocess.run", return_value=_mock_completed(stdout=FIXED_FILE_CONTENT))
    def test_subprocess_called_correctly(self, mock_run):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200

        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == "claude"
        assert "--print" in cmd
        assert "--max-turns" in cmd
        assert "--system-prompt" in cmd
        assert kwargs["input"] is not None
        assert "HardcodedWorkdayAPIRule" in kwargs["input"]
        assert "test.pod" in kwargs["input"]
        assert kwargs["timeout"] == 120

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

    @patch(
        "web.server.subprocess.run",
        return_value=_mock_completed(stdout="", returncode=0),
    )
    def test_empty_ai_response(self, mock_run):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 502
        assert "empty response" in resp.json()["detail"]

    @patch(
        "web.server.subprocess.run",
        return_value=_mock_completed(returncode=1, stderr="auth failed"),
    )
    def test_nonzero_exit_code(self, mock_run):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 502
        assert "auth failed" in resp.json()["detail"]

    @patch(
        "web.server.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=120),
    )
    def test_timeout(self, mock_run):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 504
        assert "timed out" in resp.json()["detail"]

    @patch("web.server.subprocess.run", side_effect=FileNotFoundError())
    def test_cli_not_found(self, mock_run):
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 503
        assert "not available" in resp.json()["detail"]

    @patch("web.server.subprocess.run")
    def test_code_fence_stripping(self, mock_run):
        """LLM wraps output in code fences — they should be stripped."""
        fenced = '```json\n{"id": "fixed"}\n```'
        mock_run.return_value = _mock_completed(stdout=fenced)
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["fixed_content"] == '{"id": "fixed"}'
        assert "```" not in body["fixed_content"]

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_model_env_override(self, mock_run):
        with patch.dict("os.environ", {"LLM_MODEL": "claude-haiku-4-5"}):
            resp = client.post("/api/autofix", json={
                "file_path": "test.pod",
                "file_content": SAMPLE_FILE_CONTENT,
                "finding": SAMPLE_FINDING,
            })
        assert resp.status_code == 200
        cmd = mock_run.call_args[0][0]
        assert "claude-haiku-4-5" in cmd


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

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_prompt_passed_to_subprocess(self, mock_run):
        """Verify the file-loaded prompt reaches the subprocess command."""
        resp = client.post("/api/autofix", json={
            "file_path": "test.pod",
            "file_content": SAMPLE_FILE_CONTENT,
            "finding": SAMPLE_FINDING,
        })
        assert resp.status_code == 200
        cmd = mock_run.call_args[0][0]
        sp_idx = cmd.index("--system-prompt")
        prompt_arg = cmd[sp_idx + 1]
        # Should contain content from the prompt file
        assert len(prompt_arg) > 20
