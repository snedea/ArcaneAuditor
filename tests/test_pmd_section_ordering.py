#!/usr/bin/env python3
"""
Tests for PMDSectionOrderingRule.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
        
        # Check that violations mention expected order with numbered format
        violation_messages = [f.message for f in findings]
        assert any("Expected:" in msg for msg in violation_messages)
        assert any("Actual:" in msg for msg in violation_messages)
        assert any("1." in msg for msg in violation_messages)  # Check for numbered format
        assert any("script" in msg for msg in violation_messages)
    
    def test_numbered_output_format(self):
        """Test that the output format includes numbered prefixes."""
        # Create PMD with clearly wrong order
        source_content = """{
  "presentation": {},
  "id": "test-page",
  "script": "<% %>"
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="wrong_order.pmd",
            source_content=source_content
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find ordering violations
        assert len(findings) > 0
        
        # Check the specific format
        violation_message = findings[0].message
        assert "Expected:" in violation_message
        assert "Actual:" in violation_message
        assert "1. id" in violation_message  # First expected section
        assert "2. script" in violation_message  # Second expected section
        assert "3. presentation" in violation_message  # Third expected section
        
        # Check that actual order shows the wrong sequence
        assert "1. presentation" in violation_message  # First actual section (wrong)
        assert "2. id" in violation_message  # Second actual section
        assert "3. script" in violation_message  # Third actual section
    
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
                assert "Expected:" in finding.message or "wrong position" in finding.message
    
    
    def test_pmd_with_invalid_json(self):
        """Test PMD file with invalid JSON (should be handled by compiler)."""
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
        
        # Since we removed the fallback parsing, invalid JSON should be caught
        # by the exception handler in _analyze_pmd_section_order
        findings = list(self.rule.analyze(self.context))
        
        # Should handle gracefully and return empty findings list
        # (the exception is caught and logged as a warning)
        assert isinstance(findings, list)
        assert len(findings) == 0


def run_tests():
    """Run all tests."""
    test_instance = TestPMDSectionOrderingRule()
    
    try:
        test_instance.setup_method()
        test_instance.test_rule_metadata()
        test_instance.test_default_section_order()
        test_instance.test_custom_configuration()
        test_instance.test_pmd_with_correct_ordering()
        test_instance.test_pmd_with_incorrect_ordering()
        test_instance.test_pmd_with_partial_sections()
        test_instance.test_pmd_with_unknown_sections()
        test_instance.test_pmd_with_invalid_json()
        
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
