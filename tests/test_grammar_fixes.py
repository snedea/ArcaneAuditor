#!/usr/bin/env python3
"""
Tests for the grammar fixes - comment parsing bug and error handling improvements.
"""

import pytest
from parser.pmd_script_parser import pmd_script_parser
from parser.models import PMDModel, ProjectContext


class TestGrammarFixes:
    """Test the grammar fixes for comment parsing and error handling."""

    def test_comment_after_block_parsing(self):
        """Test that comments after block symbols no longer cause parsing failures."""
        
        # Test case that previously failed: multiple functions with comments after blocks
        script_content = """
const func1 = function(){
} // end func1

const func2 = function(){
}
"""
        
        # This should now parse successfully
        ast = pmd_script_parser.parse(script_content)
        assert ast is not None
        
        # Verify we have source_elements with multiple statements
        assert ast.data == 'source_elements'
        assert len(ast.children) >= 2  # Should have at least 2 statements

    def test_single_function_with_comment_after_block(self):
        """Test that single functions with comments after blocks still work."""
        
        script_content = """
const func1 = function(){
} // end func1
"""
        
        ast = pmd_script_parser.parse(script_content)
        assert ast is not None

    def test_multiple_functions_without_comments(self):
        """Test that multiple functions without comments still work."""
        
        script_content = """
const func1 = function(){
}

const func2 = function(){
}
"""
        
        ast = pmd_script_parser.parse(script_content)
        assert ast is not None
        assert ast.data == 'source_elements'

    def test_parsing_error_handling_in_context(self):
        """Test that parsing errors are properly surfaced in ProjectContext."""
        
        # Create a PMD model with invalid script content
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test_page",
            file_path="test.pmd",
            source_content="test content",
            script="invalid script syntax {"
        )
        
        # Try to parse the script - this should fail and add error to context
        ast = pmd_model.get_script_ast(context)
        
        # AST should be None due to parsing failure
        assert ast is None
        
        # Context should have parsing errors
        assert len(context.parsing_errors) > 0
        assert any("Script parsing failed" in error for error in context.parsing_errors)

    def test_parsing_error_handling_without_context(self):
        """Test that parsing errors are handled gracefully when no context is provided."""
        
        # Create a PMD model with invalid script content
        pmd_model = PMDModel(
            pageId="test_page",
            file_path="test.pmd",
            source_content="test content",
            script="invalid script syntax {"
        )
        
        # Try to parse without context - should not crash
        ast = pmd_model.get_script_ast()
        
        # AST should be None due to parsing failure
        assert ast is None

    def test_onLoad_parsing_error_handling(self):
        """Test that onLoad parsing errors are properly handled."""
        
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test_page",
            file_path="test.pmd",
            source_content="test content",
            onLoad="invalid onLoad syntax {"
        )
        
        # Try to parse the onLoad script
        ast = pmd_model.get_onLoad_ast(context)
        
        # AST should be None due to parsing failure
        assert ast is None
        
        # Context should have parsing errors
        assert len(context.parsing_errors) > 0
        assert any("Script parsing failed" in error for error in context.parsing_errors)

    def test_empty_script_content_handling(self):
        """Test that empty or None script content is handled properly."""
        
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test_page",
            file_path="test.pmd",
            source_content="test content",
            script=""
        )
        
        # Try to parse empty script
        ast = pmd_model.get_script_ast(context)
        
        # AST should be None for empty content
        assert ast is None
        
        # Context should not have parsing errors for empty content
        assert len(context.parsing_errors) == 0

    def test_valid_script_parsing_still_works(self):
        """Test that valid script parsing still works correctly."""
        
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test_page",
            file_path="test.pmd",
            source_content="test content",
            script="const x = 1;"
        )
        
        # Try to parse valid script
        ast = pmd_model.get_script_ast(context)
        
        # AST should be valid
        assert ast is not None
        
        # Context should not have parsing errors
        assert len(context.parsing_errors) == 0

    def test_complex_comment_scenarios(self):
        """Test various complex comment scenarios that should work."""
        
        test_cases = [
            # Multiple functions with different comment styles
            """
const func1 = function(){
} // end func1

const func2 = function(){
} /* end func2 */

const func3 = function(){
}
""",
            # Function with comment on same line as closing brace
            """
const func1 = function(){
} // end func1
const func2 = function(){
}
""",
            # Function with comment and semicolon
            """
const func1 = function(){
}; // end func1

const func2 = function(){
};
"""
        ]
        
        for script_content in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse: {script_content}"
            assert ast.data == 'source_elements'
