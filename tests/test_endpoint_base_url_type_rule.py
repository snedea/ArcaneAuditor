#!/usr/bin/env python3
"""Unit tests for EndpointBaseUrlTypeRule."""

import pytest
from parser.rules.structure.endpoints.endpoint_url_base_url_type import EndpointBaseUrlTypeRule
from parser.models import ProjectContext


class TestEndpointBaseUrlTypeRule:
    """Test cases for EndpointBaseUrlTypeRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointBaseUrlTypeRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "url" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
