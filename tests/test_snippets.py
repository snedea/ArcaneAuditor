"""
Tests for source code snippet extraction.

Exercises extract_snippet() and build_source_map() which provide
the deterministic code-context shown alongside each finding.
"""
import pytest
from types import SimpleNamespace

from web.server import extract_snippet, build_source_map


# --- Sample 10-line source for most tests ---
SAMPLE_SOURCE = {
    "app/page.pmd": [
        "{",                        # line 1
        '  "pageId": "myPage",',    # line 2
        '  "script": "<%',          # line 3
        "    var x = 1;",           # line 4
        "    var y = 2;",           # line 5
        "    return x + y;",        # line 6
        '  %>",',                   # line 7
        '  "title": "Hello"',       # line 8
        "}",                        # line 9
    ],
}


# ---- extract_snippet: happy path ----

class TestExtractSnippetHappyPath:
    def test_default_returns_full_file(self):
        """Default (context_lines=None) should return all lines."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 5)
        assert result is not None
        assert result["start_line"] == 1
        numbers = [l["number"] for l in result["lines"]]
        assert numbers == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_highlighted_line_is_correct(self):
        """Only the finding line should be highlighted."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 5)
        highlights = [l for l in result["lines"] if l["highlight"]]
        assert len(highlights) == 1
        assert highlights[0]["number"] == 5
        assert highlights[0]["text"] == "    var y = 2;"

    def test_non_highlighted_lines_are_false(self):
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 5)
        non_highlights = [l for l in result["lines"] if not l["highlight"]]
        assert all(not l["highlight"] for l in non_highlights)
        assert len(non_highlights) == 8

    def test_first_line_highlight(self):
        """Finding on line 1 should highlight first line, show full file."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 1)
        assert result is not None
        assert result["start_line"] == 1
        assert result["lines"][0]["highlight"] is True
        assert len(result["lines"]) == 9

    def test_last_line_highlight(self):
        """Finding on last line should highlight last line, show full file."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 9)
        assert result is not None
        last = result["lines"][-1]
        assert last["number"] == 9
        assert last["highlight"] is True
        assert len(result["lines"]) == 9

    def test_bounded_context_lines(self):
        """context_lines=1 should return only 3 lines total."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 5, context_lines=1)
        assert result is not None
        numbers = [l["number"] for l in result["lines"]]
        assert numbers == [4, 5, 6]

    def test_bounded_context_clamps_start(self):
        """context_lines=3 on line 1 should clamp start to 1."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 1, context_lines=3)
        assert result is not None
        assert result["start_line"] == 1
        assert result["lines"][0]["highlight"] is True
        assert len(result["lines"]) == 4

    def test_bounded_context_clamps_end(self):
        """context_lines=3 on last line should clamp end to file length."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 9, context_lines=3)
        assert result is not None
        assert result["start_line"] == 6
        assert len(result["lines"]) == 4

    def test_text_content_preserved(self):
        """Snippet text should match source exactly."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 3)
        texts = [l["text"] for l in result["lines"]]
        assert '  "script": "<%' in texts


# ---- extract_snippet: edge cases returning None ----

