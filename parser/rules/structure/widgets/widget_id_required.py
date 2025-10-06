"""
Structure validation rules - catches structure and naming violations that code reviewers should catch.

These are issues that compilers can't detect but violate structure guidelines and naming conventions.
Examples: naming conventions, data structure compliance, required field validation.

Note: Basic structural validation (missing required fields, etc.) is handled by the compiler.
This tool focuses on structure and naming compliance for code reviewers.
"""
from typing import Generator
from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ...common import PMDLineUtils
from ..shared import StructureRuleBase


class WidgetIdRequiredRule(StructureRuleBase):
    """Ensures all widgets have an 'id' field - important for code reviewers to catch."""
    
    DESCRIPTION = "Ensures all widgets have an 'id' field set (structure validation for PMD and POD files)"
    SEVERITY = "ACTION"
    
    # Widget types that do not require or support ID values
    WIDGET_TYPES_WITHOUT_ID_REQUIREMENT = {
        'footer', 'item', 'group', 'title', 'pod', 'cardContainer', 'card'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes the presentation structure within a PMD model."""
        if not pmd_model.presentation:
            return

        # Use generic traversal to handle different layout types
        presentation_dict = pmd_model.presentation.__dict__
        
        # Traverse all presentation sections (body, title, footer, etc.)
        for section_name, section_data in presentation_dict.items():
            if isinstance(section_data, dict):
                # Use generic traversal for each section
                for widget, path, index in self.traverse_presentation_structure(section_data, section_name):
                    yield from self._check_widget_id(widget, pmd_model.file_path, pmd_model, section_name, path, index)

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes the template widgets within a POD model."""
        if not pod_model.seed.template:
            return
        
        # Use the base rule utility to find all widgets in the POD template
        widgets = self.find_pod_widgets(pod_model)
        
        for widget_path, widget_data in widgets:
            # Convert the path to a more readable format
            path_parts = widget_path.split('.')
            section = 'template'
            index = 0
            
            # Extract index if present in path (e.g., "children[0]" -> 0)
            if '[' in widget_path and ']' in widget_path:
                import re
                match = re.search(r'\[(\d+)\]', widget_path)
                if match:
                    index = int(match.group(1))
            
            yield from self._check_widget_id(widget_data, pod_model.file_path, None, section, widget_path, index, pod_model)

    def _check_widget_id(self, widget, file_path, pmd_model=None, section='body', widget_path="", widget_index=0, pod_model=None):
        """Check if a widget has an 'id' field."""
        if not isinstance(widget, dict):
            return

        widget_type = widget.get('type', 'unknown')

        # Skip widget types that are excluded from ID requirements
        if widget_type in self.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT:
            return

        # Skip column objects - they use columnId instead of id (enforced by compiler)
        # Column objects are found in "columns" arrays and have columnId field
        if 'columnId' in widget:
            return

        if 'id' not in widget:
            # Get line number from the PMD or POD model if available
            line_number = 1
            if pmd_model:
                line_number = self._get_widget_line_number(pmd_model, widget_type, section, widget_path, widget_index)
            elif pod_model:
                line_number = self._get_pod_widget_line_number(pod_model, widget_type, widget_path, widget_index)
            
            # Create a full readable path description
            readable_path = self._build_readable_widget_path(widget, widget_path, section, pmd_model, pod_model)
            path_description = f" at {readable_path}" if readable_path else ""
            
            yield self._create_finding(
                message=f"Widget of type '{widget_type}'{path_description} is missing required 'id' field.",
                file_path=file_path,
                line=line_number
            )

    def _get_widget_line_number(self, pmd_model: PMDModel, widget_type: str, section: str, widget_path: str = "", widget_index: int = 0) -> int:
        """Get approximate line number for a widget based on its location."""
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Look for the section first
            section_line = PMDLineUtils.find_section_line_number(pmd_model, section)
            if section_line > 1:
                # Look for the widget type in the section area
                search_start = max(0, section_line - 1)
                search_end = min(len(lines), section_line + 50)  # Search 50 lines after section
                
                widget_count = 0
                for i in range(search_start, search_end):
                    line = lines[i]
                    # Look for the widget type
                    if f'"type": "{widget_type}"' in line or f'"type":"{widget_type}"' in line:
                        if widget_count == widget_index:
                            # Find the opening brace of this widget block by looking backwards
                            widget_start_line = self._find_widget_opening_brace(lines, i)
                            return widget_start_line + 1  # Return the line number (1-based)
                        widget_count += 1
                
                # If we found the section but not the specific widget, estimate
                return section_line + widget_index * 3
            
            # Fallback: estimate based on section and widget index
            section_base_lines = {
                'title': 1,
                'body': 5,
                'footer': 10
            }
            base_line = section_base_lines.get(section, 5)
            return base_line + widget_index * 2
            
        except Exception:
            # Fallback: estimate based on section and widget index
            section_base_lines = {
                'title': 1,
                'body': 5,
                'footer': 10
            }
            base_line = section_base_lines.get(section, 5)
            return base_line + widget_index * 2

    def _get_pod_widget_line_number(self, pod_model: PodModel, widget_type: str, widget_path: str = "", widget_index: int = 0) -> int:
        """Get approximate line number for a widget in a POD file based on its location."""
        try:
            if not pod_model.source_content:
                return 1
            
            lines = pod_model.source_content.split('\n')
            
            # Look for the template section first
            template_line = PMDLineUtils.find_section_line_number(pod_model, 'template')
            if template_line > 1:
                # Look for the widget type in the template area
                search_start = max(0, template_line - 1)
                search_end = min(len(lines), template_line + 50)  # Search 50 lines after template
                
                widget_count = 0
                for i in range(search_start, search_end):
                    line = lines[i]
                    # Look for the widget type
                    if f'"type": "{widget_type}"' in line or f'"type":"{widget_type}"' in line:
                        if widget_count == widget_index:
                            # Find the opening brace of this widget block by looking backwards
                            widget_start_line = self._find_widget_opening_brace(lines, i)
                            return widget_start_line + 1  # Return the line number (1-based)
                        widget_count += 1
                
                # If we found the template but not the specific widget, estimate
                return template_line + widget_index * 3
            
            # Fallback: estimate based on widget index
            return 5 + widget_index * 2
            
        except Exception:
            # Fallback: estimate based on widget index
            return 5 + widget_index * 2
    
    def _find_widget_opening_brace(self, lines: list, type_line_index: int) -> int:
        """Find the opening brace of a widget block by looking backwards from the type line."""
        try:
            # Look backwards from the type line to find the opening brace
            for i in range(type_line_index - 1, max(0, type_line_index - 10), -1):
                line = lines[i].strip()
                # Look for an opening brace at the start of a line (indicating widget start)
                if line == '{':
                    return i
                # Also check for opening brace with content on the same line
                elif line.startswith('{'):
                    return i
            
            # If we can't find the opening brace, return the type line itself
            return type_line_index
        except Exception:
            return type_line_index
    
    def _build_readable_widget_path(self, widget, widget_path, section, pmd_model=None, pod_model=None):
        """
        Build a readable path to a widget using the same logic as script rules.
        
        Args:
            widget: The widget dictionary
            widget_path: Technical path like "body.children.0"
            section: Section name (body, title, footer, etc.)
            pmd_model: PMD model for context
            pod_model: POD model for context
            
        Returns:
            Readable path string like "body->primaryLayout->label: Primary content"
        """
        try:
            if not widget_path:
                # Fallback to just the widget identifier
                return self._get_readable_identifier(widget, 0)
            
            # Split the technical path into components
            path_parts = widget_path.split('.')
            
            # Start with the section name
            display_prefix = section
            
            # Build readable path by following the technical path and using readable identifiers
            if pmd_model and pmd_model.presentation:
                current_data = pmd_model.presentation.__dict__.get(section, {})
                display_prefix = self._build_path_from_data(current_data, path_parts[1:], display_prefix)
            elif pod_model and pod_model.seed and pod_model.seed.template:
                current_data = pod_model.seed.template
                display_prefix = self._build_path_from_data(current_data, path_parts, display_prefix)
            
            # The display_prefix already includes the widget identifier from the traversal
            return display_prefix
            
        except Exception:
            # Fallback to just the widget identifier
            return self._get_readable_identifier(widget, 0)
    
    def _build_path_from_data(self, data, path_parts, current_prefix):
        """
        Build readable path by traversing data structure following path_parts.
        Uses the same logic as script rules for consistency.
        """
        if not path_parts or not isinstance(data, dict):
            return current_prefix
        
        current_key = path_parts[0]
        
        if current_key in data:
            current_value = data[current_key]
            
            if isinstance(current_value, list) and len(path_parts) > 1:
                # This is an array, get the index from next path part
                try:
                    index = int(path_parts[1])
                    if 0 <= index < len(current_value):
                        item = current_value[index]
                        if isinstance(item, dict):
                            # Include array index in the path: key[index]->readable_id
                            readable_id = self._get_readable_identifier(item, index)
                            new_prefix = f"{current_prefix}->{current_key}[{index}]->{readable_id}"
                            
                            # Continue with remaining path parts
                            remaining_parts = path_parts[2:] if len(path_parts) > 2 else []
                            return self._build_path_from_data(item, remaining_parts, new_prefix)
                        else:
                            return f"{current_prefix}->{current_key}[{index}]"
                except (ValueError, IndexError):
                    return f"{current_prefix}->{current_key}"
            else:
                # This is a direct field
                new_prefix = f"{current_prefix}->{current_key}"
                remaining_parts = path_parts[1:] if len(path_parts) > 1 else []
                return self._build_path_from_data(current_value, remaining_parts, new_prefix)
        
        return current_prefix
