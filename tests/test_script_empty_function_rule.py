#!/usr/bin/env python3

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.rules.script.unused_code.empty_functions import ScriptEmptyFunctionRule
from parser.rules.script.unused_code.empty_function_detector import EmptyFunctionDetector
from parser.app_parser import ModelParser


class TestScriptEmptyFunctionRule:
    """Test cases for ScriptEmptyFunctionRule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptEmptyFunctionRule()
    
    def test_empty_function_detection(self):
        """Test detection of empty functions."""
        script_content = """
        var myFunction = function() {
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "empty body" in violations[0].message.lower()
    
    def test_non_empty_function_detection(self):
        """Test that non-empty functions are not flagged."""
        script_content = """
        var myFunction = function() {
            return 1;
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0
    
    def test_function_with_comments_only(self):
        """Test function with only comments."""
        script_content = """
        var myFunction = function() {
            // This is a comment
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "empty body" in violations[0].message.lower()
    
    def test_function_with_whitespace_only(self):
        """Test function with only whitespace."""
        script_content = """
        var myFunction = function() {
            
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "empty body" in violations[0].message.lower()
    
    def test_function_with_return_statement(self):
        """Test function with return statement."""
        script_content = """
        var myFunction = function() {
            return;
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0
    
    def test_function_with_expression(self):
        """Test function with expression."""
        script_content = """
        var myFunction = function() {
            x = 1;
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0
    
    def test_multiple_functions(self):
        """Test multiple functions in one script."""
        script_content = """
        var emptyFunction = function() {
        }
        
        var nonEmptyFunction = function() {
            return 1;
        }
        
        var anotherEmptyFunction = function() {
            // comment only
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 2
    
    def test_no_functions(self):
        """Test script with no functions."""
        script_content = """
        var x = 1;
        var y = 2;
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0
    
    def test_line_number_calculation(self):
        """Test line number calculation."""
        script_content = """
        var myFunction = function() {
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 10)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        # The line number should be calculated based on the script content and offset
        assert violations[0].line > 0
    
    def test_pmd_wrapper_stripping(self):
        """Test that PMD wrappers are properly stripped."""
        script_content = "<% var myFunction = function() {\n} %>"
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
    
    def test_escaped_content(self):
        """Test handling of escaped content."""
        script_content = """
        var myFunction = function() {
            // This has escaped quotes: \\"
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
    
    def test_function_with_parameters(self):
        """Test function with parameters."""
        script_content = """
        var myFunction = function(param1, param2) {
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
    
    def test_function_with_parameters_and_content(self):
        """Test function with parameters and content."""
        script_content = """
        var myFunction = function(param1, param2) {
            return param1 + param2;
        }
        """
        
        ast = self.rule._parse_script_content(script_content)
        detector = EmptyFunctionDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0


class TestScriptEmptyFunctionRuleIntegration:
    """Integration tests for ScriptEmptyFunctionRule."""
    
    def test_with_real_pmd_file(self):
        """Test with a real PMD file that should have no empty functions."""
        # Create a simple PMD file for testing
        pmd_content = '''{
  "pageId": "testPage",
  "onLoad": "<% var myFunction = function() { return 1; } %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Test Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_simple.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_simple.pmd': 'test_simple.pmd'})
            
            if context.pmds:
                pmd_model = list(context.pmds.values())[0]
                rule = ScriptEmptyFunctionRule()
                
                # Check for violations
                violations = list(rule.visit_pmd(pmd_model))
                assert len(violations) == 0, f"Expected 0 violations, got {len(violations)}"
        
        finally:
            # Clean up
            if os.path.exists('test_simple.pmd'):
                os.remove('test_simple.pmd')
    
    def test_with_empty_function_pmd(self):
        """Test with a PMD file containing an empty function."""
        pmd_content = '''{
  "pageId": "testPage",
  "onLoad": "<% var emptyFunction = function() { } %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Test Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_empty_function.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_empty_function.pmd': 'test_empty_function.pmd'})
            
            if context.pmds:
                pmd_model = list(context.pmds.values())[0]
                rule = ScriptEmptyFunctionRule()
                
                # Check for violations
                violations = list(rule.visit_pmd(pmd_model))
                assert len(violations) == 1, f"Expected 1 violation, got {len(violations)}"
                assert "empty body" in violations[0].message.lower()
        
        finally:
            # Clean up
            if os.path.exists('test_empty_function.pmd'):
                os.remove('test_empty_function.pmd')


if __name__ == "__main__":
    pytest.main([__file__])
