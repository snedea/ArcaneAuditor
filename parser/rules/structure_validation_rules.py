"""
Structure validation rules - catches structure and naming violations that code reviewers should catch.

These are issues that compilers can't detect but violate structure guidelines and naming conventions.
Examples: naming conventions, data structure compliance, required field validation.

Note: Basic structural validation (missing required fields, etc.) is handled by the compiler.
This tool focuses on structure and naming compliance for code reviewers.
"""
from .base import Rule, Finding
from .base_validation import ValidationRule
from .common_validations import validate_lower_camel_case
from ..models import PMDModel
from typing import Dict, Any, List


class WidgetIdRequiredRule(Rule):
    """Ensures all widgets have an 'id' field - important for code reviewers to catch."""
    
    ID = "STRUCT001"
    DESCRIPTION = "Ensures all widgets have an 'id' field set (structure validation)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes the presentation structure within a PMD model."""
        if not pmd_model.presentation:
            return

        # Check body widgets
        if pmd_model.presentation.body and isinstance(pmd_model.presentation.body, dict):
            children = pmd_model.presentation.body.get("children", [])
            if isinstance(children, list):
                for i, widget in enumerate(children):
                    yield from self._check_widget_id(widget, pmd_model.file_path, pmd_model, 'body', i)

        # Check title widgets
        if pmd_model.presentation.title and isinstance(pmd_model.presentation.title, dict):
            yield from self._check_widget_id(pmd_model.presentation.title, pmd_model.file_path, pmd_model, 'title', 0)

        # Check footer widgets
        if pmd_model.presentation.footer and isinstance(pmd_model.presentation.footer, dict):
            children = pmd_model.presentation.footer.get("children", [])
            if isinstance(children, list):
                for i, widget in enumerate(children):
                    yield from self._check_widget_id(widget, pmd_model.file_path, pmd_model, 'footer', i)

    def _check_widget_id(self, widget, file_path, pmd_model=None, section='body', widget_index=0):
        """Check if a widget has an 'id' field."""
        if not isinstance(widget, dict):
            return

        widget_type = widget.get('type', 'unknown')

        # Skip title and footer widget types from requiring ID
        if widget_type in ['title', 'footer']:
            return

        if 'id' not in widget:
            # Get line number from the PMD model if available
            line_number = 1
            if pmd_model:
                line_number = self._get_widget_line_number(pmd_model, widget_type, section, widget_index)
            
            yield Finding(
                rule=self,
                message=f"Widget of type '{widget_type}' is missing required 'id' field.",
                line=line_number,
                column=1,
                file_path=file_path
            )

    def _get_widget_line_number(self, pmd_model: PMDModel, widget_type: str, section: str, widget_index: int = 0) -> int:
        """Get approximate line number for a widget based on its location."""
        try:
            with open(pmd_model.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Look for the presentation section
            presentation_start = -1
            for i, line in enumerate(lines):
                if '"presentation"' in line:
                    presentation_start = i + 1
                    break
            
            if presentation_start > 0:
                # Look for the specific section within presentation
                section_start = -1
                for i in range(presentation_start, len(lines)):
                    if f'"{section}"' in lines[i]:
                        section_start = i + 1
                        break
                
                if section_start > 0:
                    # Look for the children array
                    children_start = -1
                    for i in range(section_start, len(lines)):
                        if '"children"' in lines[i]:
                            children_start = i + 1
                            break
                    
                    if children_start > 0:
                        # Count widgets until we reach the target index
                        widget_count = 0
                        brace_count = 0
                        in_widget = False
                        
                        for i in range(children_start, len(lines)):
                            line = lines[i]
                            
                            if '{' in line and not in_widget:
                                in_widget = True
                                brace_count = line.count('{')
                            elif in_widget:
                                brace_count += line.count('{') - line.count('}')
                                
                                if brace_count <= 0:
                                    # End of widget
                                    if widget_count == widget_index:
                                        return i + 1  # Return the line number (1-based)
                                    widget_count += 1
                                    in_widget = False
                                    brace_count = 0
                        
                        # If we didn't find the exact widget, return an estimate
                        return children_start + widget_index * 3
                    
                    return section_start + widget_index * 2
                
                return presentation_start + widget_index * 2
            
        except (FileNotFoundError, IOError):
            pass
        
        # Fallback: estimate based on section and widget index
        section_base_lines = {
            'title': 1,
            'body': 5,
            'footer': 10
        }
        base_line = section_base_lines.get(section, 5)
        return base_line + widget_index * 2


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
        
        # Check body widgets
        if pmd_model.presentation.body and isinstance(pmd_model.presentation.body, dict):
            children = pmd_model.presentation.body.get("children", [])
            if isinstance(children, list):
                for i, widget in enumerate(children):
                    if isinstance(widget, dict) and 'id' in widget:
                        entities.append({
                            'entity': widget,
                            'entity_type': 'widget',
                            'entity_name': widget.get('id', 'unknown'),
                            'entity_context': 'body',
                            'entity_index': i
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


class EndpointNameLowerCamelCaseRule(ValidationRule):
    """Validates that endpoint names follow lowerCamelCase convention (style guide)."""
    
    ID = "STYLE002"
    DESCRIPTION = "Ensures endpoint names follow lowerCamelCase naming convention (style guide)"
    SEVERITY = "WARNING"
    
    def __init__(self):
        super().__init__(
            self.ID,
            self.DESCRIPTION,
            self.SEVERITY
        )
    
    def get_entities_to_validate(self, pmd_model: PMDModel):
        """Get all endpoints to validate."""
        entities = []
        
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict) and 'name' in endpoint:
                    entities.append({
                        'entity': endpoint,
                        'entity_type': 'inbound endpoint',
                        'entity_name': endpoint.get('name', 'unknown'),
                        'entity_context': 'inbound',
                        'entity_index': i
                    })
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict) and 'name' in endpoint:
                        entities.append({
                            'entity': endpoint,
                            'entity_type': 'outbound endpoint',
                            'entity_name': endpoint.get('name', 'unknown'),
                            'entity_context': 'outbound',
                            'entity_index': i
                        })
        return entities
    
    def get_field_to_validate(self, entity_info):
        """Validate the 'name' field."""
        return 'name'
    
    def validate_field(self, field_value: str, entity_info: Dict[str, Any]) -> List[str]:
        """Validate that the field value follows lowerCamelCase convention."""
        entity_type = entity_info['entity_type']
        entity_name = entity_info['entity_name']
        field_name = self.get_field_to_validate(entity_info)
        
        return validate_lower_camel_case(field_value, field_name, entity_type, entity_name)
