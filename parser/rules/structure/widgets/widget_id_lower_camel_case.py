from ...base import Rule, Finding
from ...base_validation import ValidationRule
from ...common_validations import validate_lower_camel_case
from ...line_number_utils import LineNumberUtils
from ....models import PMDModel
from typing import Dict, Any, List


class WidgetIdLowerCamelCaseRule(ValidationRule):
    """Validates that widget IDs follow lowerCamelCase convention (style guide)."""
    
    ID = "STYLE001"
    DESCRIPTION = "Ensures widget IDs follow lowerCamelCase naming convention (style guide)"
    SEVERITY = "WARNING"
    
    def __init__(self):
        super().__init__(
            self.ID,
            self.DESCRIPTION,
            self.SEVERITY
        )
    
    def get_entities_to_validate(self, pmd_model: PMDModel):
        """Get all widgets to validate."""
        entities = []
        
        if not pmd_model.presentation:
            return entities
        
        # Check body widgets recursively
        if pmd_model.presentation.body and isinstance(pmd_model.presentation.body, dict):
            children = pmd_model.presentation.body.get("children", [])
            if isinstance(children, list):
                for widget, path, index in self.traverse_widgets_recursively(children, "body.children"):
                    if isinstance(widget, dict) and 'id' in widget:
                        entities.append({
                            'entity': widget,
                            'entity_type': 'widget',
                            'entity_name': widget.get('id', 'unknown'),
                            'entity_context': 'body',
                            'entity_path': path,
                            'entity_index': index
                        })
        
        
        return entities
    
    def get_field_to_validate(self, entity_info):
        """Validate the 'id' field."""
        return 'id'
    
    def validate_field(self, field_value: str, entity_info: Dict[str, Any]) -> List[str]:
        """Validate that the field value follows lowerCamelCase convention."""
        entity_type = entity_info['entity_type']
        entity_name = entity_info['entity_name']
        field_name = self.get_field_to_validate(entity_info)
        
        return validate_lower_camel_case(field_value, field_name, entity_type, entity_name)
    
    def get_line_number(self, pmd_model: PMDModel, entity_info: Dict[str, Any]) -> int:
        """Get line number for the widget ID field."""
        entity = entity_info['entity']
        widget_id = entity.get('id', '')
        
        if widget_id:
            return LineNumberUtils.find_field_line_number(pmd_model, 'id', widget_id)
        
        return 1  # Default fallback
