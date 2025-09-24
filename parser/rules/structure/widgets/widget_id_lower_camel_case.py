from ...base_validation import ValidationRule
from ...common_validations import validate_lower_camel_case
from ...line_number_utils import LineNumberUtils
from ....models import PMDModel, PodModel
from typing import Dict, Any, List


class WidgetIdLowerCamelCaseRule(ValidationRule):
    """Validates that widget IDs follow lowerCamelCase convention (style guide)."""
    
    DESCRIPTION = "Ensures widget IDs follow lowerCamelCase naming convention (style guide for PMD and POD files)"
    SEVERITY = "WARNING"
    
    # Widget types that do not require or support ID values
    WIDGET_TYPES_WITHOUT_ID_REQUIREMENT = {
        'footer', 'item', 'group', 'title'
    }
    
    def __init__(self):
        super().__init__(
            self.__class__.__name__,
            self.DESCRIPTION,
            self.SEVERITY
        )
    
    def get_entities_to_validate(self, pmd_model: PMDModel):
        """Get all widgets to validate."""
        entities = []
        
        if not pmd_model.presentation:
            return entities
        
        # Use generic traversal to handle different layout types
        presentation_dict = pmd_model.presentation.__dict__
        
        # Traverse all presentation sections (body, title, footer, etc.)
        for section_name, section_data in presentation_dict.items():
            if isinstance(section_data, dict):
                # Use generic traversal for each section
                for widget, path, index in self.traverse_presentation_structure(section_data, section_name):
                    if isinstance(widget, dict) and 'id' in widget:
                        # Skip widget types that are excluded from ID requirements
                        widget_type = widget.get('type', 'unknown')
                        if widget_type not in self.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT:
                            entities.append({
                                'entity': widget,
                                'entity_type': 'widget',
                                'entity_name': widget.get('id', 'unknown'),
                                'entity_context': section_name,
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
    
    def get_entities_to_validate_pod(self, pod_model: PodModel) -> List[Dict[str, Any]]:
        """Get all widgets with IDs from POD template to validate."""
        entities = []
        
        # Use the base rule utility to find all widgets in the POD template
        widgets = self.find_pod_widgets(pod_model)
        
        for widget_path, widget_data in widgets:
            if isinstance(widget_data, dict) and 'id' in widget_data:
                entities.append({
                    'entity': widget_data,
                    'entity_type': 'widget',
                    'entity_name': widget_data.get('id', 'unknown'),
                    'entity_context': 'template',
                    'entity_path': widget_path,
                    'entity_index': 0
                })
        
        return entities
