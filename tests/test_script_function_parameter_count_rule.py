"""Unit tests for ScriptFunctionParameterCountRule."""

from parser.rules.script.complexity.function_parameter_count import ScriptFunctionParameterCountRule
from parser.rules.script.complexity.function_parameter_count_detector import FunctionParameterCountDetector
from parser.app_parser import ModelParser


class TestScriptFunctionParameterCountRule:
    """Test cases for ScriptFunctionParameterCountRule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptFunctionParameterCountRule()
    
    def test_rule_metadata(self):
        """Test rule metadata."""
        assert self.rule.DESCRIPTION == "Functions should not have too many parameters (max 4 by default)"
        assert self.rule.SEVERITY == "WARNING"
        assert self.rule.DETECTOR == FunctionParameterCountDetector
        assert self.rule.get_description() == "Functions should not have too many parameters (max 4 by default)"
    
    def test_function_with_too_many_parameters(self):
        """Test detection of functions with too many parameters."""
        script_content = """
        var tooManyParams = function(a, b, c, d, e) {
            return a + b + c + d + e;
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        assert "5 parameters" in violations[0].message
        assert "max allowed: 4" in violations[0].message
        assert violations[0].line == 1
    
    def test_function_with_acceptable_parameters(self):
        """Test that functions with acceptable parameter count are not flagged."""
        script_content = """
        var goodFunction = function(x, y) {
            return x + y;
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0
    
    def test_arrow_function_with_too_many_parameters(self):
        """Test detection of arrow functions with too many parameters."""
        script_content = """
        var arrowFunction = (a, b, c, d, e, f) => {
            return a + b + c + d + e + f;
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        assert "6 parameters" in violations[0].message
        assert "max allowed: 4" in violations[0].message
        assert violations[0].line == 1
    
    def test_arrow_function_with_acceptable_parameters(self):
        """Test that arrow functions with acceptable parameter count are not flagged."""
        script_content = """
        var goodArrowFunction = (x) => {
            return x * 2;
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0
    
    def test_multiple_functions_mixed_results(self):
        """Test multiple functions with mixed results."""
        script_content = """
        var tooManyParams = function(a, b, c, d, e) {
            return a + b + c + d + e;
        };
        
        var goodFunction = function(x, y) {
            return x + y;
        };
        
        var arrowFunction = (a, b, c, d, e, f) => {
            return a + b + c + d + e + f;
        };
        
        var goodArrowFunction = (x) => {
            return x * 2;
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 2
        # Check that we found violations for the functions with too many parameters
        violation_messages = [v.message for v in violations]
        assert any("5 parameters" in msg for msg in violation_messages)
        assert any("6 parameters" in msg for msg in violation_messages)
    
    def test_function_with_no_parameters(self):
        """Test function with no parameters."""
        script_content = """
        var noParams = function() {
            return "hello";
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0
    
    def test_function_with_exactly_max_parameters(self):
        """Test function with exactly the maximum allowed parameters."""
        script_content = """
        var maxParams = function(a, b, c, d) {
            return a + b + c + d;
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 0
    
    def test_line_number_calculation(self):
        """Test line number calculation."""
        script_content = """
        var line1 = "test";
        var line2 = "test";
        var tooManyParams = function(a, b, c, d, e) {
            return a + b + c + d + e;
        };
        """
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        # The function should be detected at the correct line
        assert violations[0].line >= 1
    
    def test_pmd_wrapper_stripping(self):
        """Test that PMD wrapper stripping works correctly."""
        script_content = "<% var tooManyParams = function(a, b, c, d, e) { return a + b + c + d + e; }; %>"
        
        ast = self.rule._parse_script_content(script_content, None)
        detector = FunctionParameterCountDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        
        assert len(violations) == 1
        assert "5 parameters" in violations[0].message


class TestScriptFunctionParameterCountRuleIntegration:
    """Integration tests for ScriptFunctionParameterCountRule."""
    
    def test_with_real_pmd_file(self):
        """Test with a real PMD file structure."""
        pmd_content = '''{
  "pageId": "testPage",
  "script": "<% var tooManyParams = function(a, b, c, d, e) { return a + b + c + d + e; }; %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Test Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_parameter_count.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_parameter_count.pmd': 'test_parameter_count.pmd'})
            
            if context.pmds:
                pmd_model = list(context.pmds.values())[0]
                rule = ScriptFunctionParameterCountRule()
                
                # Check for violations
                findings = list(rule.analyze(context))
                assert len(findings) == 1
                assert "5 parameters" in findings[0].message
                assert findings[0].file_path == "test_parameter_count.pmd"
        
        finally:
            # Clean up
            import os
            if os.path.exists('test_parameter_count.pmd'):
                os.remove('test_parameter_count.pmd')
    
    def test_with_empty_function_pmd(self):
        """Test with PMD containing no functions."""
        pmd_content = '''{
  "pageId": "testPage",
  "script": "<% var x = 1; var y = 2; %>",
  "presentation": {
    "title": {
      "type": "title",
      "label": "Test Page"
    }
  }
}'''
        
        # Write to temporary file
        with open('test_no_functions.pmd', 'w', encoding='utf-8') as f:
            f.write(pmd_content)
        
        try:
            # Parse the file
            parser = ModelParser()
            context = parser.parse_files({'test_no_functions.pmd': 'test_no_functions.pmd'})
            
            if context.pmds:
                pmd_model = list(context.pmds.values())[0]
                rule = ScriptFunctionParameterCountRule()
                
                # Check for violations
                findings = list(rule.analyze(context))
                assert len(findings) == 0
        
        finally:
            # Clean up
            import os
            if os.path.exists('test_no_functions.pmd'):
                os.remove('test_no_functions.pmd')
