#!/usr/bin/env python3
"""Unit tests for ScriptConsoleLogRule."""

import pytest
from parser.rules.script.core.console_log import ScriptConsoleLogRule
from parser.models import ProjectContext


class TestScriptConsoleLogRule:
    """Test cases for ScriptConsoleLogRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptConsoleLogRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ACTION"
        assert "console" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])
