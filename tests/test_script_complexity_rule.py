"""Unit tests for ScriptComplexityRule."""

import pytest
from parser.rules.script.complexity.cyclomatic_complexity import ScriptComplexityRule
from parser.rules.script.complexity.cyclomatic_complexity_detector import CyclomaticComplexityDetector
from parser.models import PMDModel
from parser.app_parser import ModelParser


class TestScriptComplexityRule:
    """Test cases for ScriptComplexityRule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptComplexityRule()
    
    def test_rule_metadata(self):
        """Test rule metadata."""
        assert self.rule.DESCRIPTION == "Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)"
        assert self.rule.SEVERITY == "WARNING"
        assert self.rule.DETECTOR == CyclomaticComplexityDetector
        assert self.rule.get_description() == "Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)"
    
    def test_simple_script_no_complexity(self):
        """Test script with no complexity-increasing constructs."""
        script_content = """
        var x = 1;
        var y = 2;
        return x + y;
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0
    
    def test_if_statement_adds_complexity(self):
        """Test that if statements add to cyclomatic complexity."""
        script_content = """
        if (x > 0) {
            return true;
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 2, which is under the limit of 10
    
    def test_multiple_if_statements(self):
        """Test multiple if statements accumulating complexity."""
        script_content = """
        if (x > 0) {
            if (y > 0) {
                if (z > 0) {
                    if (a > 0) {
                        if (b > 0) {
                            if (c > 0) {
                                if (d > 0) {
                                    if (e > 0) {
                                        if (f > 0) {
                                            if (g > 0) {
                                                return true;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        assert "complexity of 11" in violations[0].message
        assert "max recommended: 10" in violations[0].message
    
    def test_while_statement_adds_complexity(self):
        """Test that while statements add to cyclomatic complexity."""
        script_content = """
        while (x > 0) {
            x--;
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 2, which is under the limit of 10
    
    def test_for_statement_adds_complexity(self):
        """Test that for statements add to cyclomatic complexity."""
        script_content = """
        for (var i = 0; i < 10; i++) {
            console.log(i);
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 2, which is under the limit of 10
    
    def test_logical_and_adds_complexity(self):
        """Test that logical AND expressions add to cyclomatic complexity."""
        script_content = """
        if (x > 0 && y > 0) {
            return true;
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 3 (if + &&), which is under the limit of 10
    
    def test_logical_or_adds_complexity(self):
        """Test that logical OR expressions add to cyclomatic complexity."""
        script_content = """
        if (x > 0 || y > 0) {
            return true;
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 3 (if + ||), which is under the limit of 10
    
    def test_ternary_expression_adds_complexity(self):
        """Test that ternary expressions add to cyclomatic complexity."""
        script_content = """
        var result = x > 0 ? true : false;
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 2, which is under the limit of 10
    
    def test_high_complexity_script(self):
        """Test script with high cyclomatic complexity."""
        script_content = """
        if (a) {
            if (b) {
                if (c) {
                    if (d) {
                        if (e) {
                            if (f) {
                                if (g) {
                                    if (h) {
                                        if (i) {
                                            if (j) {
                                                return true;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        assert "complexity of 11" in violations[0].message
        assert "max recommended: 10" in violations[0].message
    
    def test_mixed_complexity_constructs(self):
        """Test mixed complexity-increasing constructs."""
        script_content = """
        if (x > 0 && y > 0) {
            while (z > 0) {
                for (var i = 0; i < 10; i++) {
                    if (a || b) {
                        var result = c ? d : e;
                        if (f && g) {
                            if (h || i) {
                                if (j) {
                                    if (k) {
                                        return true;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        assert "complexity" in violations[0].message
        assert "max recommended: 10" in violations[0].message
    
    def test_line_number_calculation(self):
        """Test line number calculation."""
        script_content = """
        var line1 = "test";
        var line2 = "test";
        if (x > 0) {
            return true;
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 2, which is under the limit of 10
        # The if statement should be detected at the correct line
    
    def test_pmd_wrapper_stripping(self):
        """Test that PMD wrapper stripping works correctly."""
        script_content = "<% if (x > 0) { return true; } %>"
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0  # Complexity = 2, which is under the limit of 10
    
    def test_custom_max_complexity(self):
        """Test with custom max complexity threshold."""
        script_content = """
        if (x > 0) {
            return true;
        }
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = CyclomaticComplexityDetector("test.pmd", 1)
        detector.max_complexity = 1  # Set very low threshold
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        assert "complexity of 2" in violations[0].message
        assert "max recommended: 1" in violations[0].message


class TestScriptComplexityRuleIntegration:
    """Integration tests for ScriptComplexityRule."""
    
    def test_with_real_pmd_file(self):
        """Test with a real PMD file structure."""
        pmd_content = '''{
  "pageId": "TestPage",
  "script": "<% if (x > 0 && y > 0) { while (z > 0) { for (var i = 0; i < 10; i++) { if (a || b) { var result = c ? d : e; if (f && g) { if (h || i) { if (j) { if (k) { return true; } } } } } } } } %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Test Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_complexity.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_complexity.pmd': 'test_complexity.pmd'})
            
            if context.pmds:
                pmd_model = list(context.pmds.values())[0]
                rule = ScriptComplexityRule()
                
                # Check for violations
                findings = list(rule.analyze(context))
                assert len(findings) == 1
                assert "complexity" in findings[0].message
                assert findings[0].file_path == "test_complexity.pmd"
        
        finally:
            # Clean up
            import os
            if os.path.exists('test_complexity.pmd'):
                os.remove('test_complexity.pmd')
    
    def test_with_simple_pmd(self):
        """Test with PMD containing simple script."""
        pmd_content = '''{
  "pageId": "TestPage",
  "script": "<% var x = 1; var y = 2; return x + y; %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Test Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_simple_complexity.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_simple_complexity.pmd': 'test_simple_complexity.pmd'})
            
            if context.pmds:
                pmd_model = list(context.pmds.values())[0]
                rule = ScriptComplexityRule()
                
                # Check for violations
                findings = list(rule.analyze(context))
                assert len(findings) == 0
        
        finally:
            # Clean up
            import os
            if os.path.exists('test_simple_complexity.pmd'):
                os.remove('test_simple_complexity.pmd')
