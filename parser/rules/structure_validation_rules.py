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
from .line_number_utils import LineNumberUtils
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

        # Check body widgets recursively
        if pmd_model.presentation.body and isinstance(pmd_model.presentation.body, dict):
            children = pmd_model.presentation.body.get("children", [])
            if isinstance(children, list):
                for widget, path, index in self.traverse_widgets_recursively(children, "body.children"):
                    yield from self._check_widget_id(widget, pmd_model.file_path, pmd_model, 'body', path, index)

        # Check title widgets
        if pmd_model.presentation.title and isinstance(pmd_model.presentation.title, dict):
            yield from self._check_widget_id(pmd_model.presentation.title, pmd_model.file_path, pmd_model, 'title', "title", 0)


    def _check_widget_id(self, widget, file_path, pmd_model=None, section='body', widget_path="", widget_index=0):
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
                line_number = self._get_widget_line_number(pmd_model, widget_type, section, widget_path, widget_index)
            
            # Create a more descriptive message with the widget path
            path_description = f" at path '{widget_path}'" if widget_path else ""
            
            yield Finding(
                rule=self,
                message=f"Widget of type '{widget_type}'{path_description} is missing required 'id' field.",
                line=line_number,
                column=1,
                file_path=file_path
            )

    def _get_widget_line_number(self, pmd_model: PMDModel, widget_type: str, section: str, widget_path: str = "", widget_index: int = 0) -> int:
        """Get approximate line number for a widget based on its location."""
        try:
            # Use source_content instead of reading from file_path
            if not pmd_model.source_content:
                return 1
            lines = pmd_model.source_content.split('\n')
            
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
    
    def get_line_number(self, pmd_model: PMDModel, entity_info: Dict[str, Any]) -> int:
        """Get line number for the endpoint name field."""
        entity = entity_info['entity']
        endpoint_name = entity.get('name', '')
        
        if endpoint_name:
            return LineNumberUtils.find_field_line_number(pmd_model, 'name', endpoint_name)
        
        return 1  # Default fallback


