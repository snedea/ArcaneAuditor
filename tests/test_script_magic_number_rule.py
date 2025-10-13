#!/usr/bin/env python3
"""Unit tests for ScriptMagicNumberRule."""

import pytest
from parser.rules.script.logic.magic_numbers import ScriptMagicNumberRule
from parser.models import ProjectContext, PMDModel


class TestScriptMagicNumberRule:
    """Test cases for ScriptMagicNumberRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptMagicNumberRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "magic" in self.rule.DESCRIPTION.lower()
    
    def test_magic_number_in_expression(self):
        """Test that magic numbers in expressions are flagged."""
        script_content = """<%
            const result = value * 42;
            if (count > 100) {
                return count * 3.14;
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
        
        # Should find magic numbers: 42, 100
        # Note: 3.14 is a float and might not be detected depending on implementation
        assert len(findings) >= 2
        violation_messages = [f.message for f in findings]
        assert any("42" in msg for msg in violation_messages)
        assert any("100" in msg for msg in violation_messages)
    
    def test_named_constants_not_flagged(self):
        """Test that numbers assigned to named constants are NOT flagged."""
        script_content = """<%
            const maxLength = 10;
            const timeout = 5000;
            const pi = 3.14159;
            
            // These should be flagged (using the numbers directly)
            if (count > 50) {
                return true;
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
        
        # Should only flag 50 (used directly in comparison), not 10, 5000, or 3.14159 (assigned to constants)
        violation_messages = [f.message for f in findings]
        assert not any("'10'" in msg for msg in violation_messages), "const maxLength = 10 should not be flagged"
        assert not any("'5000'" in msg for msg in violation_messages), "const timeout = 5000 should not be flagged"
        assert any("'50'" in msg for msg in violation_messages), "Direct use of 50 should be flagged"
    
    def test_allowed_numbers_not_flagged(self):
        """Test that 0, 1, -1 are not flagged as magic numbers."""
        script_content = """<%
            let index = 0;
            const found = items.find(item => item.id === 1);
            let prev = current - 1;
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - 0, 1, -1 are allowed
        assert len(findings) == 0
    
    def test_let_variable_declarations_not_flagged(self):
        """Test that numbers in let declarations are not flagged."""
        script_content = """<%
            let maxRetries = 25;
            let defaultTimeout = 3;
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - numbers are in variable declarations
        assert len(findings) == 0
    
    def test_var_variable_declarations_not_flagged(self):
        """Test that numbers in var declarations are not flagged."""
        script_content = """<%
            var serverPort = 8080;
            var attemptLimit = 5;
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - numbers are in variable declarations
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
