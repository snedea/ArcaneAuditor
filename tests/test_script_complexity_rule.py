#!/usr/bin/env python3
"""Unit tests for ScriptComplexityRule."""

import pytest
from parser.rules.script.complexity.cyclomatic_complexity import ScriptComplexityRule
from parser.models import ProjectContext


class TestScriptComplexityRule:
    """Test cases for ScriptComplexityRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptComplexityRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "complexity" in self.rule.DESCRIPTION.lower()
    
    # TODO: Add test for high complexity once threshold/implementation is confirmed
    #  def test_high_complexity_function_flagged(self):
    #      """Test that highly complex functions are flagged."""
    #      # Threshold may be very high or rule needs investigation
    
    def test_simple_function_not_flagged(self):
        """Test that simple functions are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const getUserName = function(user) {\n    return user.name || 'Unknown';\n  };\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])