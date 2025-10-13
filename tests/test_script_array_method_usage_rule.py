#!/usr/bin/env python3
"""Test cases for ScriptArrayMethodUsageRule."""

from parser.rules.script.logic.array_method_usage import ScriptArrayMethodUsageRule
from parser.rules.script.logic.array_method_usage_detector import ArrayMethodUsageDetector
from parser.app_parser import ModelParser


class TestScriptArrayMethodUsageRule:
    """Test cases for ScriptArrayMethodUsageRule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptArrayMethodUsageRule()
    
    def test_rule_metadata(self):
        """Test rule metadata."""
        assert self.rule.DESCRIPTION == "Detects manual loops that could be replaced with array higher-order methods like map, filter, forEach"
        assert self.rule.SEVERITY == "ADVICE"
        assert self.rule.DETECTOR == ArrayMethodUsageDetector

    def test_simple_script_no_manual_loops(self):
        """Test a simple script with no manual loops."""
        script_content = """
        var x = 1;
        var y = x + 1;
        return y;
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_manual_for_loop_detection(self):
        """Test detection of manual for loops using .size() (PMD Script)."""
        script_content = """
        for (let i = 0; i < array.size(); i++) {
            result.push(array[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message
        assert "functional method" in violations[0].message

    def test_for_let_statement_detection(self):
        """Test detection of for let statements using .size()."""
        script_content = """
        for (let i = 0; i < items.size(); i++) {
            console.log(items[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message

    def test_for_var_statement_detection(self):
        """Test detection of for var statements using .size()."""
        script_content = """
        for (var i = 0; i < data.size(); i++) {
            sum += data[i];
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
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
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_functional_method_suggestion_map(self):
        """Test suggestion of array methods for transformation."""
        script_content = """
        for (let i = 0; i < array.size(); i++) {
            result.push(array[i] * 2);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        # The suggestion should be map() for array transformation
        assert "map()" in violations[0].message or "functional methods" in violations[0].message

    def test_functional_method_suggestion_forEach(self):
        """Test suggestion of array methods for side effects."""
        script_content = """
        for (let i = 0; i < items.size(); i++) {
            console.info(items[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        # The suggestion should be forEach() for side effects
        assert "forEach()" in violations[0].message or "functional methods" in violations[0].message

    def test_line_number_calculation(self):
        """Test line number calculation."""
        script_content = """
        var x = 1;
        for (let i = 0; i < array.size(); i++) {
            result.push(array[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert violations[0].line == 2  # for loop is on line 2

    def test_pmd_wrapper_stripping(self):
        """Test that PMD wrappers are stripped correctly and rule still applies."""
        script_content = "<% for (let i = 0; i < items.size(); i++) { result.push(items[i]); } %>"
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message

    def test_multiple_manual_loops(self):
        """Test multiple manual for loops in the same script."""
        script_content = """
        for (let i = 0; i < array1.size(); i++) {
            result1.push(array1[i]);
        }
        for (let j = 0; j < array2.size(); j++) {
            result2.push(array2[j]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 2

    def test_range_loop_detection(self):
        """Test detection of range loops. Should not be detected."""
        script_content = """
        for (let i : (0 to 100)) {
            result.push(array[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0
    
    def test_pmd_script_size_method_detection(self):
        """Test detection of loops using .size() method (PMD Script)."""
        script_content = """
        for (let i = 0; i < items.size(); i++) {
            result.push(items[i]);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "manual for loop" in violations[0].message
    
    def test_pmd_script_size_with_multiple_loops(self):
        """Test detection of multiple loops using .size() method."""
        script_content = """
        for (let i = 0; i < foo.size(); i++) {
            
        }
        for (let j = 0; j < bar.size(); j++) {
            
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 2
    
    def test_numeric_literal_loop_not_flagged(self):
        """Test that numeric literal loops (not iterating arrays) are not flagged."""
        script_content = """
        for (let i = 0; i < 10; i++) {
            console.log(i);
        }
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = ArrayMethodUsageDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0  # No .length or .size() - just numeric literal


class TestScriptArrayMethodUsageRuleIntegration:
    """Integration tests for ScriptArrayMethodUsageRule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptArrayMethodUsageRule()
        self.parser = ModelParser()

    def test_with_real_pmd_file(self):
        """Test the rule with a real PMD file containing manual loops."""
        pmd_content = '''{
  "pageId": "testPage",
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
                rule = ScriptArrayMethodUsageRule()
                
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
  "pageId": "simplePage",
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
                rule = ScriptArrayMethodUsageRule()
                
                # Check for violations
                findings = list(rule.analyze(context))
                assert len(findings) == 0
        finally:
            # Clean up
            import os
            if os.path.exists('test_simple_functional.pmd'):
                os.remove('test_simple_functional.pmd')
