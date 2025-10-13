#!/usr/bin/env python3
"""Unit tests for ScriptUnusedFunctionParametersRule."""

import pytest
from parser.rules.script.unused_code.unused_parameters import ScriptUnusedFunctionParametersRule
from parser.models import ProjectContext


class TestScriptUnusedFunctionParametersRule:
    """Test cases for ScriptUnusedFunctionParametersRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedFunctionParametersRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "parameter" in self.rule.DESCRIPTION.lower()
    
    def test_unused_parameter_flagged(self):
        """Test that unused function parameters are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const processUser = function(user, options) {\n    return user.name;\n  };\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "options" in findings[0].message
    
    def test_all_parameters_used_not_flagged(self):
        """Test that functions with all parameters used are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const formatUser = function(user, prefix) {\n    return prefix + user.name;\n  };\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
