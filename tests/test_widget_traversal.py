#!/usr/bin/env python3
"""
Tests for widget traversal in presentation structures.

Verifies that traverse_presentation_structure correctly finds all widgets
including nested ones in cellTemplate, columns, children, etc.
"""

import pytest
from parser.models import PMDModel
from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule


class TestWidgetTraversal:
    """Test cases for widget traversal functionality."""
    
    def test_simple_body_widget_traversal(self):
        """Test traversal of simple body widget."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "text",
                    "id": "myText"
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        
        rule = WidgetIdRequiredRule()
        widgets = list(rule.traverse_presentation_structure(pmd_model.presentation.body, 'body'))
        
        # Should find exactly 1 widget (the text widget)
        assert len(widgets) == 1
        assert widgets[0][0]['type'] == 'text'
        assert widgets[0][0]['id'] == 'myText'
    
    def test_children_array_traversal(self):
        """Test traversal of widgets in children array."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "section",
                    "id": "mySection",
                    "children": [
                        {"type": "text", "id": "text1"},
                        {"type": "text", "id": "text2"}
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        
        rule = WidgetIdRequiredRule()
        widgets = list(rule.traverse_presentation_structure(pmd_model.presentation.body, 'body'))
        
        # Should find 3 widgets: section + 2 text children
        assert len(widgets) == 3
        widget_types = [w[0]['type'] for w in widgets]
        assert 'section' in widget_types
        assert widget_types.count('text') == 2
    
    def test_celltemplate_traversal(self):
        """Test traversal of widgets inside cellTemplate."""
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
                                "id": "cellText"
                            }
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        
        rule = WidgetIdRequiredRule()
        widgets = list(rule.traverse_presentation_structure(pmd_model.presentation.body, 'body'))
        
        # Should find: grid + column dict + cellTemplate text widget
        assert len(widgets) >= 2  # At minimum: grid and cellTemplate widget
        widget_types = [w[0].get('type') for w in widgets if 'type' in w[0]]
        assert 'grid' in widget_types
        assert 'text' in widget_types
        
        # Verify cellTemplate widget is found
        celltemplate_widgets = [w for w in widgets if w[0].get('type') == 'text']
        assert len(celltemplate_widgets) == 1
        assert celltemplate_widgets[0][0].get('id') == 'cellText'
    
    def test_no_duplicate_widgets(self):
        """Test that widgets are not yielded multiple times."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "section",
                    "id": "mySection",
                    "children": [
                        {
                            "type": "grid",
                            "id": "myGrid",
                            "columns": [
                                {
                                    "columnId": "col1",
                                    "cellTemplate": {
                                        "type": "text",
                                        "id": "cellText"
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        
        rule = WidgetIdRequiredRule()
        widgets = list(rule.traverse_presentation_structure(pmd_model.presentation.body, 'body'))
        
        # Count how many times each widget appears by ID
        widget_ids = [w[0].get('id', w[0].get('columnId', 'no-id')) for w in widgets]
        
        # Each ID should appear exactly once
        assert widget_ids.count('mySection') == 1, "Section yielded multiple times"
        assert widget_ids.count('myGrid') == 1, "Grid yielded multiple times"
        assert widget_ids.count('cellText') == 1, "Cell template widget yielded multiple times"
    
    def test_deeply_nested_structure(self):
        """Test traversal of deeply nested widget structures."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "section",
                    "id": "outer",
                    "children": [
                        {
                            "type": "section",
                            "id": "middle",
                            "children": [
                                {
                                    "type": "text",
                                    "id": "inner"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        
        rule = WidgetIdRequiredRule()
        widgets = list(rule.traverse_presentation_structure(pmd_model.presentation.body, 'body'))
        
        # Should find all 3 nested widgets
        assert len(widgets) == 3
        widget_ids = [w[0]['id'] for w in widgets]
        assert 'outer' in widget_ids
        assert 'middle' in widget_ids
        assert 'inner' in widget_ids
    
    def test_multiple_columns_with_celltemplates(self):
        """Test traversal of grid with multiple columns containing cellTemplates."""
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
                                "id": "cell1"
                            }
                        },
                        {
                            "columnId": "col2",
                            "cellTemplate": {
                                "type": "richText",
                                "id": "cell2"
                            }
                        },
                        {
                            "columnId": "col3"
                            # No cellTemplate
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        
        rule = WidgetIdRequiredRule()
        widgets = list(rule.traverse_presentation_structure(pmd_model.presentation.body, 'body'))
        
        # Should find: grid + 3 columns + 2 cellTemplate widgets
        widget_types = [w[0].get('type') for w in widgets]
        
        # Verify grid is found
        assert 'grid' in widget_types
        
        # Verify both cellTemplate widgets are found
        celltemplate_widgets = [w for w in widgets if w[0].get('id') in ['cell1', 'cell2']]
        assert len(celltemplate_widgets) == 2
        
        # Verify each cellTemplate widget is unique
        cell_ids = [w[0]['id'] for w in celltemplate_widgets]
        assert 'cell1' in cell_ids
        assert 'cell2' in cell_ids
    
    def test_mixed_structure_with_grid_and_sections(self):
        """Test traversal of complex structure with grids, sections, and cellTemplates."""
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "type": "section",
                    "id": "mainSection",
                    "children": [
                        {
                            "type": "text",
                            "id": "header"
                        },
                        {
                            "type": "grid",
                            "id": "dataGrid",
                            "columns": [
                                {
                                    "columnId": "name",
                                    "cellTemplate": {
                                        "type": "text",
                                        "id": "nameCell"
                                    }
                                }
                            ]
                        },
                        {
                            "type": "text",
                            "id": "footer"
                        }
                    ]
                }
            }
        }
        pmd_model = PMDModel(**pmd_data)
        
        rule = WidgetIdRequiredRule()
        widgets = list(rule.traverse_presentation_structure(pmd_model.presentation.body, 'body'))
        
        # Should find: mainSection + header + dataGrid + column + nameCell + footer
        widget_ids = [w[0].get('id', w[0].get('columnId')) for w in widgets if 'id' in w[0] or 'columnId' in w[0]]
        
        assert 'mainSection' in widget_ids
        assert 'header' in widget_ids
        assert 'dataGrid' in widget_ids
        assert 'nameCell' in widget_ids
        assert 'footer' in widget_ids
        
        # Verify no duplicates
        assert len(widget_ids) == len(set(widget_ids)), "Found duplicate widgets in traversal"


if __name__ == '__main__':
    pytest.main([__file__])
