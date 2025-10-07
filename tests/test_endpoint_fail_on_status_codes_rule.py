#!/usr/bin/env python3
"""Unit tests for EndpointFailOnStatusCodesRule."""

import pytest
from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import EndpointFailOnStatusCodesRule
from parser.models import ProjectContext


class TestEndpointFailOnStatusCodesRule:
    """Test cases for EndpointFailOnStatusCodesRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointFailOnStatusCodesRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ACTION"
        assert "status" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
