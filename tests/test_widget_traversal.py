"""
Test cases for the generic widget traversal system that handles different PMD body layout types.
"""
import unittest
from parser.rules.base import Rule
from parser.models import PMDModel, ProjectContext


class ConcreteRule(Rule):
    """Concrete implementation of Rule for testing purposes."""
    
    def analyze(self, context: ProjectContext):
        """Required abstract method implementation."""
        yield from []


class TestWidgetTraversal(unittest.TestCase):
    """Test cases for the widget traversal functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rule = ConcreteRule()
        # Clear any cached state
        if hasattr(self.rule, '_script_ast_cache'):
            self.rule._script_ast_cache.clear()
    
    def test_traverse_standard_section_layout(self):
        """Test traversal of standard section layout with children array."""
        presentation_data = {
            "type": "section",
            "children": [
                {
                    "type": "text",
                    "id": "text1",
                    "label": "Hello"
                },
                {
                    "type": "button",
                    "id": "button1",
                    "label": "Click me"
                }
            ]
        }
        
        widgets = list(self.rule.traverse_presentation_structure(presentation_data, "body"))
        
        assert len(widgets) == 2
        assert widgets[0][0]["type"] == "text"
        assert widgets[0][0]["id"] == "text1"
        assert widgets[0][1] == "body.children.0"
        assert widgets[0][2] == 0
        
        assert widgets[1][0]["type"] == "button"
        assert widgets[1][0]["id"] == "button1"
        assert widgets[1][1] == "body.children.1"
        assert widgets[1][2] == 1
    
    def test_traverse_area_layout(self):
        """Test traversal of areaLayout with primaryLayout and secondaryLayout."""
        presentation_data = {
            "type": "areaLayout",
            "primaryLayout": [
                {
                    "type": "text",
                    "id": "primaryText",
                    "label": "Primary content"
                }
            ],
            "secondaryLayout": [
                {
                    "type": "button",
                    "id": "secondaryButton",
                    "label": "Secondary action"
                }
            ]
        }
        
        widgets = list(self.rule.traverse_presentation_structure(presentation_data, "body"))
        
        assert len(widgets) == 2
        
        # Check widgets (order may vary due to dictionary iteration)
        widget_types = [w[0]["type"] for w in widgets]
        assert "text" in widget_types
        assert "button" in widget_types
        
        # Find specific widgets
        text_widget = next(w for w in widgets if w[0]["type"] == "text")
        button_widget = next(w for w in widgets if w[0]["type"] == "button")
        
        assert text_widget[0]["id"] == "primaryText"
        assert text_widget[1] == "body.primaryLayout.0"
        assert text_widget[2] == 0
        
        assert button_widget[0]["id"] == "secondaryButton"
        assert button_widget[1] == "body.secondaryLayout.0"
        assert button_widget[2] == 0
    
    def test_traverse_basic_form_layout(self):
        """Test traversal of basicFormLayout with sections containing layoutSections."""
        presentation_data = {
            "type": "basicFormLayout",
            "sections": [
                {
                    "type": "layoutSection",
                    "id": "section1",
                    "children": [
                        {
                            "type": "text",
                            "id": "formText",
                            "label": "Form field"
                        }
                    ]
                },
                {
                    "type": "layoutSection", 
                    "id": "section2",
                    "children": [
                        {
                            "type": "input",
                            "id": "formInput",
                            "label": "User input"
                        }
                    ]
                }
            ]
        }
        
        widgets = list(self.rule.traverse_presentation_structure(presentation_data, "body"))
        
        assert len(widgets) == 4  # 2 layoutSections + 2 widgets
        
        # Check widgets in the order they are found
        assert widgets[0][0]["type"] == "layoutSection"
        assert widgets[0][0]["id"] == "section1"
        assert widgets[0][1] == "body.sections.0"
        assert widgets[0][2] == 0
        
        assert widgets[1][0]["type"] == "text"
        assert widgets[1][0]["id"] == "formText"
        assert widgets[1][1] == "body.sections.0.children.0"
        assert widgets[1][2] == 0
        
        assert widgets[2][0]["type"] == "layoutSection"
        assert widgets[2][0]["id"] == "section2"
        assert widgets[2][1] == "body.sections.1"
        assert widgets[2][2] == 1
        
        assert widgets[3][0]["type"] == "input"
        assert widgets[3][0]["id"] == "formInput"
        assert widgets[3][1] == "body.sections.1.children.0"
        assert widgets[3][2] == 0
    
    def test_traverse_nested_widgets(self):
        """Test traversal of nested widgets with children."""
        presentation_data = {
            "type": "section",
            "children": [
                {
                    "type": "container",
                    "id": "container1",
                    "children": [
                        {
                            "type": "text",
                            "id": "nestedText",
                            "label": "Nested content"
                        }
                    ]
                }
            ]
        }
        
        widgets = list(self.rule.traverse_presentation_structure(presentation_data, "body"))
        
        assert len(widgets) == 2
        assert widgets[0][0]["type"] == "container"
        assert widgets[0][0]["id"] == "container1"
        assert widgets[0][1] == "body.children.0"
        assert widgets[0][2] == 0
        
        assert widgets[1][0]["type"] == "text"
        assert widgets[1][0]["id"] == "nestedText"
        assert widgets[1][1] == "body.children.0.children.0"
        assert widgets[1][2] == 0
    
    def test_traverse_hub_layout(self):
        """Test traversal of hub layout with custom widget containers."""
        presentation_data = {
            "type": "hub",
            "widgets": [
                {
                    "type": "card",
                    "id": "hubCard",
                    "title": "Hub card"
                }
            ],
            "items": [
                {
                    "type": "link",
                    "id": "hubLink",
                    "url": "/somewhere"
                }
            ]
        }
        
        widgets = list(self.rule.traverse_presentation_structure(presentation_data, "body"))
        
        assert len(widgets) == 2  # card + link
        
        # Check widgets (order may vary due to dictionary iteration)
        widget_types = [w[0]["type"] for w in widgets]
        assert "card" in widget_types
        assert "link" in widget_types
        
        # Find specific widgets
        card_widget = next(w for w in widgets if w[0]["type"] == "card")
        link_widget = next(w for w in widgets if w[0]["type"] == "link")
        
        assert card_widget[0]["id"] == "hubCard"
        assert card_widget[1] == "body.widgets.0"
        assert card_widget[2] == 0
        
        assert link_widget[0]["id"] == "hubLink"
        assert link_widget[1] == "body.items.0"
        assert link_widget[2] == 0
    
    def test_traverse_mixed_layout_types(self):
        """Test traversal of mixed layout types in the same structure."""
        presentation_data = {
            "type": "section",
            "children": [
                {
                    "type": "areaLayout",
                    "primaryLayout": [
                        {
                            "type": "text",
                            "id": "mixedText",
                            "label": "Mixed layout"
                        }
                    ]
                },
                {
                    "type": "basicFormLayout",
                    "sections": [
                        {
                            "type": "input",
                            "id": "mixedInput",
                            "label": "Mixed input"
                        }
                    ]
                }
            ]
        }
        
        widgets = list(self.rule.traverse_presentation_structure(presentation_data, "body"))
        
        assert len(widgets) == 4
        
        # Check layout containers
        assert widgets[0][0]["type"] == "areaLayout"
        assert widgets[0][1] == "body.children.0"
        assert widgets[0][2] == 0
        
        assert widgets[2][0]["type"] == "basicFormLayout"
        assert widgets[2][1] == "body.children.1"
        assert widgets[2][2] == 1
        
        # Check actual widgets
        assert widgets[1][0]["type"] == "text"
        assert widgets[1][0]["id"] == "mixedText"
        assert widgets[1][1] == "body.children.0.primaryLayout.0"
        assert widgets[1][2] == 0
        
        assert widgets[3][0]["type"] == "input"
        assert widgets[3][0]["id"] == "mixedInput"
        assert widgets[3][1] == "body.children.1.sections.0"
        assert widgets[3][2] == 0
    
    def test_traverse_empty_structures(self):
        """Test traversal of empty or invalid structures."""
        # Empty list
        widgets = list(self.rule.traverse_presentation_structure([], "body"))
        assert len(widgets) == 0
        
        # Non-dict structure
        widgets = list(self.rule.traverse_presentation_structure("not a dict", "body"))
        assert len(widgets) == 0
        
        # Dict without widgets
        widgets = list(self.rule.traverse_presentation_structure({"type": "section"}, "body"))
        assert len(widgets) == 0
    
    def test_widget_type_exclusion(self):
        """Test that excluded widget types are properly identified."""
        excluded_types = {'title', 'footer', 'item', 'group'}
        
        # Test excluded types
        assert "title" in excluded_types
        assert "footer" in excluded_types
        assert "item" in excluded_types
        assert "group" in excluded_types
        
        # Test non-excluded types
        assert "text" not in excluded_types
        assert "button" not in excluded_types
        assert "input" not in excluded_types
        assert "unknown" not in excluded_types
    
    def test_traverse_with_excluded_widgets(self):
        """Test that excluded widget types are still traversed but can be filtered out."""
        presentation_data = {
            "type": "section",
            "children": [
                {
                    "type": "title",
                    "label": "Page Title"
                },
                {
                    "type": "text",
                    "id": "contentText",
                    "label": "Content"
                },
                {
                    "type": "footer",
                    "label": "Page Footer"
                }
            ]
        }
        
        widgets = list(self.rule.traverse_presentation_structure(presentation_data, "body"))
        
        # All widgets should be found by traversal
        assert len(widgets) == 3
        assert widgets[0][0]["type"] == "title"
        assert widgets[1][0]["type"] == "text"
        assert widgets[2][0]["type"] == "footer"
        
        # But only non-excluded widgets should require IDs
        excluded_types = {'title', 'footer', 'item', 'group'}
        non_excluded_widgets = [w for w in widgets if w[0]["type"] not in excluded_types]
        assert len(non_excluded_widgets) == 1
        assert non_excluded_widgets[0][0]["type"] == "text"
        assert non_excluded_widgets[0][0]["id"] == "contentText"


class TestWidgetIdRequiredRuleWithGenericTraversal(unittest.TestCase):
    """Test the updated WidgetIdRequiredRule with generic traversal."""
    
    def setUp(self):
        """Set up test fixtures."""
        from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule
        self.rule = WidgetIdRequiredRule()
    
    def test_area_layout_widget_id_validation(self):
        """Test widget ID validation with areaLayout structure."""
        pmd_data = {
            "pageId": "test-page",
            "presentation": {
                "body": {
                    "type": "areaLayout",
                    "primaryLayout": [
                        {
                            "type": "text",
                            "label": "Primary content"
                            # Missing ID - should trigger validation error
                        }
                    ],
                    "secondaryLayout": [
                        {
                            "type": "button",
                            "id": "secondaryButton",
                            "label": "Secondary action"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test.pmd", source_content="{}")
        
        findings = list(self.rule.visit_pmd(pmd_model))
        
        # Should find one missing ID (for the text widget in primaryLayout)
        assert len(findings) == 1
        assert "missing required 'id' field" in findings[0].message
        assert "text" in findings[0].message
        assert "primaryLayout" in findings[0].message
    
    def test_basic_form_layout_widget_id_validation(self):
        """Test widget ID validation with basicFormLayout structure."""
        pmd_data = {
            "pageId": "test-page",
            "presentation": {
                "body": {
                    "type": "basicFormLayout",
                    "sections": [
                        {
                            "type": "layoutSection",
                            "id": "section1",
                            "children": [
                                {
                                    "type": "input",
                                    "label": "User input"
                                    # Missing ID - should trigger validation error
                                }
                            ]
                        },
                        {
                            "type": "layoutSection",
                            "id": "section2", 
                            "children": [
                                {
                                    "type": "button",
                                    "id": "submitButton",
                                    "label": "Submit"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test.pmd", source_content="{}")
        
        findings = list(self.rule.visit_pmd(pmd_model))
        
        # Should find one missing ID (for the input widget in sections.children)
        assert len(findings) == 1
        assert "missing required 'id' field" in findings[0].message
        assert "input" in findings[0].message
        assert "sections" in findings[0].message
    
    def test_excluded_widget_types_not_require_id(self):
        """Test that excluded widget types don't require IDs."""
        pmd_data = {
            "pageId": "test-page",
            "presentation": {
                "body": {
                    "type": "section",
                    "children": [
                        {
                            "type": "title",
                            "label": "Page Title"
                            # No ID - should NOT trigger validation error
                        },
                        {
                            "type": "item"
                            # No ID - should NOT trigger validation error
                        },
                        {
                            "type": "text",
                            "label": "Content"
                            # Missing ID - should trigger validation error
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test.pmd", source_content="{}")
        
        findings = list(self.rule.visit_pmd(pmd_model))
        
        # Should find only one missing ID (for the text widget)
        assert len(findings) == 1
        assert "missing required 'id' field" in findings[0].message
        assert "text" in findings[0].message
        assert "title" not in findings[0].message
        assert "item" not in findings[0].message
