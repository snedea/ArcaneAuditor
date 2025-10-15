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

    def test_nested_simple_functions_not_flagged(self):
        """Test that top-level function with simple inline function (neither flagged)."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const parentFunc = function(data) {
    const helperFunc = function(x) {
      return x + 1;
    };
    return helperFunc(data);
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0

    def test_nested_complex_inline_function_flagged(self):
        """Test that only complex inline function is flagged when parent is simple."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const parentFunc = function(data) {
    const complexHelper = function(x) {
      if (x.a) {
        if (x.b) {
          if (x.c) {
            if (x.d) {
              if (x.e) {
                if (x.f) {
                  if (x.g) {
                    if (x.h) {
                      if (x.i) {
                        if (x.j) {
                          if (x.k) {
                            return 'complex';
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
    return complexHelper(data);
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Only the inline function should be flagged
        assert len(findings) == 1
        assert "complexHelper" in findings[0].message
        assert "parentFunc" in findings[0].message
        assert "inline" in findings[0].message.lower() or "inside" in findings[0].message.lower()

    def test_nested_complex_parent_function_flagged(self):
        """Test that only complex parent function is flagged when inline is simple."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const complexParent = function(data) {
    const simpleHelper = function(x) {
      return x + 1;
    };
    if (data.a) {
      if (data.b) {
        if (data.c) {
          if (data.d) {
            if (data.e) {
              if (data.f) {
                if (data.g) {
                  if (data.h) {
                    if (data.i) {
                      if (data.j) {
                        if (data.k) {
                          return simpleHelper(data);
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
        
        # Only the parent function should be flagged
        assert len(findings) == 1
        assert "complexParent" in findings[0].message
        assert "simpleHelper" not in findings[0].message
        assert "inline" not in findings[0].message.lower()

    def test_nested_both_functions_complex_flagged(self):
        """Test that both complex parent and inline functions are flagged separately."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const complexParent = function(data) {
    const complexHelper = function(x) {
      if (x.a) {
        if (x.b) {
          if (x.c) {
            if (x.d) {
              if (x.e) {
                if (x.f) {
                  if (x.g) {
                    if (x.h) {
                      if (x.i) {
                        if (x.j) {
                          if (x.k) {
                            return 'complex helper';
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
      return 'default helper';
    };
    if (data.a) {
      if (data.b) {
        if (data.c) {
          if (data.d) {
            if (data.e) {
              if (data.f) {
                if (data.g) {
                  if (data.h) {
                    if (data.i) {
                      if (data.j) {
                        if (data.k) {
                          return complexHelper(data);
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
    return 'default parent';
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Both functions should be flagged
        assert len(findings) == 2
        
        # Check that we have violations for both functions
        messages = [f.message for f in findings]
        assert any("complexParent" in msg and "inline" not in msg.lower() for msg in messages)
        assert any("complexHelper" in msg and "inline" in msg.lower() for msg in messages)

    def test_nested_function_line_numbers_correct(self):
        """Test that line numbers are correct for nested function violations."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const parentFunc = function(data) {
    const complexHelper = function(x) {
      if (x.a) {
        if (x.b) {
          if (x.c) {
            if (x.d) {
              if (x.e) {
                if (x.f) {
                  if (x.g) {
                    if (x.h) {
                      if (x.i) {
                        if (x.j) {
                          if (x.k) {
                            return 'complex';
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
    return complexHelper(data);
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have one finding for the inline function
        assert len(findings) == 1
        finding = findings[0]
        
        # The line number should be around where the inline function is defined
        # (line 3 in the script, but accounting for PMD wrapper, should be around line 2-4)
        assert 2 <= finding.line <= 4, f"Expected line 2-4, got {finding.line}"

    def test_deeply_nested_functions_limit_tracking(self):
        """Test that deeply nested functions (3+ levels) only track top 2 levels."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="""<%
  const level1Func = function(data) {
    const level2Func = function(x) {
      const level3Func = function(y) {
        if (y.a) {
          if (y.b) {
            if (y.c) {
              if (y.d) {
                if (y.e) {
                  if (y.f) {
                    if (y.g) {
                      if (y.h) {
                        if (y.i) {
                          if (y.j) {
                            if (y.k) {
                              return 'very deep';
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
        return 'default level3';
      };
      return level3Func(x);
    };
    return level2Func(data);
  };
%>"""
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should only flag level2Func (the nested function we track)
        # level3Func should be ignored as it's too deeply nested
        assert len(findings) == 1
        assert "level2Func" in findings[0].message
        assert "level3Func" not in findings[0].message
        assert "level1Func" in findings[0].message  # Should be mentioned as parent


if __name__ == '__main__':
    pytest.main([__file__])