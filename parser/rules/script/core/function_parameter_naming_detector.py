"""Function parameter naming detection logic for ScriptFunctionParameterNamingRule."""

from typing import Generator, Dict, Any
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation
from ...common_validations import validate_script_variable_camel_case


class FunctionParameterNamingDetector(ScriptDetector):
    """Detects function parameters that don't follow lowerCamelCase naming convention."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect function parameters that don't follow naming conventions in the AST."""
        # Find all function expressions
        function_expressions = ast.find_data('function_expression')
        
        for func_expr in function_expressions:
            # Look for formal_parameter_list first
            for child in func_expr.children:
                if hasattr(child, 'data') and child.data == 'formal_parameter_list':
                    # Check each parameter in the formal parameter list
                    for param in child.children:
                        if hasattr(param, 'value'):
                            param_name = param.value
                            is_valid, suggestion = validate_script_variable_camel_case(param_name)
                            if not is_valid:
                                # Get line number from the parameter token
                                line_number = self.get_line_number(param)
                                
                                yield Violation(
                                    message=f"File section '{field_name}' has function parameter '{param_name}' that doesn't follow lowerCamelCase convention. Consider renaming to '{suggestion}'.",
                                    line=line_number
                                )
                elif hasattr(child, 'value') and not hasattr(child, 'data'):
                    # This is a direct parameter token (not in formal_parameter_list)
                    # Check if it's a parameter by looking at the context
                    param_name = child.value
                    if self._is_parameter_token(func_expr, child):
                        is_valid, suggestion = validate_script_variable_camel_case(param_name)
                        if not is_valid:
                            # Get line number from the parameter token
                            line_number = self.get_line_number(child)
                            
                            yield Violation(
                                message=f"File section '{field_name}' has function parameter '{param_name}' that doesn't follow lowerCamelCase convention. Consider renaming to '{suggestion}'.",
                                line=line_number
                            )
    
    def _is_parameter_token(self, func_expr, token) -> bool:
        """Check if a token is a function parameter by examining its position in the function expression."""
        # Parameters typically come after the 'function' keyword and before the function body
        # Look for tokens that are not 'function' and come before source_elements
        if not hasattr(token, 'value'):
            return False
        
        # Find the position of this token in the function expression
        for i, child in enumerate(func_expr.children):
            if child == token:
                # Check if this token comes after 'function' and before source_elements
                # Parameters are typically at index 1 (after 'function' token)
                if i == 1 and hasattr(token, 'value'):
                    # Additional check: make sure it's not a source_elements node
                    if not (hasattr(token, 'data') and token.data == 'source_elements'):
                        return True
                break
        
        return False
