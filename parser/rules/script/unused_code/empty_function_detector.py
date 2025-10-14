"""Empty function detection logic for ScriptEmptyFunctionRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class EmptyFunctionDetector(ScriptDetector):
    """Detects empty function bodies in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect empty function bodies in the AST."""
        violations = []
        self._check_functions(ast, violations, ast)
        
        for violation in violations:
            yield Violation(
                message=violation['message'],
                line=violation['line']
            )
    
    def _check_functions(self, node, violations: List[dict], full_ast):
        """Recursively check functions in AST nodes."""
        if hasattr(node, 'data') and node.data == 'function_expression':
            self._analyze_function(node, violations, full_ast)
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                self._check_functions(child, violations, full_ast)
    
    def _analyze_function(self, function_node, violations: List[dict], full_ast):
        """Analyze a specific function for empty body."""
        # Find the function body
        function_body = None
        
        if len(function_node.children) == 2:
            # Empty function: children are [function, function_body]
            function_body = function_node.children[1]
        elif len(function_node.children) == 3:
            # Non-empty function: children are [function, params, source_elements]
            function_body = function_node.children[2]
        
        # Check if function body is empty
        if function_body and self._is_empty_function_body(function_body):
            # Use the proper function context mapping to get the function name
            function_name = self.get_function_context_for_node(function_node, full_ast)
            
            if function_name:
                message = f"Function '{function_name}' has empty body - implement the function or remove it"
            else:
                message = "Function has empty body - implement the function or remove it"
            
            violations.append({
                'message': message,
                'line': self.get_line_number(function_node)
            })
    
    
    def _is_empty_function_body(self, function_body) -> bool:
        """Check if function body is empty (only whitespace/comments)"""
        if not hasattr(function_body, 'children'):
            return True
        
        # If the function body is a direct statement (like return_statement), it's not empty
        if hasattr(function_body, 'data') and function_body.data in ['return_statement', 'expression_statement']:
            return False
        
        # If the function body has no children, it's empty
        if len(function_body.children) == 0:
            return True
        
        # Check if body has any meaningful statements
        for child in function_body.children:
            if hasattr(child, 'data'):
                # If we find any statement that's not just whitespace, it's not empty
                if child.data in ['statement', 'expression_statement', 'return_statement', 
                                'if_statement', 'while_statement', 'for_statement',
                                'assignment_expression', 'call_expression', 'identifier_expression',
                                'literal_expression', 'binary_expression', 'unary_expression',
                                'variable_statement', 'source_elements']:
                    return False
        
        return True
