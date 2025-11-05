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

    def test_taskreference_widget_without_id_not_flagged(self):
        """Test that taskReference widgets don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "taskReference"
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_edittasks_widget_without_id_not_flagged(self):
        """Test that editTasks widgets don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "editTasks"
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_multiselectcalendar_widget_without_id_not_flagged(self):
        """Test that multiSelectCalendar widgets don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "multiSelectCalendar"
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_bpextender_widget_without_id_not_flagged(self):
        """Test that bpExtender widgets don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "bpExtender"
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_hub_widget_without_id_not_flagged(self):
        """Test that hub widgets don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "hub"
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_image_endpoint_children_without_id_not_flagged(self):
        """Test that image->endPoint entries don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "image",
                    "id": "myImage",
                    "endPoint": {
                        "name": "getImage"
                    }
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_dropdownbutton_values_without_id_not_flagged(self):
        """Test that dropDownButton->values entries don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "dropDownButton",
                    "id": "myDropdown",
                    "values": [
                        {
                            "type": "item",
                            "label": "Option 1"
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_fileuploader_children_without_id_not_flagged(self):
        """Test that fileUploader children don't require id."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "fileUploader",
                    "id": "myUploader",
                    "children": [
                        {
                            "type": "text",
                            "value": "Upload here"
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_dynamiccolumns_without_id_but_columns_need_id(self):
        """Test that dynamicColumns don't have id, but their columns need columnId."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "grid",
                    "id": "myGrid",
                    "dynamicColumns": {
                        "columns": [
                            {
                                "columnId": "col1"
                            }
                        ]
                    }
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        # dynamicColumns object itself doesn't need id, columns inside use columnId
        assert len(findings) == 0

    def test_custom_configuration_exclusions(self):
        """Test that custom widget type exclusions work correctly."""
        # Create a rule with custom exclusions for common widget types
        config = {
            'excluded_widget_types': ['section', 'fieldSet']
        }
        custom_rule = WidgetIdRequiredRule(config)
        
        # Verify built-in exclusions are preserved
        assert 'footer' in custom_rule.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT
        assert 'item' in custom_rule.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT
        
        # Verify custom exclusions are added
        assert 'section' in custom_rule.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT
        assert 'fieldSet' in custom_rule.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT
        
        # Test that custom excluded widgets are not flagged
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '{"presentation": {"body": {"children": [{"type": "section"}, {"type": "fieldSet"}]}}}',
            "presentation": {
                "body": {
                    "children": [
                        {"type": "section"},  # Should not be flagged due to custom exclusion
                        {"type": "fieldSet"}  # Should not be flagged due to custom exclusion
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds["testPage"] = pmd_model
        
        findings = list(custom_rule.analyze(context))
        # Both custom widgets should be excluded and not flagged
        assert len(findings) == 0

    def test_custom_configuration_without_config(self):
        """Test that rule works normally when no config is provided."""
        rule_no_config = WidgetIdRequiredRule()
        
        # Should have built-in exclusions only
        assert 'footer' in rule_no_config.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT
        assert 'section' not in rule_no_config.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT
        
        # Test that non-excluded widgets are still flagged
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '{"presentation": {"body": {"children": [{"type": "section"}]}}}',
            "presentation": {
                "body": {
                    "children": [
                        {"type": "section"}  # Should be flagged since not in built-in exclusions
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds["testPage"] = pmd_model
        
        findings = list(rule_no_config.analyze(context))
        # section should be flagged since it's not in built-in exclusions
        assert len(findings) == 1
        assert "section" in findings[0].message

    def test_widget_in_tabs_without_id_flagged(self):
        """Test that widgets in tabs section without id are flagged."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "presentation": {
    "body": {},
    "tabs": [
      {
        "type": "section",
        "children": [
          {
            "type": "text",
            "value": "Hello"
          }
        ]
      }
    ]
  }
}''',
            "presentation": {
                "body": {},
                "tabs": [
                    {
                        "type": "section",
                        "children": [
                            {
                                "type": "text",
                                "value": "Hello"
                            }
                        ]
                    }
                ]
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        # Both section and text widgets in tabs should be flagged (no IDs)
        assert len(findings) == 2
        # Check that both widgets are found
        text_finding = next((f for f in findings if "text" in f.message.lower()), None)
        section_finding = next((f for f in findings if "section" in f.message.lower()), None)
        assert text_finding is not None
        assert section_finding is not None
        assert "tabs" in text_finding.message.lower() or "tab" in text_finding.message.lower()

    def test_widget_in_tabs_with_id_not_flagged(self):
        """Test that widgets in tabs section with id are not flagged."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "presentation": {
    "body": {},
    "tabs": [
      {
        "type": "section",
        "id": "mySection",
        "children": [
          {
            "type": "text",
            "id": "myText",
            "value": "Hello"
          }
        ]
      }
    ]
  }
}''',
            "presentation": {
                "body": {},
                "tabs": [
                    {
                        "type": "section",
                        "id": "mySection",
                        "children": [
                            {
                                "type": "text",
                                "id": "myText",
                                "value": "Hello"
                            }
                        ]
                    }
                ]
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_multiple_tabs_analyzed(self):
        """Test that multiple tabs are all analyzed."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "presentation": {
    "body": {},
    "tabs": [
      {
        "type": "section",
        "children": [
          {"type": "text", "value": "Tab 1"}
        ]
      },
      {
        "type": "section",
        "children": [
          {"type": "text", "value": "Tab 2"}
        ]
      }
    ]
  }
}''',
            "presentation": {
                "body": {},
                "tabs": [
                    {
                        "type": "section",
                        "children": [
                            {"type": "text", "value": "Tab 1"}
                        ]
                    },
                    {
                        "type": "section",
                        "children": [
                            {"type": "text", "value": "Tab 2"}
                        ]
                    }
                ]
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        # Both section widgets and both text widgets in tabs should be flagged (no IDs)
        # Total: 2 sections + 2 texts = 4 findings
        assert len(findings) == 4


if __name__ == '__main__':
    pytest.main([__file__])
