"""
Unit tests for the Finding class.
"""
import pytest
from parser.rules.base import Finding, Rule


class MockRule(Rule):
    """Mock rule for testing Finding class."""
    ID = "TEST001"
    DESCRIPTION = "Test rule for unit testing"
    SEVERITY = "WARNING"
    
    def analyze(self, context):
        """Mock analysis that yields test findings."""
        yield from []


class TestFinding:
    """Test cases for Finding class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = MockRule()
    
    def test_finding_creation(self):
        """Test basic Finding creation."""
        finding = Finding(
            rule=self.rule,
            message="Test finding message",
            line=10,
            column=5,
            file_path="test.pmd"
        )
        
        assert finding.rule == self.rule
        assert finding.message == "Test finding message"
        assert finding.line == 10
        assert finding.column == 5
        assert finding.file_path == "test.pmd"
    
    def test_finding_default_values(self):
        """Test Finding creation with default values."""
        finding = Finding(
            rule=self.rule,
            message="Test finding message"
        )
        
        assert finding.rule == self.rule
        assert finding.message == "Test finding message"
        assert finding.line == 0
        assert finding.column == 0
        assert finding.file_path == ""
    
    def test_finding_derived_fields(self):
        """Test that derived fields are set correctly."""
        finding = Finding(
            rule=self.rule,
            message="Test finding message",
            line=15,
            column=8,
            file_path="example.pmd"
        )
        
        # Check derived fields
        assert finding.rule_id == "MockRule"
        assert finding.rule_description == "Test rule for unit testing"
        assert finding.severity == "WARNING"
    
    def test_finding_repr(self):
        """Test Finding string representation."""
        finding = Finding(
            rule=self.rule,
            message="Test finding message",
            line=20,
            column=12,
            file_path="sample.pmd"
        )
        
        expected_repr = "[MockRule:20] (WARNING) in 'sample.pmd': Test finding message"
        assert repr(finding) == expected_repr
    
    def test_finding_repr_no_file_path(self):
        """Test Finding string representation without file path."""
        finding = Finding(
            rule=self.rule,
            message="Test finding message",
            line=25,
            column=3
        )
        
        expected_repr = "[MockRule:25] (WARNING) in '': Test finding message"
        assert repr(finding) == expected_repr
    
    def test_finding_equality(self):
        """Test Finding equality comparison."""
        finding1 = Finding(
            rule=self.rule,
            message="Test finding message",
            line=10,
            column=5,
            file_path="test.pmd"
        )
        
        finding2 = Finding(
            rule=self.rule,
            message="Test finding message",
            line=10,
            column=5,
            file_path="test.pmd"
        )
        
        # Findings with same values should be equal
        assert finding1.rule == finding2.rule
        assert finding1.message == finding2.message
        assert finding1.line == finding2.line
        assert finding1.column == finding2.column
        assert finding1.file_path == finding2.file_path
    
    def test_finding_inequality(self):
        """Test Finding inequality comparison."""
        finding1 = Finding(
            rule=self.rule,
            message="Test finding message 1",
            line=10,
            column=5,
            file_path="test1.pmd"
        )
        
        finding2 = Finding(
            rule=self.rule,
            message="Test finding message 2",
            line=15,
            column=8,
            file_path="test2.pmd"
        )
        
        # Findings with different values should not be equal
        assert finding1.message != finding2.message
        assert finding1.line != finding2.line
        assert finding1.column != finding2.column
        assert finding1.file_path != finding2.file_path
    
    def test_finding_with_different_rule(self):
        """Test Finding with different rule."""
        rule1 = MockRule()
        rule1.ID = "RULE001"
        rule1.SEVERITY = "SEVERE"
        
        rule2 = MockRule()
        rule2.ID = "RULE002"
        rule2.SEVERITY = "INFO"
        
        finding1 = Finding(
            rule=rule1,
            message="Test finding message",
            line=10,
            column=5
        )
        
        finding2 = Finding(
            rule=rule2,
            message="Test finding message",
            line=10,
            column=5
        )
        
        assert finding1.rule_id == "MockRule"
        assert finding1.severity == "SEVERE"
        assert finding2.rule_id == "MockRule"
        assert finding2.severity == "INFO"
    
    def test_finding_attributes(self):
        """Test that Finding has all expected attributes."""
        finding = Finding(
            rule=self.rule,
            message="Test finding message",
            line=10,
            column=5,
            file_path="test.pmd"
        )
        
        # Check all expected attributes exist
        assert hasattr(finding, 'rule')
        assert hasattr(finding, 'message')
        assert hasattr(finding, 'line')
        assert hasattr(finding, 'column')
        assert hasattr(finding, 'file_path')
        assert hasattr(finding, 'rule_id')
        assert hasattr(finding, 'rule_description')
        assert hasattr(finding, 'severity')
    
    def test_finding_dataclass_behavior(self):
        """Test that Finding behaves like a dataclass."""
        finding = Finding(
            rule=self.rule,
            message="Test finding message",
            line=10,
            column=5,
            file_path="test.pmd"
        )
        
        # Should be able to access fields as attributes
        assert finding.rule == self.rule
        assert finding.message == "Test finding message"
        assert finding.line == 10
        assert finding.column == 5
        assert finding.file_path == "test.pmd"


if __name__ == "__main__":
    pytest.main([__file__])
