#!/usr/bin/env python3
"""Unit tests for ScriptEmptyFunctionRule."""

import pytest
from parser.rules.script.unused_code.empty_functions import ScriptEmptyFunctionRule
from parser.models import ProjectContext


class TestScriptEmptyFunctionRule:
    """Test cases for ScriptEmptyFunctionRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptEmptyFunctionRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "empty" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])