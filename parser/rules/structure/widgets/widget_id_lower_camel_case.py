from typing import Generator
from ...base import Finding
from ...common_validations import validate_lower_camel_case
from ...line_number_utils import LineNumberUtils
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class WidgetIdLowerCamelCaseRule(StructureRuleBase):
    """Validates that widget IDs follow lowerCamelCase convention (style guide)."""
    
    ID = "WidgetIdLowerCamelCaseRule"
    DESCRIPTION = "Ensures widget IDs follow lowerCamelCase naming convention (style guide for PMD and POD files)"
    SEVERITY = "WARNING"
    
    # Widget types that do not require or support ID values
    WIDGET_TYPES_WITHOUT_ID_REQUIREMENT = {
        'footer', 'item', 'group', 'title'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for widget ID naming conventions."""
        if not pmd_model.presentation:
            return
        
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
                            yield from self._check_widget_id_naming(widget, pmd_model, section_name, path, index)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for widget ID naming conventions."""
        # Use the base rule utility to find all widgets in the POD template
        widgets = self.find_pod_widgets(pod_model)
        
        for widget_path, widget_data in widgets:
            if isinstance(widget_data, dict) and 'id' in widget_data:
                yield from self._check_widget_id_naming(widget_data, None, 'template', widget_path, 0, pod_model)
    
    def _check_widget_id_naming(self, widget, pmd_model=None, section='body', widget_path="", widget_index=0, pod_model=None):
        """Check if a widget ID follows lowerCamelCase convention."""
        if not isinstance(widget, dict) or 'id' not in widget:
            return
        
        widget_id = widget.get('id', '')
        widget_type = widget.get('type', 'unknown')
        
        # Skip widget types that are excluded from ID requirements
        if widget_type in self.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT:
            return
        
        # Validate the ID follows lowerCamelCase convention
        validation_errors = validate_lower_camel_case(widget_id, 'id', 'widget', widget_id)
        
        if validation_errors:
            # Get line number
            line_number = 1
            if pmd_model:
                line_number = self._get_widget_line_number(pmd_model, widget_id)
            elif pod_model:
                line_number = self._get_pod_widget_line_number(pod_model, widget_id)
            
            # Create descriptive message
            path_description = f" at path '{widget_path}'" if widget_path else ""
            
            yield self._create_finding(
                message=f"Widget ID '{widget_id}'{path_description} has invalid name '{widget_id}'. Must follow lowerCamelCase convention (e.g., 'myField', 'userName').",
                file_path=pmd_model.file_path if pmd_model else pod_model.file_path,
                line=line_number
            )
    
    def _get_widget_line_number(self, pmd_model: PMDModel, widget_id: str) -> int:
        """Get line number for widget ID field."""
        if widget_id:
            return LineNumberUtils.find_field_line_number(pmd_model, 'id', widget_id)
        return 1
    
    def _get_pod_widget_line_number(self, pod_model: PodModel, widget_id: str) -> int:
        """Get line number for widget ID field in POD."""
        if widget_id:
            return LineNumberUtils.find_field_line_number(pod_model, 'id', widget_id)
        return 1
