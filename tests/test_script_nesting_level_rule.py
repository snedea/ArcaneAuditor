#!/usr/bin/env python3
"""Unit tests for ScriptNestingLevelRule."""

import pytest
from parser.rules.script.complexity.nesting_level import ScriptNestingLevelRule
from parser.models import ProjectContext


class TestScriptNestingLevelRule:
    """Test cases for ScriptNestingLevelRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptNestingLevelRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "nesting" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
