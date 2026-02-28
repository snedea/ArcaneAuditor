"""
Tests for POST /api/revalidate endpoint.

Validates that edited file contents can be re-validated against the rules engine
without file upload, and that findings update correctly when code is fixed.
"""
import json

import pytest
from fastapi.testclient import TestClient

from web.server import app

client = TestClient(app)

# A PMD with a widget missing an id (triggers WidgetIdRequiredRule)
DIRTY_PMD_CONTENT = json.dumps({
    "id": "testPage",
    "endPoints": [],
    "presentation": {
        "title": {"type": "title", "label": "Test Page"},
        "body": {
            "type": "section",
            "children": [
                {
                    "type": "text",
                    "label": "Hello"
                }
            ]
        }
    }
}, indent=2)

# Same PMD but with the id field added (fixes WidgetIdRequiredRule)
CLEAN_PMD_CONTENT = json.dumps({
    "id": "testPage",
    "endPoints": [],
    "presentation": {
        "title": {"type": "title", "label": "Test Page"},
        "body": {
            "type": "section",
            "children": [
                {
                    "type": "text",
                    "id": "helloText",
                    "label": "Hello"
                }
            ]
        }
    }
}, indent=2)

# A Workday script using var (triggers ScriptVarUsageRule)
DIRTY_SCRIPT_CONTENT = """\
<%
  var userName = 'test';
  return userName;
%>"""

# Same script using const instead (fixes ScriptVarUsageRule)
CLEAN_SCRIPT_CONTENT = """\
<%
  const userName = 'test';
  return userName;
%>"""

MALFORMED_JSON = "{ this is not valid json !!!"

# Config path that exists in presets (v1.4.0 moved presets under config/rules/)
DEFAULT_CONFIG = "config/rules/presets/development.json"


class TestRevalidateEndpoint:
    """Tests for /api/revalidate."""

    def test_valid_pmd_returns_findings(self):
        """Dirty PMD content should produce at least one finding."""
        resp = client.post("/api/revalidate", json={
            "files": {"test.pmd": DIRTY_PMD_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "findings" in body
        assert "summary" in body
        assert "errors" in body
        assert isinstance(body["findings"], list)
        # Widget missing id should trigger WidgetIdRequiredRule
        assert body["summary"]["total_findings"] > 0

    def test_fixed_pmd_returns_fewer_findings(self):
        """Clean PMD content should produce fewer findings than dirty."""
        dirty_resp = client.post("/api/revalidate", json={
            "files": {"test.pmd": DIRTY_PMD_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        clean_resp = client.post("/api/revalidate", json={
            "files": {"test.pmd": CLEAN_PMD_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        assert dirty_resp.status_code == 200
        assert clean_resp.status_code == 200
        dirty_count = dirty_resp.json()["summary"]["total_findings"]
        clean_count = clean_resp.json()["summary"]["total_findings"]
        assert clean_count < dirty_count

    def test_malformed_json_returns_error(self):
        """Malformed JSON file should not crash the endpoint."""
        resp = client.post("/api/revalidate", json={
            "files": {"broken.pmd": MALFORMED_JSON},
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        # Should still return a valid response structure
        assert "findings" in body
        assert "errors" in body

    def test_malformed_json_surfaces_parse_error(self):
        """Malformed JSON should produce a per-file error via context.parsing_errors."""
        # Valid JSON but invalid PMD schema (missing required presentation field)
        bad_pmd = json.dumps({"id": "noPresentation", "endPoints": []})
        resp = client.post("/api/revalidate", json={
            "files": {"bad.pmd": bad_pmd},
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        # Parser should report a parsing error for the invalid PMD
        pmd_errors = [e for e in body["errors"] if e["file_path"] == "bad.pmd"]
        assert len(pmd_errors) > 0, f"Expected parse error for bad.pmd, got errors: {body['errors']}"

    def test_empty_files_returns_empty_findings(self):
        """Empty files dict should return zero findings and no errors."""
        resp = client.post("/api/revalidate", json={
            "files": {},
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["findings"] == []
        assert body["summary"]["total_findings"] == 0
        assert body["errors"] == []

    def test_missing_config_falls_back(self):
        """Non-existent config name should fall back gracefully."""
        resp = client.post("/api/revalidate", json={
            "files": {"test.pmd": CLEAN_PMD_CONTENT},
            "config": "nonexistent_config_name",
        })
        assert resp.status_code == 200
        body = resp.json()
        # Should not crash — ConfigurationManager falls back to default
        assert "findings" in body
        assert "summary" in body

    def test_script_file_revalidation(self):
        """Script file with var usage should produce findings."""
        resp = client.post("/api/revalidate", json={
            "files": {"helpers.script": DIRTY_SCRIPT_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["findings"], list)
        # var usage should trigger ScriptVarUsageRule
        assert body["summary"]["total_findings"] > 0

    def test_script_file_fixed_no_findings(self):
        """Fixed script content should produce fewer findings."""
        dirty_resp = client.post("/api/revalidate", json={
            "files": {"helpers.script": DIRTY_SCRIPT_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        clean_resp = client.post("/api/revalidate", json={
            "files": {"helpers.script": CLEAN_SCRIPT_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        assert dirty_resp.status_code == 200
        assert clean_resp.status_code == 200
        dirty_count = dirty_resp.json()["summary"]["total_findings"]
        clean_count = clean_resp.json()["summary"]["total_findings"]
        assert clean_count < dirty_count

    def test_response_has_correct_structure(self):
        """Verify the response has all expected fields."""
        resp = client.post("/api/revalidate", json={
            "files": {"test.pmd": DIRTY_PMD_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "findings" in body
        assert "summary" in body
        assert "errors" in body
        summary = body["summary"]
        assert "total_findings" in summary
        assert "rules_executed" in summary
        assert "by_severity" in summary
        assert "action" in summary["by_severity"]
        assert "advice" in summary["by_severity"]

    def test_findings_have_expected_fields(self):
        """Each finding should include standard fields."""
        resp = client.post("/api/revalidate", json={
            "files": {"test.pmd": DIRTY_PMD_CONTENT},
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        for finding in body["findings"]:
            assert "rule_id" in finding
            assert "severity" in finding
            assert "message" in finding
            assert "file_path" in finding
            assert "line" in finding

    def test_multiple_files_cross_validation(self):
        """Sending multiple files should validate all of them."""
        resp = client.post("/api/revalidate", json={
            "files": {
                "page.pmd": DIRTY_PMD_CONTENT,
                "helpers.script": DIRTY_SCRIPT_CONTENT,
            },
            "config": DEFAULT_CONFIG,
        })
        assert resp.status_code == 200
        body = resp.json()
        # Should have findings from at least one file
        assert body["summary"]["total_findings"] > 0
