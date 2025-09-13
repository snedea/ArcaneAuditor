from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel
from ...common_validations import validate_script_variable_camel_case


class ScriptVariableNamingRule(Rule):
    """Validates that variables follow naming conventions."""
    
    ID = "SCRIPT008"
    DESCRIPTION = "Ensures variables follow lowerCamelCase naming convention"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_variable_naming(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_variable_naming(self, script_content, field_name, file_path, line_offset=1):
        """Check variable naming conventions in script content."""
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all variable declarations
        declared_vars = self._find_declared_variables(ast)
        
        for var_name, var_info in declared_vars.items():
            is_valid, suggestion = self._validate_camel_case(var_name)
            if not is_valid:
                # Use line_offset as base, add relative line if available
                relative_line = var_info.get('line', 1) or 1
                line_number = line_offset + relative_line - 1
                
                yield Finding(
                    rule=self,
                    message=f"File section '{field_name}' declares variable '{var_name}' that doesn't follow lowerCamelCase convention. Consider renaming to '{suggestion}'.",
                    line=line_number,
                    column=1,
                    file_path=file_path
                )
    
    def _find_declared_variables(self, node):
        """Find all variable declarations in the AST."""
        declared_vars = {}
        
        if hasattr(node, 'data'):
            if node.data == 'variable_declaration':
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    var_name = node.children[0].value
                    # Get line number from the first token in the node
                    line_number = None
                    if hasattr(node, 'children') and len(node.children) > 0:
                        for child in node.children:
                            if hasattr(child, 'line') and child.line is not None:
                                line_number = child.line
                                break
                    
                    declared_vars[var_name] = {
                        'line': line_number,
                        'type': 'declaration'
                    }
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                child_vars = self._find_declared_variables(child)
                declared_vars.update(child_vars)
        
        return declared_vars
    
    def _validate_camel_case(self, var_name):
        """Validate variable name using common camel case validation."""
        return validate_script_variable_camel_case(var_name)
