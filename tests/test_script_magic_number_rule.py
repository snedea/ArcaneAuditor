#!/usr/bin/env python3
"""Unit tests for ScriptMagicNumberRule."""

import pytest
from parser.rules.script.logic.magic_numbers import ScriptMagicNumberRule
from parser.models import ProjectContext


class TestScriptMagicNumberRule:
    """Test cases for ScriptMagicNumberRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptMagicNumberRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "magic" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
