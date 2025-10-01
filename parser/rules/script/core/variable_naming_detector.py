"""Variable naming detection logic for ScriptVariableNamingRule."""

from typing import Generator, Dict, Any
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation
from ...common_validations import validate_script_variable_camel_case


class VariableNamingDetector(ScriptDetector):
    """Detects variables that don't follow lowerCamelCase naming convention."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect variables that don't follow naming conventions in the AST."""
        # Find all variable declarations
        declared_vars = self._find_declared_variables(ast)
        
        for var_name, var_info in declared_vars.items():
            is_valid, suggestion = self._validate_camel_case(var_name)
            if not is_valid:
                # Use line_offset as base, add relative line if available
                relative_line = var_info.get('line', 1) or 1
                line_number = self.line_offset + relative_line - 1
                
                yield Violation(
                    message=f"File section '{field_name}' declares variable '{var_name}' that doesn't follow lowerCamelCase convention. Consider renaming to '{suggestion}'.",
                    line=line_number
                )
    
    def _find_declared_variables(self, node) -> Dict[str, Dict[str, Any]]:
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
    
    def _validate_camel_case(self, var_name: str) -> tuple[bool, str]:
        """Validate variable name using common camel case validation."""
        return validate_script_variable_camel_case(var_name)
