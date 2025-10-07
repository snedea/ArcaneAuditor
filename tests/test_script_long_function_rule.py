#!/usr/bin/env python3
"""Unit tests for ScriptLongFunctionRule."""

import pytest
from parser.rules.script.complexity.long_function import ScriptLongFunctionRule
from parser.models import ProjectContext


class TestScriptLongFunctionRule:
    """Test cases for ScriptLongFunctionRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptLongFunctionRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "function" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
