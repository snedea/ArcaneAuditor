#!/usr/bin/env python3
"""Unit tests for ScriptVariableNamingRule."""

import pytest
from parser.rules.script.core.variable_naming import ScriptVariableNamingRule
from parser.models import ProjectContext


class TestScriptVariableNamingRule:
    """Test cases for ScriptVariableNamingRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptVariableNamingRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "naming" in self.rule.DESCRIPTION.lower()
    
    def test_pascal_case_variable_flagged(self):
        """Test that PascalCase variables are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const UserName = 'John';\n  return UserName;\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "UserName" in findings[0].message
    
    def test_snake_case_variable_flagged(self):
        """Test that snake_case variables are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const user_name = 'John';\n  return user_name;\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "user_name" in findings[0].message
    
    def test_lower_camel_case_not_flagged(self):
        """Test that lowerCamelCase variables are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const userName = 'John';\n  const userEmail = 'john@example.com';\n  return userName;\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0
    
    def test_arrow_function_single_parameter_flagged(self):
        """Test that single parameter arrow functions with bad naming are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const goodFunc = BadParam => BadParam * 2;\n  return goodFunc(5);\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "BadParam" in findings[0].message
        assert "arrow function" in findings[0].message.lower() or "function" in findings[0].message.lower()
    
    def test_arrow_function_multiple_parameters_flagged(self):
        """Test that multiple parameter arrow functions with bad naming are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const BadFunc = (BadParam1, BadParam2) => {BadParam1 + BadParam2};\n  return BadFunc(1, 2);\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for both BadParam1 and BadParam2
        assert len(findings) >= 2
        param_names = [f.message for f in findings]
        assert any("BadParam1" in msg for msg in param_names)
        assert any("BadParam2" in msg for msg in param_names)
    
    def test_arrow_function_good_naming_not_flagged(self):
        """Test that arrow functions with proper lowerCamelCase parameters are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const goodFunc = (goodParam1, goodParam2) => {goodParam1 + goodParam2};\n  const singleParam = x => x * 2;\n  return goodFunc(1, 2);\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should not find any violations for properly named parameters
        assert len(findings) == 0
    
    def test_arrow_function_mixed_naming(self):
        """Test arrow functions with mix of good and bad parameter naming."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const mixedFunc = (goodParam, BadParam) => {goodParam + BadParam};\n  return mixedFunc(1, 2);\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should only flag the bad parameter
        assert len(findings) == 1
        assert "BadParam" in findings[0].message
        assert "goodParam" not in findings[0].message


if __name__ == '__main__':
    pytest.main([__file__])
