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
        """Test that functions with no return statements are not flagged (void functions are valid)."""
        script_content = """<%
            const failNull = function(){
              const workerData = {'skills': []};
              const isProgrammer = workerData.skills[0] == 'Programming' ?? false;
              // No return statement - this is a valid void function
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
        
        # Should not find violation for void functions (no return statements)
        assert len(findings) == 0
    
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
        """Test that functions with inconsistent return patterns are correctly flagged."""
        script_content = """<%
            const inconsistentFunc = function(x){
              if(x > 0){
                return true;
              }
              // No return in else path - this is inconsistent!
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
        
        # Should find "not all code paths return" violation
        assert len(findings) >= 1, f"Expected violation for inconsistent return pattern, got: {[f.message for f in findings]}"
        partial_return_finding = next((f for f in findings if "not all code paths return" in f.message.lower()), None)
        assert partial_return_finding is not None, f"Expected 'not all code paths return' violation, got: {[f.message for f in findings]}"
        assert "not all code paths return" in partial_return_finding.message.lower()
        assert "consider adding else branches or a final return statement" in partial_return_finding.message.lower()
    
    def test_unreachable_return_after_if_else(self):
        """Test that unreachable return statements after if-else blocks are detected with specific messaging."""
        script_content = """<%
            const unreachableFunc = function(x){
              if(x > 0){
                return "positive";
              } else {
                return "negative";
              }
              return "unreachable"; // This should be flagged as unreachable
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
        
        # Should find unreachable return violation
        assert len(findings) >= 1
        unreachable_finding = next((f for f in findings if "unreachable" in f.message.lower()), None)
        assert unreachable_finding is not None, f"Expected unreachable violation, got: {[f.message for f in findings]}"
        assert "unreachable return statement" in unreachable_finding.message.lower()
        assert "if-else block above returns on all paths" in unreachable_finding.message.lower()
    
    def test_mixed_return_pattern_in_if_else(self):
        """Test detection of mixed return patterns in if-else-if-else chains."""
        script_content = """<%
            const mixedReturnFunc = function(x){
              if(x > 0){
                return "positive";
              } else if(x < 0){
                return "negative";
              }
              // No return in final else - this should be flagged as not all paths return
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
        
        # Should find "not all code paths return" violation (this is correct behavior)
        assert len(findings) >= 1
        partial_return_finding = next((f for f in findings if "not all code paths return" in f.message.lower()), None)
        assert partial_return_finding is not None, f"Expected partial return violation, got: {[f.message for f in findings]}"
        assert "not all code paths return" in partial_return_finding.message.lower()
        assert "consider adding else branches or a final return statement" in partial_return_finding.message.lower()


if __name__ == '__main__':
    pytest.main([__file__])