class EndpointOnSendSelfDataRule(Rule):
    """Validates that endpoints don't use the anti-pattern 'self.data = {:}' in onSend scripts."""
    
    ID = "SCRIPT009"
    DESCRIPTION = "Ensures endpoints don't use anti-pattern 'self.data = {:}' in onSend scripts"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes endpoints for anti-pattern usage."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_anti_pattern(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_anti_pattern(endpoint, pmd_model, 'outbound', i)

    def _check_endpoint_anti_pattern(self, endpoint, pmd_model, endpoint_type, index):
        """Check if an endpoint uses the anti-pattern in its onSend script."""
        on_send = endpoint.get('onSend', '')
        endpoint_name = endpoint.get('name', f'unnamed_{endpoint_type}_{index}')
        
        if on_send and 'self.data = {:}' in on_send:
            line_number = self._get_on_send_line_number(pmd_model, endpoint_name, endpoint_type)
            
            yield Finding(
                rule=self,
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' uses anti-pattern 'self.data = {{:}}' in onSend script. This pattern should be avoided.",
                line=line_number,
                column=1,
                file_path=pmd_model.file_path
            )

    def _get_on_send_line_number(self, pmd_model: PMDModel, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the onSend script containing the anti-pattern."""
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Look for the endpoint name first
            endpoint_line = -1
            for i, line in enumerate(lines):
                if f'"name": "{endpoint_name}"' in line or f'"name":"{endpoint_name}"' in line:
                    endpoint_line = i
                    break
            
            if endpoint_line >= 0:
                # Look for the onSend field after the endpoint name
                for i in range(endpoint_line, min(endpoint_line + 20, len(lines))):
                    if '"onSend"' in lines[i]:
                        # Look for the anti-pattern in the next few lines
                        for j in range(i, min(i + 10, len(lines))):
                            if 'self.data = {:}' in lines[j]:
                                return j + 1  # Convert to 1-based line numbering
            
            return endpoint_line + 1 if endpoint_line >= 0 else 1
            
        except Exception:
            return 1


class FooterPodRequiredRule(Rule):
    """Ensures footer uses pod structure - either direct pod or footer with pod children."""
    
    ID = "STRUCT003"
    DESCRIPTION = "Ensures footer uses pod structure (direct pod or footer with pod children)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes the footer structure within a PMD model."""
        if not pmd_model.presentation or not pmd_model.presentation.footer:
            return

        footer = pmd_model.presentation.footer
        if not isinstance(footer, dict):
            return

        # Check if footer is missing entirely
        if not footer:
            yield Finding(
                rule=self,
                message="Footer section is missing. Footer should use pod structure.",
                line=1,
                column=1,
                file_path=pmd_model.file_path
            )
            return

        # Check if footer uses direct pod structure
        if footer.get('type') == 'pod':
            return  # Valid pod structure

        # Check if footer uses footer type with pod children
        if footer.get('type') == 'footer':
            children = footer.get('children', [])
            if not isinstance(children, list) or len(children) == 0:
                line_number = self._get_footer_line_number(pmd_model)
                yield Finding(
                    rule=self,
                    message="Footer must utilize a pod.",
                    line=line_number,
                    column=1,
                    file_path=pmd_model.file_path
                )
                return

            # Check if the first (and only expected) child is a pod
            if len(children) > 0:
                child = children[0]
                if isinstance(child, dict) and child.get('type') == 'pod':
                    return  # Valid pod child
                else:
                    line_number = self._get_footer_line_number(pmd_model)
                    yield Finding(
                        rule=self,
                        message="Footer must utilize a pod.",
                        line=line_number,
                        column=1,
                        file_path=pmd_model.file_path
                    )
            else:
                line_number = self._get_footer_line_number(pmd_model)
                yield Finding(
                    rule=self,
                    message="Footer must utilize a pod.",
                    line=line_number,
                    column=1,
                    file_path=pmd_model.file_path
                )
            return

        # If we get here, footer has invalid structure
        line_number = self._get_footer_line_number(pmd_model)
        yield Finding(
            rule=self,
            message="Footer must utilize a pod.",
            line=line_number,
            column=1,
            file_path=pmd_model.file_path
        )

    def _get_footer_line_number(self, pmd_model: PMDModel) -> int:
        """Get approximate line number for the footer section."""
        return LineNumberUtils.find_section_line_number(pmd_model, 'footer')


class EndpointFailOnStatusCodesRule(Rule):
    """Ensures endpoints have proper failOnStatusCodes structure with required codes 400 and 403."""
    
    ID = "STRUCT004"
    DESCRIPTION = "Ensures endpoints have failOnStatusCodes with minimum required codes 400 and 403"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes endpoints for proper failOnStatusCodes structure."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_fail_on_status_codes(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_fail_on_status_codes(endpoint, pmd_model, 'outbound', i)

    def _check_endpoint_fail_on_status_codes(self, endpoint, pmd_model, endpoint_type, index):
        """Check if an endpoint has proper failOnStatusCodes structure."""
        endpoint_name = endpoint.get('name')
        fail_on_status_codes = endpoint.get('failOnStatusCodes', None)
        
        # Check if failOnStatusCodes exists
        if fail_on_status_codes is None:
            line_number = self._get_endpoint_line_number(pmd_model, endpoint_name, endpoint_type)
            yield Finding(
                rule=self,
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' is missing required 'failOnStatusCodes' field.",
                line=line_number,
                column=1,
                file_path=pmd_model.file_path
            )
            return

        codes_found = set()
        for _, status_code_entry in enumerate(fail_on_status_codes):
            code = status_code_entry['code']
            codes_found.add(code)
        
        # Check for required codes 400 and 403
        required_codes = {'400', '403'}
        # Remove codes found from required codes. Empty set if all required codes are found.
        missing_codes = required_codes - codes_found
        
        # If there are missing codes, yield a finding
        if missing_codes:
            line_number = self._get_fail_on_status_codes_line_number(pmd_model, endpoint_name, endpoint_type)
            missing_codes_str = ', '.join(sorted(missing_codes))
            yield Finding(
                rule=self,
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' is missing required status codes: {missing_codes_str}.",
                line=line_number,
                column=1,
                file_path=pmd_model.file_path
            )

    def _get_endpoint_line_number(self, pmd_model: PMDModel, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the endpoint."""
        if endpoint_name:
            return LineNumberUtils.find_field_line_number(pmd_model, 'name', endpoint_name)
        return 1

    def _get_fail_on_status_codes_line_number(self, pmd_model: PMDModel, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the failOnStatusCodes field."""
        if endpoint_name:
            return LineNumberUtils.find_field_after_entity(pmd_model, 'name', endpoint_name, 'failOnStatusCodes')
        return 1


class StringBooleanRule(Rule):
    """Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans."""
    
    ID = "STRUCT005"
    DESCRIPTION = "Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes the PMD model for string boolean values."""
        if not pmd_model.source_content:
            return
        
        # Check the raw source content for string boolean patterns
        yield from self._check_source_content_for_string_booleans(pmd_model)

    def _check_source_content_for_string_booleans(self, pmd_model: PMDModel):
        """Check the source content for string boolean patterns."""
        import re
        
        lines = pmd_model.source_content.split('\n')
        
        # Pattern to match field: "true" or field: "false" or field:"true" or field:"false"
        pattern = r'"([^"]+)"\s*:\s*"(true|false)"'
        
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                field_name = match.group(1)
                string_value = match.group(2)
                
                yield Finding(
                    rule=self,
                    message=f"Field '{field_name}' has string value '{string_value}' instead of boolean {string_value}. Use boolean {string_value} instead of string '{string_value}'.",
                    line=line_num,
                    column=match.start() + 1,
                    file_path=pmd_model.file_path
                )
