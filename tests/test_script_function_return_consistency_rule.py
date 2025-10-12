#!/usr/bin/env python3
"""Unit tests for ScriptFunctionReturnConsistencyRule."""

import pytest
from parser.rules.script.logic.return_consistency import ScriptFunctionReturnConsistencyRule
from parser.models import ProjectContext, PMDModel


class TestScriptFunctionReturnConsistencyRule:
    """Test cases for ScriptFunctionReturnConsistencyRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptFunctionReturnConsistencyRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "return" in self.rule.DESCRIPTION.lower()
    
    def test_function_with_no_return_statement(self):
        """Test that functions computing values without return statements are flagged."""
        script_content = """<%
            const failNull = function(){
              const workerData = {'skills': []};
              const isProgrammer = workerData.skills[0] == 'Programming' ?? false;
              // missing return!
            }
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violation for missing return
        assert len(findings) >= 1
        assert any("no return" in f.message.lower() for f in findings)
        assert any("failNull" in f.message for f in findings)
    
    def test_function_with_consistent_returns(self):
        """Test that functions with consistent returns are not flagged."""
        script_content = """<%
            const goodFunc = function(){
              const data = {'value': 42};
              return data.value;
            }
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_side_effect_only_function_without_variables(self):
        """Test that side-effect only functions without variable declarations are not flagged."""
        script_content = """<%
            const sideEffectFunc = function(){
              console.log('Hello');
              widget.setValue('test');
            }
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations for side-effect only functions
        assert len(findings) == 0
    
    def test_inconsistent_return_pattern(self):
        """Test that functions with inconsistent return patterns are flagged."""
        script_content = """<%
            const inconsistentFunc = function(x){
              if(x > 0){
                return true;
              }
              // No return in else path
            }
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find inconsistent return pattern
        assert len(findings) >= 1
        assert any("inconsistent" in f.message.lower() or "not all code paths" in f.message.lower() for f in findings)


if __name__ == '__main__':
    pytest.main([__file__])
