#!/usr/bin/env python3
"""Unit tests for WidgetIdRequiredRule."""

import pytest
from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule
from parser.models import ProjectContext, PMDModel


class TestWidgetIdRequiredRule:
    """Test cases for WidgetIdRequiredRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = WidgetIdRequiredRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ACTION"
        assert "widget" in self.rule.DESCRIPTION.lower()
    
    def test_widget_with_id_not_flagged(self):
        """Test that widgets with id are not flagged."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "text",
                    "id": "myText",
                    "value": "Hello"
                }
            },
            "source_content": '''{
  "presentation": {
    "body": {
      "type": "text",
      "id": "myText",
      "value": "Hello"
    }
  }
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_widget_without_id_flagged(self):
        """Test that widgets without id are flagged."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "text",
                    "value": "Hello"
                }
            },
            "source_content": '''{
  "presentation": {
    "body": {
      "type": "text",
      "value": "Hello"
    }
  }
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "missing required 'id' field" in findings[0].message
        assert "type 'text'" in findings[0].message
    
    def test_celltemplate_widget_without_id_flagged(self):
        """Test that widgets inside cellTemplate are checked for missing id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "grid",
                    "id": "myGrid",
                    "columns": [
                        {
                            "columnId": "col1",
                            "cellTemplate": {
                                "type": "text",
                                "value": "Hello"
                            }
                        }
                    ]
                }
            },
            "source_content": '''{
  "presentation": {
    "body": {
      "type": "grid",
      "id": "myGrid",
      "columns": [
        {
          "columnId": "col1",
          "cellTemplate": {
            "type": "text",
            "value": "Hello"
          }
        }
      ]
    }
  }
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "missing required 'id' field" in findings[0].message
        assert "type 'text'" in findings[0].message
    
    def test_excluded_widget_types_not_flagged(self):
        """Test that excluded widget types without id are not flagged."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "footer"
                }
            },
            "source_content": '''{
  "presentation": {
    "body": {
      "type": "footer"
    }
  }
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_column_with_columnid_not_flagged(self):
        """Test that columns with columnId are not flagged as missing id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "grid",
                    "id": "myGrid",
                    "columns": [
                        {
                            "columnId": "col1"
                        }
                    ]
                }
            },
            "source_content": '''{
  "presentation": {
    "body": {
      "type": "grid",
      "id": "myGrid",
      "columns": [{"columnId": "col1"}]
    }
  }
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
