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


if __name__ == '__main__':
    pytest.main([__file__])