"""Test cases for PMD Script block comment parsing."""

import pytest
from parser.pmd_script_parser import pmd_script_parser


class TestPMDScriptBlockComments:
    """Test cases for block comment parsing in PMD Script grammar."""

    def test_simple_block_comment(self):
        """Test simple single-line block comment."""
        script = "/* simple comment */"
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_multiline_block_comment_with_alphabetic_characters(self):
        """Test multiline block comment with alphabetic characters (user's reported issue)."""
        script = """/*
 * This is a comment
*/"""
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_complex_multiline_block_comment(self):
        """Test complex multiline block comment with various content."""
        script = """/*
 * This is a complex comment
 * with alphabetic characters
 * and multiple lines
 * containing various symbols: @#$%^&*()
 */"""
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_block_comment_with_code_after(self):
        """Test block comment followed by actual code."""
        script = """/*
 * This is a comment
 */ var x = 1;"""
        result = pmd_script_parser.parse(script)
        assert result is not None
        # Should parse the variable declaration
        assert len(result.children) > 0

    def test_mixed_comments(self):
        """Test block comment combined with line comment."""
        script = """/* block comment */ // line comment"""
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_empty_block_comment(self):
        """Test empty block comment."""
        script = "/**/"
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_block_comment_with_special_characters(self):
        """Test block comment with special characters."""
        script = """/* comment with special chars: @#$%^&*()_+{}|:<>?[]\\;'\",./ */"""
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_block_comment_with_code_like_content(self):
        """Test block comment containing code-like syntax."""
        script = """/*
 * This looks like code:
 * var x = 1;
 * if (true) { return; }
 */"""
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_very_long_multiline_comment(self):
        """Test very long multiline comment for performance."""
        script = """/*
 * Very long comment
 * with multiple lines
 * and lots of text
 * to test performance
 * and ensure it handles
 * large comments properly
 */"""
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_nested_block_comments_should_fail(self):
        """Test that nested block comments fail gracefully (expected behavior)."""
        script = "/* outer /* inner */ outer */"
        with pytest.raises(Exception):
            pmd_script_parser.parse(script)

    def test_block_comment_in_block(self):
        """Test block comment within a code block."""
        script = """{
    /*
     * This is a block comment
     */
    var x = 1;
}"""
        result = pmd_script_parser.parse(script)
        assert result is not None

    def test_block_comment_with_unicode_characters(self):
        """Test block comment with unicode characters."""
        script = """/*
 * Comment with unicode: 你好世界 🌍
 * And emojis: 🚀 💻 📝
 */"""
        result = pmd_script_parser.parse(script)
        assert result is not None
