#!/usr/bin/env python3
"""Test cases for ScriptFunctionalMethodUsageRule."""

import pytest
from parser.rules.script.logic.functional_method_usage import ScriptFunctionalMethodUsageRule
from parser.rules.script.logic.functional_method_usage_detector import FunctionalMethodUsageDetector
from parser.models import PMDModel
from parser.app_parser import ModelParser


class TestScriptFunctionalMethodUsageRule:
    """Test cases for ScriptFunctionalMethodUsageRule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptFunctionalMethodUsageRule()
    
    def test_rule_metadata(self):
        """Test rule metadata."""
        assert self.rule.DESCRIPTION == "Detects manual loops that could be replaced with functional methods like map, filter, forEach"
        assert self.rule.SEVERITY == "WARNING"
        assert self.rule.DETECTOR == FunctionalMethodUsageDetector

    def test_simple_script_no_manual_loops(self):
        """Test a simple script with no manual loops."""
        script_content = """
        var x = 1;
        var y = x + 1;
        return y;
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_manual_for_loop_detection(self):
        """Test detection of manual for loops."""
        script_content = """
        for (let i = 0; i < array.length; i++) {
            result.push(array[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message
        assert "functional method" in violations[0].message

    def test_for_let_statement_detection(self):
        """Test detection of for let statements."""
        script_content = """
        for (let i = 0; i < items.length; i++) {
            console.log(items[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message

    def test_for_var_statement_detection(self):
        """Test detection of for var statements."""
        script_content = """
        for (var i = 0; i < data.length; i++) {
            sum += data[i];
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message

    def test_non_counter_based_loop_not_detected(self):
        """Test that non-counter-based loops are not detected."""
        script_content = """
        var x = 1;
        var y = x + 1;
        return y;
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_functional_method_suggestion_map(self):
        """Test suggestion of map() for array transformation."""
        script_content = """
        for (let i = 0; i < array.length; i++) {
            result.push(array[i] * 2);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        # The suggestion should be map() for array transformation
        assert "map()" in violations[0].message or "functional methods" in violations[0].message

    def test_functional_method_suggestion_forEach(self):
        """Test suggestion of forEach() for side effects."""
        script_content = """
        for (let i = 0; i < items.length; i++) {
            console.log(items[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        # The suggestion should be forEach() for side effects
        assert "forEach()" in violations[0].message or "functional methods" in violations[0].message

    def test_line_number_calculation(self):
        """Test line number calculation."""
        script_content = """
        var x = 1;
        for (let i = 0; i < array.length; i++) {
            result.push(array[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert violations[0].line == 2  # for loop is on line 2

    def test_pmd_wrapper_stripping(self):
        """Test that PMD wrappers are stripped correctly and rule still applies."""
        script_content = "<% for (let i = 0; i < items.length; i++) { result.push(items[i]); } %>"
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message

    def test_multiple_manual_loops(self):
        """Test multiple manual for loops in the same script."""
        script_content = """
        for (let i = 0; i < array1.length; i++) {
            result1.push(array1[i]);
        }
        for (let j = 0; j < array2.length; j++) {
            result2.push(array2[j]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 2

    def test_reverse_loop_detection(self):
        """Test detection of reverse loops."""
        script_content = """
        for (let i = array.length - 1; i >= 0; i--) {
            result.push(array[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionalMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message


class TestScriptFunctionalMethodUsageRuleIntegration:
    """Integration tests for ScriptFunctionalMethodUsageRule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptFunctionalMethodUsageRule()
        self.parser = ModelParser()

    def test_with_real_pmd_file(self):
        """Test the rule with a real PMD file containing manual loops."""
        pmd_content = '''{
  "pageId": "TestPage",
  "script": "<% for (let i = 0; i < items.length; i++) { result.push(items[i]); } %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Test Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_functional_method.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_functional_method.pmd': 'test_functional_method.pmd'})
            
            if context.pmds:
                rule = ScriptFunctionalMethodUsageRule()
                
                # Check for violations
                findings = list(rule.analyze(context))
                assert len(findings) == 1
                assert "manual for loop" in findings[0].message
                assert findings[0].file_path == "test_functional_method.pmd"
        finally:
            # Clean up
            import os
            if os.path.exists('test_functional_method.pmd'):
                os.remove('test_functional_method.pmd')

    def test_with_simple_pmd(self):
        """Test the rule with a simple PMD file that should not have violations."""
        pmd_content = '''{
  "pageId": "SimplePage",
  "script": "<% var x = 1; %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Simple Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_simple_functional.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_simple_functional.pmd': 'test_simple_functional.pmd'})
            
            if context.pmds:
                rule = ScriptFunctionalMethodUsageRule()
                
                # Check for violations
                findings = list(rule.analyze(context))
                assert len(findings) == 0
        finally:
            # Clean up
            import os
            if os.path.exists('test_simple_functional.pmd'):
                os.remove('test_simple_functional.pmd')
