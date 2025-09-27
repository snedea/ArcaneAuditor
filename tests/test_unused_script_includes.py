#!/usr/bin/env python3
"""
Tests for ScriptUnusedScriptIncludesRule.
"""

import pytest
from parser.rules.script.unused_code.unused_script_includes import ScriptUnusedScriptIncludesRule
from parser.models import ProjectContext, PMDModel, PMDIncludes


class TestScriptUnusedScriptIncludesRule:
    """Test cases for ScriptUnusedScriptIncludesRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedScriptIncludesRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly defined."""
        assert self.rule.DESCRIPTION == "Ensures included script files are actually used (via script.function() calls)"
        assert self.rule.SEVERITY == "WARNING"
    
    def test_pmd_with_used_script_include(self):
        """Test PMD that includes and uses a script file."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=["util.script"]),
            script="<% let result = util.getCurrentTime(); %>",
            file_path="test.pmd",
            source_content=""
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - script is used
        assert len(findings) == 0
    
    def test_pmd_with_unused_script_include(self):
        """Test PMD that includes but doesn't use a script file."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=["util.script"]),
            script="<% let x = 1; %>",  # No util.* calls
            file_path="test.pmd",
            source_content='{"script": "<% let x = 1; %>"}'
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find unused script include
        assert len(findings) == 1
        assert "util.script" in findings[0].message
        assert "never used" in findings[0].message
        assert "util." in findings[0].message  # Should suggest usage pattern
    
    def test_pmd_with_multiple_script_includes(self):
        """Test PMD with multiple script includes, some used, some not."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=["util.script", "helper.script", "unused.script"]),
            script="<% let time = util.getCurrentTime(); let data = helper.formatData(); %>",
            file_path="test.pmd",
            source_content='{"script": "<% let time = util.getCurrentTime(); let data = helper.formatData(); %>"}'
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find only the unused script
        assert len(findings) == 1
        assert "unused" in findings[0].message
        assert "never used" in findings[0].message
    
    def test_pmd_with_script_calls_in_different_fields(self):
        """Test PMD with script calls in various fields (onLoad, onSubmit, etc.)."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=["util.script", "validator.script"]),
            onLoad="<% util.initialize(); %>",
            script="<% let result = validator.checkData(); %>",
            file_path="test.pmd",
            source_content=""
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - both scripts are used
        assert len(findings) == 0
    
    def test_pmd_with_no_includes(self):
        """Test PMD with no script includes."""
        pmd_model = PMDModel(
            pageId="test-page",
            script="<% let x = 1; %>",
            file_path="test.pmd",
            source_content=""
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - no includes to check
        assert len(findings) == 0
    
    def test_pmd_with_empty_includes(self):
        """Test PMD with empty includes array."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=[]),
            script="<% let x = 1; %>",
            file_path="test.pmd",
            source_content=""
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - no includes to check
        assert len(findings) == 0
    
    def test_script_calls_with_different_patterns(self):
        """Test various script call patterns."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=["util.script", "data.script"]),
            script="""<%
                let time = util.getCurrentTime();
                let formatted = util.formatDate(time);
                data.save(formatted);
                let config = data.getConfig();
            %>""",
            file_path="test.pmd",
            source_content=""
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - both scripts are used multiple times
        assert len(findings) == 0
    
    def test_script_call_detection_edge_cases(self):
        """Test edge cases in script call detection."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=["util.script"]),
            script="""<%
                // These should NOT count as script calls:
                let util = "string";  // Variable named util
                obj.util.something(); // Member access on obj.util
                
                // This SHOULD count:
                util.actualFunction();
            %>""",
            file_path="test.pmd",
            source_content=""
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - util.actualFunction() is a valid call
        assert len(findings) == 0


if __name__ == "__main__":
    pytest.main([__file__])
