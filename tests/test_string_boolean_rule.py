"""Unit tests for StringBooleanRule."""

from parser.rules.structure.validation.string_boolean import StringBooleanRule
from parser.models import PMDModel, PodModel, ProjectContext


class TestStringBooleanRule:
    """Test cases for StringBooleanRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = StringBooleanRule()
        assert rule.DESCRIPTION == "Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans"
        assert rule.SEVERITY == "INFO"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = StringBooleanRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_detect_string_boolean_in_pmd(self):
        """Test detection of string boolean values in PMD files."""
        rule = StringBooleanRule()
        
        # Mock PMD model with string boolean values
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '{\n  "enabled": "true",\n  "disabled": "false"\n}'
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        
        # Check first finding
        assert "Field 'enabled' has string value 'true'" in findings[0].message
        assert findings[0].file_path == "test.pmd"
        assert findings[0].line == 2
        
        # Check second finding
        assert "Field 'disabled' has string value 'false'" in findings[1].message
        assert findings[1].file_path == "test.pmd"
        assert findings[1].line == 3

    def test_detect_string_boolean_in_pod(self):
        """Test detection of string boolean values in POD files."""
        rule = StringBooleanRule()
        
        # Mock POD model with string boolean values
        pod_data = {
            "podId": "test",
            "file_path": "test.pod",
            "source_content": '{\n  "visible": "true",\n  "hidden": "false"\n}',
            "seed": {
                "template": {}
            }
        }
        
        pod_model = PodModel(**pod_data)
        context = ProjectContext()
        context.pods = {"test": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        
        # Check first finding
        assert "Field 'visible' has string value 'true'" in findings[0].message
        assert findings[0].file_path == "test.pod"
        assert findings[0].line == 2
        
        # Check second finding
        assert "Field 'hidden' has string value 'false'" in findings[1].message
        assert findings[1].file_path == "test.pod"
        assert findings[1].line == 3

    def test_ignore_actual_booleans(self):
        """Test that actual boolean values are ignored."""
        rule = StringBooleanRule()
        
        # Mock PMD model with actual boolean values
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '{\n  "enabled": true,\n  "disabled": false\n}'
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_ignore_empty_source_content(self):
        """Test that empty source content is ignored."""
        rule = StringBooleanRule()
        
        # Mock PMD model with empty source content
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": ""
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_ignore_none_source_content(self):
        """Test that None source content is ignored."""
        rule = StringBooleanRule()
        
        # Mock PMD model with empty source content (default behavior)
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd"
            # source_content defaults to empty string
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_multiple_string_booleans_same_line(self):
        """Test detection of multiple string boolean values on the same line."""
        rule = StringBooleanRule()
        
        # Mock PMD model with multiple string boolean values on same line
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '{"enabled": "true", "disabled": "false"}'
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        
        # Both findings should be on line 1
        assert all(finding.line == 1 for finding in findings)

    def test_mixed_boolean_types(self):
        """Test detection with mixed boolean types."""
        rule = StringBooleanRule()
        
        # Mock PMD model with mixed boolean types
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '{\n  "stringTrue": "true",\n  "actualTrue": true,\n  "stringFalse": "false",\n  "actualFalse": false\n}'
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        
        # Only string booleans should be detected
        assert "stringTrue" in findings[0].message
        assert "stringFalse" in findings[1].message
