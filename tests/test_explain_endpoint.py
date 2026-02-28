"""
Tests for POST /api/explain endpoint.

All tests mock subprocess.run so no real Claude CLI is needed.
"""
import subprocess
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from web.server import app, get_explain_system_prompt, EXPLAIN_PROMPT_PATH

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


def _mock_completed(stdout="## Explanation\nLooks good.", returncode=0, stderr=""):
    """Return a mock CompletedProcess for subprocess.run."""
    cp = MagicMock(spec=subprocess.CompletedProcess)
    cp.stdout = stdout
    cp.stderr = stderr
    cp.returncode = returncode
    return cp


class TestExplainEndpoint:
    """Tests for /api/explain."""

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_success(self, mock_run):
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert "explanation" in body
        assert "Explanation" in body["explanation"]

        # Verify subprocess was called with correct args
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == "claude"
        assert "--print" in cmd
        assert "--max-turns" in cmd
        assert "--system-prompt" in cmd
        assert kwargs["input"] is not None
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
    def test_response_is_stripped(self, mock_run):
        """Verify leading/trailing whitespace is stripped from Claude output."""
        mock_run.return_value = _mock_completed(stdout="\n\n  Some explanation  \n\n")
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        assert resp.json()["explanation"] == "Some explanation"

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_control_chars_in_output_are_serialized(self, mock_run):
        """Verify control characters in Claude output survive JSON serialization."""
        mock_run.return_value = _mock_completed(
            stdout="| Col1\t| Col2 |\n| ---\t| --- |"
        )
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        body = resp.json()
        assert "\t" in body["explanation"]  # tab preserved through FastAPI serialization


class TestPromptLoading:
    """Tests for mtime-cached prompt file loading."""

    def test_loads_from_file(self):
        prompt = get_explain_system_prompt()
        assert "Workday Extend" in prompt
        assert "TRIAGE" in prompt

    def test_prompt_file_exists(self):
        assert EXPLAIN_PROMPT_PATH.exists(), f"Prompt file missing: {EXPLAIN_PROMPT_PATH}"

    def test_fallback_on_missing_file(self):
        with patch.object(EXPLAIN_PROMPT_PATH.__class__, "stat", side_effect=FileNotFoundError):
            prompt = get_explain_system_prompt()
            assert "code reviewer" in prompt  # fallback prompt

    @patch("web.server.subprocess.run", return_value=_mock_completed())
    def test_prompt_passed_to_subprocess(self, mock_run):
        """Verify the file-loaded prompt reaches the subprocess command."""
        resp = client.post("/api/explain", json={"findings": SAMPLE_FINDINGS})
        assert resp.status_code == 200
        cmd = mock_run.call_args[0][0]
        # Find the --system-prompt value
        sp_idx = cmd.index("--system-prompt")
        prompt_arg = cmd[sp_idx + 1]
        assert "TRIAGE" in prompt_arg
