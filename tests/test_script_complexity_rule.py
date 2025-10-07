#!/usr/bin/env python3
"""Unit tests for ScriptComplexityRule."""

import pytest
from parser.rules.script.complexity.cyclomatic_complexity import ScriptComplexityRule
from parser.models import ProjectContext


class TestScriptComplexityRule:
    """Test cases for ScriptComplexityRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptComplexityRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "complexity" in self.rule.DESCRIPTION.lower()


if __name__ == '__main__':
    pytest.main([__file__])