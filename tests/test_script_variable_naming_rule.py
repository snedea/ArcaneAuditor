#!/usr/bin/env python3
"""Unit tests for ScriptVariableNamingRule."""

import pytest
from parser.rules.script.core.variable_naming import ScriptVariableNamingRule
from parser.models import ProjectContext


class TestScriptVariableNamingRule:
    """Test cases for ScriptVariableNamingRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptVariableNamingRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "naming" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
