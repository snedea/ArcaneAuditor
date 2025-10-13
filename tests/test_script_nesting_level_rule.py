#!/usr/bin/env python3
"""Unit tests for ScriptNestingLevelRule."""

import pytest
from parser.rules.script.complexity.nesting_level import ScriptNestingLevelRule
from parser.models import ProjectContext


class TestScriptNestingLevelRule:
    """Test cases for ScriptNestingLevelRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptNestingLevelRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "nesting" in self.rule.DESCRIPTION.lower()
    
    def test_deep_nesting_flagged(self):
        """Test that deeply nested code is flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const processData = function(data) {
    if (data.level1) {
      if (data.level2) {
        if (data.level3) {
          if (data.level4) {
            if (data.level5) {
              return 'deeply nested';
            }
          }
        }
      }
    }
    return 'default';
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) >= 1
        assert "nesting" in findings[0].message.lower() or "depth" in findings[0].message.lower()
    
    def test_shallow_nesting_not_flagged(self):
        """Test that shallow nesting is not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const isValid = function(data) {\n    if (data.active) {\n      return data.value > 0;\n    }\n    return false;\n  };\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
