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


if __name__ == '__main__':
    pytest.main([__file__])