class TestExtractSnippetEdgeCases:
    def test_file_not_in_source_map(self):
        """Unknown file path should return None."""
        result = extract_snippet(SAMPLE_SOURCE, "nonexistent.pmd", 5)
        assert result is None

    def test_line_zero(self):
        """Line 0 (invalid) should return None."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 0)
        assert result is None

    def test_negative_line(self):
        """Negative line number should return None."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", -3)
        assert result is None

    def test_empty_source_map(self):
        """Empty source map should return None."""
        result = extract_snippet({}, "app/page.pmd", 5)
        assert result is None

    def test_line_beyond_file_end_full_file(self):
        """Line past end with default (full file) returns all lines, none highlighted."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 100)
        # Full file is returned but no line is highlighted (line 100 doesn't exist)
        assert result is not None
        assert len(result["lines"]) == 9
        assert all(not l["highlight"] for l in result["lines"])

    def test_line_beyond_file_end_bounded(self):
        """Line past end with bounded context returns None."""
        result = extract_snippet(SAMPLE_SOURCE, "app/page.pmd", 100, context_lines=3)
        assert result is None

    def test_empty_file(self):
        """File with empty content (0 lines) should return None."""
        source = {"empty.pmd": []}
        result = extract_snippet(source, "empty.pmd", 1)
        assert result is None


# ---- build_source_map ----

class TestBuildSourceMap:
    @staticmethod
    def _make_context(pmds=None, pods=None, scripts=None, amd=None, smd=None):
        """Build a minimal context-like object for testing."""
        ctx = SimpleNamespace()
        ctx.pmds = pmds or {}
        ctx.pods = pods or {}
        ctx.scripts = scripts or {}
        ctx.amd = amd
        ctx.smd = smd
        return ctx

    def test_pmd_model(self):
        pmd = SimpleNamespace(
            source_content="line1\nline2\nline3",
            file_path="app/page.pmd"
        )
        ctx = self._make_context(pmds={"myPage": pmd})
        source_map = build_source_map(ctx)
        assert "app/page.pmd" in source_map
        assert source_map["app/page.pmd"] == ["line1", "line2", "line3"]

    def test_pod_model(self):
        pod = SimpleNamespace(
            source_content='{"podId":"test"}',
            file_path="app/test.pod"
        )
        ctx = self._make_context(pods={"test": pod})
        source_map = build_source_map(ctx)
        assert "app/test.pod" in source_map

    def test_script_model_uses_source_field(self):
        """ScriptModel has .source not .source_content — build_source_map handles this."""
        script = SimpleNamespace(
            source="var x = 1;\nvar y = 2;",
            file_path="app/helpers.script"
        )
        # No source_content attr — getattr fallback should use .source
        ctx = self._make_context(scripts={"helpers.script": script})
        source_map = build_source_map(ctx)
        assert "app/helpers.script" in source_map
        assert source_map["app/helpers.script"] == ["var x = 1;", "var y = 2;"]

    def test_script_model_with_source_content(self):
        """If a script model has source_content, prefer it over .source."""
        script = SimpleNamespace(
            source_content="preferred\ncontent",
            source="fallback",
            file_path="app/utils.script"
        )
        ctx = self._make_context(scripts={"utils.script": script})
        source_map = build_source_map(ctx)
        assert source_map["app/utils.script"] == ["preferred", "content"]

    def test_amd_model(self):
        amd = SimpleNamespace(
            source_content='{"routes":{}}',
            file_path="app/routes.amd"
        )
        ctx = self._make_context(amd=amd)
        source_map = build_source_map(ctx)
        assert "app/routes.amd" in source_map

    def test_smd_model(self):
        smd = SimpleNamespace(
            source_content='{"id":"app"}',
            file_path="app/service.smd"
        )
        ctx = self._make_context(smd=smd)
        source_map = build_source_map(ctx)
        assert "app/service.smd" in source_map

    def test_empty_context(self):
        ctx = self._make_context()
        source_map = build_source_map(ctx)
        assert source_map == {}

    def test_skips_empty_source_content(self):
        """Models with empty source_content should not appear in source_map."""
        pmd = SimpleNamespace(source_content="", file_path="app/empty.pmd")
        ctx = self._make_context(pmds={"empty": pmd})
        source_map = build_source_map(ctx)
        assert "app/empty.pmd" not in source_map

    def test_multiple_model_types(self):
        """All model types should appear in a single source_map."""
        pmd = SimpleNamespace(source_content="pmd content", file_path="a.pmd")
        pod = SimpleNamespace(source_content="pod content", file_path="b.pod")
        script = SimpleNamespace(source="script content", file_path="c.script")
        amd = SimpleNamespace(source_content="amd content", file_path="d.amd")
        smd = SimpleNamespace(source_content="smd content", file_path="e.smd")
        ctx = self._make_context(
            pmds={"p": pmd}, pods={"q": pod},
            scripts={"c.script": script}, amd=amd, smd=smd
        )
        source_map = build_source_map(ctx)
        assert len(source_map) == 5
