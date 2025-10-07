#!/usr/bin/env python3
"""Unit tests for HardcodedWidRule."""

import pytest
from parser.rules.structure.validation.hardcoded_wid import HardcodedWidRule
from parser.models import ProjectContext


class TestHardcodedWidRule:
    """Test cases for HardcodedWidRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = HardcodedWidRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "HardcodedWidRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "ADVICE"
        assert "wid" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
