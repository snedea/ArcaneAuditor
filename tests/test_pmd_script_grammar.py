#!/usr/bin/env python3
"""
Tests for PMD script grammar parsing functionality.
"""

import pytest
from parser.pmd_script_parser import pmd_script_parser


class TestPMDScriptGrammar:
    """Test PMD script grammar parsing functionality."""

    def test_namespace_identifier_parsing(self):
        """Test parsing of namespace identifiers (module:function syntax)."""
        test_cases = [
            ("date:getTodaysDate", "namespace_identifier_expression"),
            ("workday:getCurrentWorker", "namespace_identifier_expression"),
            ("api:fetchData", "namespace_identifier_expression"),
            ("util:formatString", "namespace_identifier_expression"),
        ]
        
        for script_content, expected_rule in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast.data == expected_rule
            assert len(ast.children) == 1
            assert ast.children[0].type == "NAMESPACE_IDENTIFIER"

    def test_namespace_function_calls(self):
        """Test parsing of function calls with namespace identifiers."""
        test_cases = [
            ("date:getTodaysDate()", "arguments_expression"),
            ("date:getTodaysDate(date:getDateTimeZone('US/Pacific'))", "arguments_expression"),
            ("workday:getCurrentWorker()", "arguments_expression"),
            ("api:fetchData(url, params)", "arguments_expression"),
        ]
        
        for script_content, expected_rule in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast.data == expected_rule
            # Check that the function name is a namespace identifier
            function_name = ast.children[0]
            assert function_name.data == "namespace_identifier_expression"

    def test_namespace_in_expressions(self):
        """Test namespace identifiers in various expression contexts."""
        test_cases = [
            # Assignment
            ("var result = date:getTodaysDate();", "variable_statement"),
            ("let data = api:fetchData();", "variable_statement"),
            # Return statement
            ("return date:getTodaysDate();", "return_statement"),
            # Function call as argument
            ("var result = formatDate(date:getTodaysDate());", "variable_statement"),
        ]
        
        for script_content, expected_rule in test_cases:
            ast = pmd_script_parser.parse(script_content)
            # The root should be the expected rule type
            assert ast.data == expected_rule

    def test_mixed_namespace_and_regular_identifiers(self):
        """Test mixing namespace identifiers with regular identifiers."""
        script_content = """
            var localVar = 123;
            var result = date:getTodaysDate();
            var combined = localVar + result;
            return workday:formatDate(combined);
        """
        
        ast = pmd_script_parser.parse(script_content)
        assert ast is not None
        # Should parse successfully without conflicts

    def test_namespace_identifier_validation(self):
        """Test that invalid namespace syntax fails appropriately."""
        invalid_cases = [
            ":getTodaysDate",  # Missing module name
            "date:",  # Missing function name
            "date::getTodaysDate",  # Double colon
            "date:getTodays:Date",  # Multiple colons
        ]
        
        for invalid_content in invalid_cases:
            with pytest.raises(Exception):
                pmd_script_parser.parse(invalid_content)

    def test_backward_compatibility_regular_identifiers(self):
        """Test that regular identifiers still work correctly."""
        test_cases = [
            ("myVariable", "identifier_expression"),
            ("getCurrentTime", "identifier_expression"),
            ("myFunction()", "arguments_expression"),
            ("var x = 123;", "variable_statement"),
        ]
        
        for script_content, expected_rule in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast.data == expected_rule

    def test_empty_object_literal_parsing(self):
        """Test that empty object literals {:} parse correctly."""
        test_cases = [
            ("{:}", "object_literal_expression"),
            ("self.data = {:};", "assignment_expression"),
            ("var obj = {:};", "variable_statement"),
        ]
        
        for script_content, expected_rule in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None
            # Should parse successfully without errors

    def test_complex_namespace_usage(self):
        """Test complex real-world namespace usage scenarios."""
        # Test the actual content from util.script
        script_content = """
            var getCurrentTime = function() {
                return date:getTodaysDate(date:getDateTimeZone('US/Pacific'));
            };
        """
        
        ast = pmd_script_parser.parse(script_content)
        assert ast is not None
        # Should parse the function definition with namespace calls successfully
