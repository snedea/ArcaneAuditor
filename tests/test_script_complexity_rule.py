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
    
    def test_high_complexity_function_flagged(self):
        """Test that highly complex functions are flagged (per-function analysis)."""
        from parser.models import PMDModel
        
        # Function with 11+ nested if statements (complexity > 10)
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const complexFunc = function(item) {
    if (item.a) {
      if (item.b) {
        if (item.c) {
          if (item.d) {
            if (item.e) {
              if (item.f) {
                if (item.g) {
                  if (item.h) {
                    if (item.i) {
                      if (item.j) {
                        if (item.k) {
                          return 'very complex';
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
    }
    return 'default';
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "complexity" in findings[0].message.lower()
        assert "complexFunc" in findings[0].message
    
    def test_mixed_simple_and_complex_only_flags_complex(self):
        """Test that only complex function is flagged when mixed with simple function."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const simpleFunc = function(x) {
    return x > 0;
  };
  
  const complexFunc = function(item) {
    if (item.a) {
      if (item.b) {
        if (item.c) {
          if (item.d) {
            if (item.e) {
              if (item.f) {
                if (item.g) {
                  if (item.h) {
                    if (item.i) {
                      if (item.j) {
                        if (item.k) {
                          return 'very complex';
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
    }
    return 'default';
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Only complexFunc should be flagged, not the simple one
        assert len(findings) == 1
        assert "complexFunc" in findings[0].message
        assert "simpleFunc" not in findings[0].message
    
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