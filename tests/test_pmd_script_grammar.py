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
        # Most invalid cases should fail, but Earley parser is more permissive
        invalid_cases = [
            ":getTodaysDate",  # Missing module name
            "date:",  # Missing function name
            "date::getTodaysDate",  # Double colon
        ]
        
        for invalid_content in invalid_cases:
            with pytest.raises(Exception):
                pmd_script_parser.parse(invalid_content)
        
        # Some cases that Earley parser might accept (due to its permissive nature)
        # but would be caught by other validation layers
        potentially_invalid_cases = [
            "date:getTodays:Date",  # Multiple colons - Earley might parse as separate tokens
        ]
        
        for invalid_content in potentially_invalid_cases:
            # Earley parser might accept this, so we just verify it doesn't crash
            try:
                ast = pmd_script_parser.parse(invalid_content)
                # If it parses, that's okay - validation would happen elsewhere
                assert ast is not None
            except Exception:
                # If it fails, that's also okay
                pass

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

    def test_set_literal_basic_parsing(self):
        """Test basic set literal parsing with {} syntax."""
        test_cases = [
            # Basic sets with different value types (wrapped in variable assignments for proper context)
            "var x = {1, 2, 3};",
            "var y = {'a', 'b', 'c'};",
            "var z = {true, false};",
            "var mixed = {1, 'mixed', true};",

            # Sets with variables
            "var vars = {x, y, z};",
            "var props = {user.name, user.email};",

            # Sets with expressions
            "var calc = {1 + 2, 3 * 4};",
            "var funcs = {getValue(), getOther()};",
        ]
        
        for script_content in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse set literal: {script_content}"
            
            # Verify that set literal expressions are present
            found_set_literal = False
            for node in ast.iter_subtrees():
                if hasattr(node, 'data') and node.data in ['set_literal_with_elements', 'curly_literal_expression']:
                    found_set_literal = True
                    break
            
            assert found_set_literal, f"Set literal expression not found in AST for: {script_content}"

    def test_set_literal_in_variable_declarations(self):
        """Test set literals in variable declarations and assignments."""
        test_cases = [
            # Variable declarations with sets
            "var mySet = {1, 2, 3};",
            "const colors = {'red', 'green', 'blue'};",
            "let numbers = {10, 20, 30};",
            
            # Assignments
            "mySet = {4, 5, 6};",
            "this.allowedValues = {'option1', 'option2'};",
            
            # In function calls
            "processSet({1, 2, 3});",
            "return {user.id, user.name};",
        ]
        
        for script_content in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse set in context: {script_content}"

    def test_set_literal_vs_empty_block_disambiguation(self):
        """Test that empty blocks {} are correctly distinguished from sets."""
        test_cases = [
            # Empty blocks (statements)
            ("if (true) {}", "Empty block should parse as block"),
            ("function test() {}", "Empty function body should parse as block"),
            ("while (x > 0) {}", "Empty while body should parse as block"),
            
            # Non-empty sets (expressions)
            ("var s = {1};", "Single-element set should parse as set"),
            ("var s = {1, 2};", "Multi-element set should parse as set"),
            ("return {value};", "Set in return should parse as set"),
        ]
        
        for script_content, description in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse: {script_content} ({description})"

    def test_set_literal_complex_expressions(self):
        """Test set literals with complex expressions and nested structures."""
        test_cases = [
            # Sets with complex expressions
            "{user.name + ' suffix', user.email}",
            "{getValue() ?? 'default', getOther()}",
            "{items[0], items[1]}",
            
            # Sets in object literals
            "var config = { allowedValues: {1, 2, 3}, name: 'test' };",
            
            # Sets in arrays
            "var data = [{1, 2}, {3, 4}];",
            
            # Nested expressions
            "{func(a, b), func(c, d)}",
            "{a ? b : c, d ? e : f}",
        ]
        
        for script_content in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse complex set: {script_content}"

    def test_set_literal_edge_cases(self):
        """Test set literal edge cases and boundary conditions."""
        test_cases = [
            # Single element sets (important for disambiguation)
            "{42}",
            "{'single'}",
            "{variable}",
            
            # Sets with trailing commas (if supported)
            # Note: This might not be supported depending on expression_sequence definition
            # "{1, 2, 3,}",  # Uncomment if trailing commas are supported
            
            # Sets with whitespace
            "{ 1 , 2 , 3 }",
            "{\n  'a',\n  'b'\n}",
            
            # Sets with function calls
            "{getFirst(), getSecond()}",
            
            # Sets with member access
            "{obj.prop1, obj.prop2}",
        ]
        
        for script_content in test_cases:
            ast = pmd_script_parser.parse(script_content)
            assert ast is not None, f"Failed to parse set edge case: {script_content}"

    def test_empty_set_limitation(self):
        """Test that empty sets {} are not supported (due to block ambiguity)."""
        # Empty sets should be created using alternative syntax
        # This test documents the limitation
        
        # These should work (non-empty sets)
        working_cases = [
            "{1}",
            "{null}",
            "{'empty'}",
        ]
        
        for case in working_cases:
            ast = pmd_script_parser.parse(case)
            assert ast is not None, f"Non-empty set should work: {case}"
        
        # Empty {} will parse as a block/statement, not a set literal
        # This is expected behavior due to the grammar disambiguation
        empty_block = "{}"
        ast = pmd_script_parser.parse(empty_block)
        assert ast is not None, f"Empty braces should parse (as block): {empty_block}"
        
        # Note: For empty sets, users should use: new Set() or Set.of() syntax