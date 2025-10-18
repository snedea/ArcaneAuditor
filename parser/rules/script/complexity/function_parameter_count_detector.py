"""Function parameter count detection logic for ScriptFunctionParameterCountRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class FunctionParameterCountDetector(ScriptDetector):
    """Detects functions with too many parameters."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        self.max_parameters = 4
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect functions with too many parameters in the AST."""
        # Find all function definitions
        function_definitions = self._find_function_definitions(ast)
        
        for func_def in function_definitions:
            param_count = self._count_parameters(func_def)
            if param_count > self.max_parameters:
                # Get line number using standardized method
                line_number = self.get_line_from_tree_node(func_def)
                
                # Get the function name using proper function context mapping
                function_name = self.get_function_context_for_node(func_def, ast)
                
                if function_name:
                    message = f"Function '{function_name}' has {param_count} parameters (max allowed: {self.max_parameters}). Consider refactoring to reduce complexity."
                else:
                    message = f"Function has {param_count} parameters (max allowed: {self.max_parameters}). Consider refactoring to reduce complexity."
                
                yield Violation(
                    message=message,
                    line=line_number or self.line_offset
                )
    
    def _find_function_definitions(self, ast: Tree) -> List[Tree]:
        """Find all function definition nodes in the AST."""
        function_definitions = []
        
        def traverse(node):
            if isinstance(node, Tree):
                # Check if this is a function expression (top-level or nested)
                if node.data == 'function_expression':
                    function_definitions.append(node)
                # Check if this is an arrow function
                elif node.data == 'arrow_function_expression':
                    function_definitions.append(node)
                
                # Recursively traverse children
                for child in node.children:
                    traverse(child)
        
        traverse(ast)
        return function_definitions
    
    def _count_parameters(self, function_node: Tree) -> int:
        """Count the number of parameters in a function definition."""
        if not isinstance(function_node, Tree):
            return 0
        
        if function_node.data == 'function_expression':
            # For function expressions, look for formal_parameter_list
            for child in function_node.children:
                if isinstance(child, Tree) and child.data == 'formal_parameter_list':
                    # Count the parameters in the parameter list
                    return self._count_parameter_list(child)
        elif function_node.data == 'arrow_function_expression':
            # For arrow functions, count identifier tokens directly
            return self._count_arrow_function_parameters(function_node)
        
        return 0
    
    def _count_parameter_list(self, parameter_list_node: Tree) -> int:
        """Count parameters in a formal parameter list."""
        if not isinstance(parameter_list_node, Tree):
            return 0
        
        count = 0
        for child in parameter_list_node.children:
            # In formal_parameter_list, each child is an IDENTIFIER token
            if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                count += 1
        
        return count
    
    def _count_arrow_function_parameters(self, arrow_function_node: Tree) -> int:
        """Count parameters in an arrow function."""
        if not isinstance(arrow_function_node, Tree):
            return 0
        
        count = 0
        for child in arrow_function_node.children:
            # In arrow functions, parameters are IDENTIFIER tokens
            if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                # Skip the arrow token and expression parts
                if hasattr(child, 'value') and child.value == '=>':
                    break
                count += 1
        
        return count
    
    def _get_line_number(self, node: Tree) -> int:
        """Get the line number for a tree node."""
        if hasattr(node, 'meta') and hasattr(node.meta, 'line'):
            return node.meta.line
        return 1  # Default to line 1 if no line info available
