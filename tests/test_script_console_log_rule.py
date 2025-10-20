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
    
    def test_console_debug_detected(self):
        """Test that console.debug is detected."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const userName = 'test';\n  console.debug(userName);\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "console" in findings[0].message
    
    def test_console_warn_detected(self):
        """Test that console.warn is detected."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  console.warn('Warning message');\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "console" in findings[0].message
    
    def test_console_info_detected(self):
        """Test that console.info is detected."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  console.info('Info message');\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "console" in findings[0].message
    
    def test_console_error_detected(self):
        """Test that console.error is detected."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  console.error('Error occurred');\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "console" in findings[0].message
    
    def test_no_console_statements_no_violations(self):
        """Test that scripts without console statements have no violations."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const userName = 'test';\n  return userName;\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
