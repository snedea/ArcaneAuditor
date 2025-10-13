#!/usr/bin/env python3
"""Unit tests for ScriptEmptyFunctionRule."""

import pytest
from parser.rules.script.unused_code.empty_functions import ScriptEmptyFunctionRule
from parser.models import ProjectContext


class TestScriptEmptyFunctionRule:
    """Test cases for ScriptEmptyFunctionRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptEmptyFunctionRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "empty" in self.rule.DESCRIPTION.lower()
    
    def test_empty_function_detected(self):
        """Test that empty functions are detected."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const emptyHandler = function() {\n  };\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "empty" in findings[0].message.lower()
    
    def test_function_with_body_not_flagged(self):
        """Test that functions with bodies are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const processData = function(data) {\n    return data.filter(item => item.active);\n  };\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])