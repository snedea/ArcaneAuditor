"""Unit tests for MultipleStringInterpolatorsRule."""

from parser.rules.structure.validation.multiple_string_interpolators import MultipleStringInterpolatorsRule
from parser.models import PMDModel, PodModel, ProjectContext


class TestMultipleStringInterpolatorsRule:
    """Test cases for MultipleStringInterpolatorsRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = MultipleStringInterpolatorsRule()
        assert rule.ID == "MultipleStringInterpolatorsRule"
        assert rule.DESCRIPTION == "Detects multiple string interpolators in a single string which should use template literals instead"
        assert rule.SEVERITY == "ADVICE"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = MultipleStringInterpolatorsRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_single_interpolator_not_flagged(self):
        """Test that strings with single interpolator are not flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "value": "Hello <% name %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_multiple_interpolators_flagged(self):
        """Test that strings with multiple interpolators are flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "value": "My name is <% name %> and I like <% food %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "template literal" in findings[0].message.lower()
        assert findings[0].file_path == "test.pmd"

    def test_three_interpolators_flagged(self):
        """Test that strings with three interpolators are flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "value": "Name: <% name %>, Age: <% age %>, City: <% city %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1

    def test_multiple_strings_with_multiple_interpolators(self):
        """Test that multiple strings with multiple interpolators are all flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "value": "First: <% a %> and Second: <% b %>"
    },
    {
      "type": "text",
      "value": "Third: <% c %> and Fourth: <% d %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2

    def test_pod_with_multiple_interpolators(self):
        """Test that POD files with multiple interpolators are flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "testPod",
            "file_path": "test.pod",
            "seed": {
                "template": {
                    "type": "text",
                    "value": "Name: <% name %>, Job: <% job %>"
                }
            },
            "source_content": '''{
  "seed": {
    "template": {
      "type": "text",
      "value": "Name: <% name %>, Job: <% job %>"
    }
  }
}'''
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"testPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].file_path == "test.pod"

    def test_no_interpolators_not_flagged(self):
        """Test that strings without interpolators are not flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "value": "Static text with no interpolation"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_template_literal_already_used_not_flagged(self):
        """Test that template literals (backticks with {{}}) are not flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "value": "<% `My name is {{name}} and I like {{food}}` %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_nested_interpolators_in_different_contexts(self):
        """Test that only string-level interpolators are counted (not nested in scripts)."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "label": "Name: <% firstName %> <% lastName %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "template literal" in findings[0].message.lower()

    def test_file_without_source_content_no_crash(self):
        """Test that files without source_content don't crash."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0
    
    def test_multiline_string_with_multiple_interpolators(self):
        """Test that multi-line strings with multiple interpolators are flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "value": "Hello <% name %>
                and welcome <% title %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "template literal" in findings[0].message.lower()
    
    def test_multiline_string_with_three_interpolators(self):
        """Test that multi-line strings with three interpolators are flagged."""
        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "text",
      "label": "Line 1: <% first %>
Line 2: <% second %>
Line 3: <% third %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "3 interpolators" in findings[0].message

