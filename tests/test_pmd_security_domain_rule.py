#!/usr/bin/env python3
"""Unit tests for PMDSecurityDomainRule."""

import pytest
from parser.rules.structure.validation.pmd_security_domain import PMDSecurityDomainRule
from parser.models import ProjectContext


class TestPMDSecurityDomainRule:
    """Test cases for PMDSecurityDomainRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = PMDSecurityDomainRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ACTION"
        assert "security" in self.rule.DESCRIPTION.lower()
    
    def test_missing_security_domains_flagged(self):
        """Test that PMD without securityDomains is flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "test"}',
            presentation={"body": {"type": "text", "value": "Hello"}}
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "security" in findings[0].message.lower()
    
    def test_empty_security_domains_flagged(self):
        """Test that PMD with empty securityDomains array is flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "test", "securityDomains": []}',
            securityDomains=[],
            presentation={"body": {"type": "text", "value": "Hello"}}
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "security" in findings[0].message.lower()
    
    def test_with_security_domains_not_flagged(self):
        """Test that PMD with securityDomains is not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "test", "securityDomains": ["My_App_Security"]}',
            securityDomains=["My_App_Security"],
            presentation={"body": {"type": "text", "value": "Hello"}}
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
