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


if __name__ == '__main__':
    pytest.main([__file__])
