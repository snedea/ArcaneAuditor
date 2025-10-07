#!/usr/bin/env python3
"""Unit tests for ScriptUnusedVariableRule."""

import pytest
from parser.rules.script.unused_code.unused_variables import ScriptUnusedVariableRule
from parser.models import ProjectContext


class TestScriptUnusedVariableRule:
    """Test cases for ScriptUnusedVariableRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedVariableRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "variable" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
