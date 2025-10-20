#!/usr/bin/env python3
"""Unit tests for StringBooleanRule."""

import pytest
from parser.rules.structure.validation.string_boolean import StringBooleanRule
from parser.models import ProjectContext


class TestStringBooleanRule:
    """Test cases for StringBooleanRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = StringBooleanRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "string" in self.rule.DESCRIPTION.lower()
    
    def test_string_true_flagged(self):
        """Test that string 'true' is flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "test", "enabled": "true"}',
            presentation={"body": {"type": "text", "enabled": "true"}}
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "true" in findings[0].message.lower()
    
    def test_string_false_flagged(self):
        """Test that string 'false' is flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "test", "visible": "false"}',
            presentation={"body": {"type": "text", "visible": "false"}}
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "false" in findings[0].message.lower()
    
    def test_actual_boolean_not_flagged(self):
        """Test that actual boolean values are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "test", "enabled": true, "visible": false}',
            presentation={"body": {"type": "text", "enabled": True, "visible": False}}
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])