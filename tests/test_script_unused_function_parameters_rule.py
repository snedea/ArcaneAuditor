#!/usr/bin/env python3
"""Unit tests for ScriptUnusedFunctionParametersRule."""

import pytest
from parser.rules.script.unused_code.unused_parameters import ScriptUnusedFunctionParametersRule
from parser.models import ProjectContext


class TestScriptUnusedFunctionParametersRule:
    """Test cases for ScriptUnusedFunctionParametersRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedFunctionParametersRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ACTION"
        assert "parameter" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
