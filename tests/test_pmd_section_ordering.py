#!/usr/bin/env python3
"""
Tests for PMDSectionOrderingRule.
"""

import pytest
from parser.rules.structure.validation.pmd_section_ordering import PMDSectionOrderingRule
from parser.models import ProjectContext, PMDModel


class TestPMDSectionOrderingRule:
    """Test cases for PMDSectionOrderingRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = PMDSectionOrderingRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly defined."""
        assert self.rule.DESCRIPTION == "Ensures PMD file root-level sections follow consistent ordering for better readability"
        assert self.rule.SEVERITY == "INFO"
    
    def test_default_section_order(self):
        """Test that default section order is correctly configured."""
        expected_order = [
            "id", "securityDomains", "include", "script", "endPoints", 
            "onSubmit", "outboundData", "onLoad", "presentation"
        ]
        assert self.rule.section_order == expected_order
    
    def test_custom_configuration(self):
        """Test rule with custom configuration."""
        custom_config = {
            "section_order": ["id", "presentation", "script"]
        }
        rule = PMDSectionOrderingRule(config=custom_config)
        
        assert rule.section_order == ["id", "presentation", "script"]
    
    def test_pmd_with_correct_ordering(self):
        """Test PMD file with correct section ordering."""
        # Simulate a PMD with correct ordering
        source_content = """{
  "id": "test-page",
  "include": [],
  "script": "<% %>",
  "endPoints": [],
  "onLoad": "<% %>",
  "presentation": {}
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="correct.pmd",
            source_content=source_content
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - order is correct
        assert len(findings) == 0
    
    def test_pmd_with_incorrect_ordering(self):
        """Test PMD file with incorrect section ordering."""
        # Simulate a PMD with incorrect ordering (script before presentation)
        source_content = """{
  "id": "test-page",
  "script": "<% %>",
  "presentation": {},
  "onLoad": "<% %>"
}"""
        
        pmd_model = PMDModel(
            pageId="test-page", 
            file_path="incorrect.pmd",
            source_content=source_content
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find ordering violations
        assert len(findings) > 0
        
        # Check that violations mention expected order
        violation_messages = [f.message for f in findings]
        assert any("Expected order:" in msg for msg in violation_messages)
        assert any("script" in msg for msg in violation_messages)
    
    def test_pmd_with_partial_sections(self):
        """Test PMD file with only some sections present."""
        source_content = """{
  "id": "test-page",
  "script": "<% %>",
  "presentation": {}
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="partial.pmd", 
            source_content=source_content
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no findings - partial order is correct
        assert len(findings) == 0
    
    def test_pmd_with_unknown_sections(self):
        """Test PMD file with sections not in configured order."""
        source_content = """{
  "id": "test-page",
  "customSection": "custom",
  "presentation": {},
  "anotherCustom": "value"
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="custom.pmd",
            source_content=source_content
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should handle unknown sections gracefully
        # The rule may flag ordering issues, but should not crash
        assert isinstance(findings, list)
        
        # If there are findings, they should be about ordering, not about unknown sections being invalid
        if findings:
            for finding in findings:
                assert "Expected order:" in finding.message or "wrong position" in finding.message
    
    
    def test_pmd_with_invalid_json(self):
        """Test PMD file with invalid JSON (fallback parsing)."""
        source_content = """invalid json content
  "id": "test-page"
  "presentation": {}
"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="invalid.pmd",
            source_content=source_content
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should handle gracefully (may or may not find issues depending on fallback parsing)
        # The important thing is it doesn't crash
        assert isinstance(findings, list)


if __name__ == "__main__":
    pytest.main([__file__])
