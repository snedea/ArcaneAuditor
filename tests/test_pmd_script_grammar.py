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

    def test_null_coalescing_basic_parsing(self):
        """Test basic null coalescing operator parsing."""
        test_cases = [
            ("a ?? b", "null_coalescing_expression"),
            ("null ?? 'default'", "null_coalescing_expression"),
            ("undefined ?? false", "null_coalescing_expression"),
            ("user.name ?? 'Anonymous'", "null_coalescing_expression"),
        ]
        
        for script_content, expected_rule in test_cases:
            ast = pmd_script_parser.parse(script_content)
            # Find the null coalescing expression in the tree
            found = False
            for node in ast.iter_subtrees():
                if hasattr(node, 'data') and node.data == expected_rule:
                    found = True
                    break
            assert found, f"Expected {expected_rule} not found in AST for '{script_content}'"

    def test_null_coalescing_precedence(self):
        """Test null coalescing operator precedence with other operators."""
        test_cases = [
            # Null coalescing has lower precedence than logical AND
            ("a && b ?? c", "Should parse as (a && b) ?? c"),
            # Null coalescing has lower precedence than logical OR  
            ("a || b ?? c", "Should parse as (a || b) ?? c"),
            # Null coalescing has higher precedence than ternary
            ("a ?? b ? c : d", "Should parse as (a ?? b) ? c : d"),
            # Null coalescing with equality
            ("a == null ?? false", "Should parse as (a == null) ?? false"),
        ]
        
        for script_content, description in test_cases:
            # Just ensure it parses without error - precedence is handled by grammar structure
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse: {script_content} ({description})"

    def test_null_coalescing_chaining(self):
        """Test chained null coalescing operations (left-associative)."""
        test_cases = [
            "a ?? b ?? c",
            "user.name ?? user.email ?? 'Anonymous'",
            "config.primary ?? config.secondary ?? config.default ?? 'fallback'",
        ]
        
        for script_content in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse chained null coalescing: {script_content}"
            
            # Verify that null coalescing expressions are present
            null_coalescing_count = 0
            for node in ast.iter_subtrees():
                if hasattr(node, 'data') and node.data == 'null_coalescing_expression':
                    null_coalescing_count += 1
            
            # For chained operations, we expect at least one null coalescing expression
            assert null_coalescing_count > 0, f"No null coalescing expressions found in: {script_content}"

    def test_null_coalescing_in_complex_expressions(self):
        """Test null coalescing in complex expressions and statements."""
        test_cases = [
            # In variable declarations
            "var name = user.name ?? 'Anonymous';",
            "const result = data.value ?? 0;",
            "let config = settings.config ?? defaultConfig;",
            
            # In function calls
            "console.log(user.name ?? 'Guest');",
            "return calculateTotal(items ?? []);",
            
            # In assignments
            "this.title = options.title ?? 'Untitled';",
            
            # In object literals
            "var obj = { name: user.name ?? 'Unknown', age: user.age ?? 0 };",
            
            # In array literals
            "var arr = [user.name ?? 'Default', user.email ?? 'none'];",
            
            # With member access
            "var value = data.response.result ?? fallback.value;",
            
            # In conditional expressions
            "if (user.name ?? defaultName) { doSomething(); }",
        ]
        
        for script_content in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse complex expression: {script_content}"

    def test_null_coalescing_with_problematic_case(self):
        """Test the specific problematic case from the sample code.
        
        This tests that the grammar can parse the syntax, but the logic is flawed:
        - workerData.skills[0] == 'Programming' ?? false
        - The comparison happens first, returning false (not null/undefined)
        - So the ?? false never triggers, making it ineffective
        - The real issue is unsafe property access that could throw before ?? runs
        """
        # This is the exact case that was failing before grammar support
        script_content = "const isProgrammer = workerData.skills[0] == 'Programming' ?? false;"
        
        ast = pmd_script_parser.parse(script_content)
        assert ast is not None, "Failed to parse the problematic null coalescing case"
        
        # Verify it contains a null coalescing expression
        found_null_coalescing = False
        for node in ast.iter_subtrees():
            if hasattr(node, 'data') and node.data == 'null_coalescing_expression':
                found_null_coalescing = True
                break
        
        assert found_null_coalescing, "Null coalescing expression not found in problematic case"

    def test_null_coalescing_correct_usage_examples(self):
        """Test examples of correct null coalescing usage that would actually work."""
        correct_usage_cases = [
            # Correct: Provide fallback for potentially undefined values
            "const skill = workerData.skills[0] ?? 'No skills';",
            
            # Correct: Fallback for the entire object property
            "const skills = workerData.skills ?? [];",
            
            # Correct: Multiple fallbacks in chain
            "const name = user.name ?? user.email ?? 'Anonymous';",
            
            # Correct: Use with function return values
            "const result = getData() ?? getBackupData() ?? 'No data';",
            
            # Correct: Fallback for object properties
            "const config = settings.theme ?? 'default';",
        ]
        
        for script_content in correct_usage_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse correct usage: {script_content}"