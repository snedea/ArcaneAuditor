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
                # Get line number using the proper method
                line_number = var_info.get('line_number', self.line_offset)
                self._debug_line_calc(var_info.get('ast_line', 1), self.line_offset, line_number, "variable_naming")
                
                # Check if this variable is inside a function
                variable_node = var_info.get('node')
                function_name = None
                if variable_node:
                    function_name = self.get_function_context_for_node(variable_node, ast)
                
                if function_name:
                    message = f"File section '{field_name}' declares variable '{var_name}' in function '{function_name}' that doesn't follow lowerCamelCase convention. Consider renaming to '{suggestion}'."
                else:
                    message = f"File section '{field_name}' declares variable '{var_name}' that doesn't follow lowerCamelCase convention. Consider renaming to '{suggestion}'."
                
                yield Violation(
                    message=message,
                    line=line_number
                )
    
    def _find_declared_variables(self, node) -> Dict[str, Dict[str, Any]]:
        """Find all variable declarations in the AST."""
        declared_vars = {}
        
        if hasattr(node, 'data'):
            # Handle variable_declaration nodes (direct declarations)
            if node.data == 'variable_declaration':
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    var_name = node.children[0].value
                    # Get AST line and calculate file line using standard formula
                    ast_line = node.children[0].line if hasattr(node.children[0], 'line') else 1
                    line_number = self.line_offset + ast_line - 1
                    
                    declared_vars[var_name] = {
                        'line_number': line_number,
                        'ast_line': ast_line,
                        'type': 'declaration',
                        'node': node
                    }
            
            # Handle variable_statement nodes (var/let/const declarations)
            elif node.data == 'variable_statement':
                # Get the variable declaration list (second child)
                if len(node.children) > 1:
                    var_declaration_list = node.children[1]
                    if hasattr(var_declaration_list, 'data') and var_declaration_list.data == 'variable_declaration_list':
                        # Process each variable declaration in the list
                        for var_declaration in var_declaration_list.children:
                            if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                                if len(var_declaration.children) > 0 and hasattr(var_declaration.children[0], 'value'):
                                    var_name = var_declaration.children[0].value
                                    # Get AST line and calculate file line using standard formula
                                    ast_line = var_declaration.children[0].line if hasattr(var_declaration.children[0], 'line') else 1
                                    line_number = self.line_offset + ast_line - 1
                                    
                                    declared_vars[var_name] = {
                                        'line_number': line_number,
                                        'ast_line': ast_line,
                                        'type': 'declaration',
                                        'node': var_declaration
                                    }
            
            # Handle for loop variable declarations
            elif node.data in ['for_var_statement', 'for_let_statement', 'for_const_statement']:
                # Get the variable declaration list (second child)
                if len(node.children) > 1:
                    var_declaration_list = node.children[1]
                    if hasattr(var_declaration_list, 'data') and var_declaration_list.data == 'variable_declaration_list':
                        # Process each variable declaration in the list
                        for var_declaration in var_declaration_list.children:
                            if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                                if len(var_declaration.children) > 0 and hasattr(var_declaration.children[0], 'value'):
                                    var_name = var_declaration.children[0].value
                                    # Get AST line and calculate file line using standard formula
                                    ast_line = var_declaration.children[0].line if hasattr(var_declaration.children[0], 'line') else 1
                                    line_number = self.line_offset + ast_line - 1
                                    
                                    declared_vars[var_name] = {
                                        'line_number': line_number,
                                        'ast_line': ast_line,
                                        'type': 'declaration',
                                        'node': var_declaration
                                    }
            
            # Handle for-in loop variable declarations
            elif node.data in ['for_var_in_statement', 'for_let_in_statement', 'for_const_in_statement']:
                # Get the variable name (second child)
                if len(node.children) > 1 and hasattr(node.children[1], 'value'):
                    var_name = node.children[1].value
                    # Get AST line and calculate file line using standard formula
                    ast_line = node.children[1].line if hasattr(node.children[1], 'line') else 1
                    line_number = self.line_offset + ast_line - 1
                    
                    declared_vars[var_name] = {
                        'line_number': line_number,
                        'ast_line': ast_line,
                        'type': 'declaration',
                        'node': node.children[1]
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
