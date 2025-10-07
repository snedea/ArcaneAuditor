#!/usr/bin/env python3
"""Unit tests for ScriptFunctionReturnConsistencyRule."""

import pytest
from parser.rules.script.logic.return_consistency import ScriptFunctionReturnConsistencyRule
from parser.models import ProjectContext


class TestScriptFunctionReturnConsistencyRule:
    """Test cases for ScriptFunctionReturnConsistencyRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptFunctionReturnConsistencyRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "return" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
