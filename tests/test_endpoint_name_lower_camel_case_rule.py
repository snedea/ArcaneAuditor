#!/usr/bin/env python3
"""Unit tests for EndpointNameLowerCamelCaseRule."""

import pytest
from parser.rules.structure.endpoints.endpoint_name_lower_camel_case import EndpointNameLowerCamelCaseRule
from parser.models import ProjectContext


class TestEndpointNameLowerCamelCaseRule:
    """Test cases for EndpointNameLowerCamelCaseRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointNameLowerCamelCaseRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "EndpointNameLowerCamelCaseRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "ACTION"
        assert "endpoint" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
