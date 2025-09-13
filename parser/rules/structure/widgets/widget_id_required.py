"""
Structure validation rules - catches structure and naming violations that code reviewers should catch.

These are issues that compilers can't detect but violate structure guidelines and naming conventions.
Examples: naming conventions, data structure compliance, required field validation.

Note: Basic structural validation (missing required fields, etc.) is handled by the compiler.
This tool focuses on structure and naming compliance for code reviewers.
"""
from ...base import Rule, Finding
from ....models import PMDModel
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
