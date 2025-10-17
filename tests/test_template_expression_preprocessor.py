#!/usr/bin/env python3
"""Unit tests for Template Expression Preprocessor."""

import unittest
from parser.rules.script.shared.template_expression_preprocessor import TemplateExpressionPreprocessor


class TestTemplateExpressionPreprocessor(unittest.TestCase):
    """Test cases for TemplateExpressionPreprocessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preprocessor = TemplateExpressionPreprocessor()
    
    def test_is_template_expression_simple(self):
        """Test detection of simple template expressions."""
        # Template expression with multiple script blocks
        self.assertTrue(self.preprocessor.is_template_expression('"<% true %> foo <% false %>"'))
        self.assertTrue(self.preprocessor.is_template_expression("'<% name %> and <% age %>'"))
        
        # Pure script block (not a template expression)
        self.assertFalse(self.preprocessor.is_template_expression('<% true %>'))
        self.assertFalse(self.preprocessor.is_template_expression('<% var x = 1; %>'))
        
        # Regular string (not a template expression)
        self.assertFalse(self.preprocessor.is_template_expression('"Hello World"'))
        self.assertFalse(self.preprocessor.is_template_expression('"No script blocks"'))
        
        # Non-string input
        self.assertFalse(self.preprocessor.is_template_expression(123))
        self.assertFalse(self.preprocessor.is_template_expression(None))
    
    def test_parse_template_content_simple(self):
        """Test parsing of simple template expressions."""
        # Test: "<% true %> foo <% false %>"
        parts = self.preprocessor._parse_template_content('<% true %> foo <% false %>')
        expected = [
            {'type': 'script', 'content': 'true'},
            {'type': 'text', 'content': ' foo '},
            {'type': 'script', 'content': 'false'}
        ]
        self.assertEqual(parts, expected)
    
    def test_parse_template_content_text_first(self):
        """Test parsing when text comes first."""
        # Test: "Hello <% name %> world"
        parts = self.preprocessor._parse_template_content('Hello <% name %> world')
        expected = [
            {'type': 'text', 'content': 'Hello '},
            {'type': 'script', 'content': 'name'},
            {'type': 'text', 'content': ' world'}
        ]
        self.assertEqual(parts, expected)
    
    def test_parse_template_content_text_last(self):
        """Test parsing when text comes last."""
        # Test: "<% greeting %> there!"
        parts = self.preprocessor._parse_template_content('<% greeting %> there!')
        expected = [
            {'type': 'script', 'content': 'greeting'},
            {'type': 'text', 'content': ' there!'}
        ]
        self.assertEqual(parts, expected)
    
    def test_parse_template_content_multiple_blocks(self):
        """Test parsing with multiple script blocks."""
        # Test: "<% first %> and <% second %> and <% third %>"
        parts = self.preprocessor._parse_template_content('<% first %> and <% second %> and <% third %>')
        expected = [
            {'type': 'script', 'content': 'first'},
            {'type': 'text', 'content': ' and '},
            {'type': 'script', 'content': 'second'},
            {'type': 'text', 'content': ' and '},
            {'type': 'script', 'content': 'third'}
        ]
        self.assertEqual(parts, expected)
    
    def test_parse_template_content_empty_text(self):
        """Test parsing with empty text segments."""
        # Test: "<%a%><%b%>"
        parts = self.preprocessor._parse_template_content('<%a%><%b%>')
        expected = [
            {'type': 'script', 'content': 'a'},
            {'type': 'script', 'content': 'b'}
        ]
        self.assertEqual(parts, expected)
    
    def test_parse_template_content_whitespace(self):
        """Test parsing with various whitespace."""
        # Test: "<%  true  %>   foo   <%  false  %>"
        parts = self.preprocessor._parse_template_content('<%  true  %>   foo   <%  false  %>')
        expected = [
            {'type': 'script', 'content': 'true'},
            {'type': 'text', 'content': '   foo   '},
            {'type': 'script', 'content': 'false'}
        ]
        self.assertEqual(parts, expected)
    
    def test_preprocess_template_expression_simple(self):
        """Test preprocessing of simple template expressions."""
        # Test: "<% true %> foo <% false %>"
        result = self.preprocessor.preprocess_template_expression('<% true %> foo <% false %>')
        
        # Check that we get a template_expression tree
        self.assertEqual(result.data, 'template_expression')
        self.assertEqual(len(result.children), 3)
        
        # Check first script block - should contain AST, not token
        self.assertEqual(result.children[0].data, 'template_script_block')
        self.assertEqual(len(result.children[0].children), 1)
        # The child should be an AST node, not a token
        script_ast = result.children[0].children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
        
        # Check text part
        self.assertEqual(result.children[1].data, 'template_text')
        self.assertEqual(result.children[1].children[0].value, ' foo ')
        
        # Check second script block - should contain AST, not token
        self.assertEqual(result.children[2].data, 'template_script_block')
        self.assertEqual(len(result.children[2].children), 1)
        # The child should be an AST node, not a token
        script_ast = result.children[2].children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
    
    def test_preprocess_template_expression_with_quotes(self):
        """Test preprocessing with surrounding quotes."""
        # Test: '"<% name %> and <% age %>"'
        result = self.preprocessor.preprocess_template_expression('"<% name %> and <% age %>"')
        
        # Check that quotes are removed and content is parsed correctly
        self.assertEqual(result.data, 'template_expression')
        self.assertEqual(len(result.children), 3)
        
        # Check first script block - should contain AST
        self.assertEqual(result.children[0].data, 'template_script_block')
        script_ast = result.children[0].children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
        
        # Check text part
        self.assertEqual(result.children[1].data, 'template_text')
        self.assertEqual(result.children[1].children[0].value, ' and ')
        
        # Check second script block - should contain AST
        self.assertEqual(result.children[2].data, 'template_script_block')
        script_ast = result.children[2].children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
    
    def test_preprocess_template_expression_single_quotes(self):
        """Test preprocessing with single quotes."""
        # Test: "'<% greeting %> there!'"
        result = self.preprocessor.preprocess_template_expression("'<% greeting %> there!'")
        
        # Check that single quotes are removed and content is parsed correctly
        self.assertEqual(result.data, 'template_expression')
        self.assertEqual(len(result.children), 2)
        
        # Check script block - should contain AST
        self.assertEqual(result.children[0].data, 'template_script_block')
        script_ast = result.children[0].children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
        
        # Check text part
        self.assertEqual(result.children[1].data, 'template_text')
        self.assertEqual(result.children[1].children[0].value, ' there!')
    
    def test_preprocess_template_expression_empty_script(self):
        """Test preprocessing with empty script blocks."""
        # Test: "<% %> foo <% bar %>"
        result = self.preprocessor.preprocess_template_expression('<% %> foo <% bar %>')
        
        # Empty script blocks should be skipped
        self.assertEqual(result.data, 'template_expression')
        self.assertEqual(len(result.children), 2)
        
        # Check text part
        self.assertEqual(result.children[0].data, 'template_text')
        self.assertEqual(result.children[0].children[0].value, ' foo ')
        
        # Check script block
        self.assertEqual(result.children[1].data, 'template_script_block')
        script_ast = result.children[1].children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
    
    def test_script_blocks_are_parsed_ast(self):
        """Test that script blocks contain parsed AST, not tokens."""
        # Test with property access
        result = self.preprocessor.preprocess_template_expression('"<% user.name %> and <% user.age %>"')
        
        # Check first script block contains AST
        first_script = result.children[0]
        self.assertEqual(first_script.data, 'template_script_block')
        script_ast = first_script.children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
        
        # Check second script block contains AST
        second_script = result.children[2]
        self.assertEqual(second_script.data, 'template_script_block')
        script_ast = second_script.children[0]
        self.assertTrue(hasattr(script_ast, 'data'))
        self.assertEqual(script_ast.data, 'source_elements')
    
    def test_template_expression_with_property_access(self):
        """Test template expression with property access."""
        result = self.preprocessor.preprocess_template_expression('"<% user.name %> and <% user.age %>"')
        
        # Verify structure
        self.assertEqual(result.data, 'template_expression')
        self.assertEqual(len(result.children), 3)
        
        # Check property access AST
        first_script = result.children[0]
        script_ast = first_script.children[0]
        self.assertEqual(script_ast.data, 'source_elements')
        
        second_script = result.children[2]
        script_ast = second_script.children[0]
        self.assertEqual(script_ast.data, 'source_elements')
    
    def test_template_expression_with_function_calls(self):
        """Test template expression with function calls."""
        result = self.preprocessor.preprocess_template_expression('"Value: <% calculateTotal(price, tax) %>"')
        
        # Verify structure
        self.assertEqual(result.data, 'template_expression')
        self.assertEqual(len(result.children), 2)
        
        # Check function call AST
        script_block = result.children[1]
        script_ast = script_block.children[0]
        self.assertEqual(script_ast.data, 'source_elements')
    
    def test_template_expression_with_operators(self):
        """Test template expression with operators."""
        result = self.preprocessor.preprocess_template_expression('"<% firstName + " " + lastName %>"')
        
        # Verify structure
        self.assertEqual(result.data, 'template_expression')
        self.assertEqual(len(result.children), 1)
        
        # Check additive expression AST
        script_block = result.children[0]
        script_ast = script_block.children[0]
        self.assertEqual(script_ast.data, 'source_elements')
    
    def test_single_script_block_not_affected(self):
        """Test that single script blocks are not affected by template expression handling."""
        # This should NOT be detected as a template expression
        single_block = '"<% user.name %>"'
        self.assertFalse(self.preprocessor.is_template_expression(single_block))
        
        # Test with complex expression
        complex_single = '"<% calculateTotal(price, tax) %>"'
        self.assertFalse(self.preprocessor.is_template_expression(complex_single))
    
    def test_single_script_block_with_complex_expression(self):
        """Test that single script blocks with complex expressions still work."""
        # This should NOT be detected as a template expression
        complex_single = '"<% calculateTotal(price, tax) %>"'
        self.assertFalse(self.preprocessor.is_template_expression(complex_single))
        
        # Test with ternary operator
        ternary_single = '"<% empty(user.profile) ? \"No profile\" : user.profile.name %>"'
        self.assertFalse(self.preprocessor.is_template_expression(ternary_single))


if __name__ == '__main__':
    unittest.main()
