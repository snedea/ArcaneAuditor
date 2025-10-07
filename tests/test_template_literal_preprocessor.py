#!/usr/bin/env python3
"""Unit tests for the Template Literal Preprocessor."""

import unittest
from lark import Tree, Token
from parser.rules.script.shared.template_literal_preprocessor import TemplateLiteralPreprocessor


class TestTemplateLiteralPreprocessor(unittest.TestCase):
    """Test cases for the Template Literal Preprocessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preprocessor = TemplateLiteralPreprocessor()
    
    def test_simple_property_access(self):
        """Test preprocessing of simple property access."""
        template_token = Token('TEMPLATE_LITERAL', "`{{workerPhoto.workerPhotos.href.ff}}`")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with one template_interpolation
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 1)
        
        interpolation = result_tree.children[0]
        self.assertEqual(interpolation.data, 'template_interpolation')
        
        # The interpolation should contain a member_dot_expression
        expr_tree = interpolation.children[0]
        self.assertEqual(expr_tree.data, 'member_dot_expression')
    
    def test_null_coalescing_expression(self):
        """Test preprocessing of null coalescing expressions."""
        template_token = Token('TEMPLATE_LITERAL', "`{{workerPhoto.workerPhotos.href.ff ?? ''}}`")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with one template_interpolation
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 1)
        
        interpolation = result_tree.children[0]
        self.assertEqual(interpolation.data, 'template_interpolation')
        
        # The interpolation should contain a null_coalescing_expression
        expr_tree = interpolation.children[0]
        self.assertEqual(expr_tree.data, 'null_coalescing_expression')
        
        # Should have two children: left (property access) and right (string literal)
        self.assertEqual(len(expr_tree.children), 2)
        
        # Left side should be member_dot_expression
        left_expr = expr_tree.children[0]
        self.assertEqual(left_expr.data, 'member_dot_expression')
        
        # Right side should be literal_expression with string
        right_expr = expr_tree.children[1]
        self.assertEqual(right_expr.data, 'literal_expression')
        self.assertEqual(right_expr.children[0].value, "''")
    
    def test_multiple_interpolations(self):
        """Test preprocessing of template with multiple interpolations."""
        template_token = Token('TEMPLATE_LITERAL', "`Hello {{user.name}}, your email is {{user.profile.email}}`")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with 4 children:
        # template_text, template_interpolation, template_text, template_interpolation
        # (empty text at the end is filtered out)
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 4)
        
        # Check first text part
        self.assertEqual(result_tree.children[0].data, 'template_text')
        self.assertEqual(result_tree.children[0].children[0].value, 'Hello ')
        
        # Check first interpolation
        self.assertEqual(result_tree.children[1].data, 'template_interpolation')
        first_interpolation = result_tree.children[1].children[0]
        self.assertEqual(first_interpolation.data, 'member_dot_expression')
        
        # Check second text part
        self.assertEqual(result_tree.children[2].data, 'template_text')
        self.assertEqual(result_tree.children[2].children[0].value, ', your email is ')
        
        # Check second interpolation
        self.assertEqual(result_tree.children[3].data, 'template_interpolation')
        second_interpolation = result_tree.children[3].children[0]
        self.assertEqual(second_interpolation.data, 'member_dot_expression')
    
    def test_static_text_only(self):
        """Test preprocessing of template with only static text."""
        template_token = Token('TEMPLATE_LITERAL', "`Hello World`")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with one template_text
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 1)
        
        text_part = result_tree.children[0]
        self.assertEqual(text_part.data, 'template_text')
        self.assertEqual(text_part.children[0].value, 'Hello World')
    
    def test_simple_identifier(self):
        """Test preprocessing of simple identifier interpolation."""
        template_token = Token('TEMPLATE_LITERAL', "`{{userName}}`")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with one template_interpolation
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 1)
        
        interpolation = result_tree.children[0]
        self.assertEqual(interpolation.data, 'template_interpolation')
        
        # The interpolation should contain an identifier_expression
        expr_tree = interpolation.children[0]
        self.assertEqual(expr_tree.data, 'identifier_expression')
        self.assertEqual(expr_tree.children[0].value, 'userName')
    
    def test_string_literal_interpolation(self):
        """Test preprocessing of string literal interpolation."""
        template_token = Token('TEMPLATE_LITERAL', "`{{'Hello'}}`")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with one template_interpolation
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 1)
        
        interpolation = result_tree.children[0]
        self.assertEqual(interpolation.data, 'template_interpolation')
        
        # The interpolation should contain a literal_expression
        expr_tree = interpolation.children[0]
        self.assertEqual(expr_tree.data, 'literal_expression')
        self.assertEqual(expr_tree.children[0].value, "'Hello'")
    
    def test_empty_template(self):
        """Test preprocessing of empty template."""
        template_token = Token('TEMPLATE_LITERAL', "``")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with no children
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 0)
    
    def test_template_with_only_interpolation(self):
        """Test preprocessing of template with only interpolation (no static text)."""
        template_token = Token('TEMPLATE_LITERAL', "`{{user.name}}`")
        result_tree = self.preprocessor.preprocess_template_literal(template_token)
        
        # Should create a template_literal_expression with one template_interpolation
        self.assertEqual(result_tree.data, 'template_literal_expression')
        self.assertEqual(len(result_tree.children), 1)
        
        interpolation = result_tree.children[0]
        self.assertEqual(interpolation.data, 'template_interpolation')
        
        # The interpolation should contain a member_dot_expression
        expr_tree = interpolation.children[0]
        self.assertEqual(expr_tree.data, 'member_dot_expression')
    
    def test_property_access_tree_creation(self):
        """Test the _create_property_access_tree method directly."""
        parts = ['user', 'profile', 'email']
        result_tree = self.preprocessor._create_property_access_tree(parts)
        
        # Should create a nested member_dot_expression
        self.assertEqual(result_tree.data, 'member_dot_expression')
        
        # Right side should be 'email'
        self.assertEqual(result_tree.children[1].value, 'email')
        
        # Left side should be another member_dot_expression for 'user.profile'
        left_expr = result_tree.children[0]
        self.assertEqual(left_expr.data, 'member_dot_expression')
        self.assertEqual(left_expr.children[1].value, 'profile')
        
        # Left side of that should be 'user'
        user_expr = left_expr.children[0]
        self.assertEqual(user_expr.data, 'identifier_expression')
        self.assertEqual(user_expr.children[0].value, 'user')
    
    def test_parse_template_content(self):
        """Test the _parse_template_content method directly."""
        content = "Hello {{user.name}}, your email is {{user.profile.email}}"
        parts = self.preprocessor._parse_template_content(content)
        
        # Should have 4 parts: text, interpolation, text, interpolation
        # (empty text at the end is filtered out)
        self.assertEqual(len(parts), 4)
        
        # Check types
        self.assertEqual(parts[0]['type'], 'text')
        self.assertEqual(parts[0]['content'], 'Hello ')
        
        self.assertEqual(parts[1]['type'], 'interpolation')
        self.assertEqual(parts[1]['content'], 'user.name')
        
        self.assertEqual(parts[2]['type'], 'text')
        self.assertEqual(parts[2]['content'], ', your email is ')
        
        self.assertEqual(parts[3]['type'], 'interpolation')
        self.assertEqual(parts[3]['content'], 'user.profile.email')


if __name__ == '__main__':
    unittest.main()
