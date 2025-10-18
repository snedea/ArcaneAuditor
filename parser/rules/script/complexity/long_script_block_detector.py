#!/usr/bin/env python3
"""Long script block detection logic for LongScriptBlockRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class LongScriptBlockDetector(ScriptDetector):
    """Detects script blocks that exceed maximum line count."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1, max_lines: int = 30):
        super().__init__(file_path, line_offset)
        self.max_lines = max_lines  # Configurable threshold, default 30
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect script blocks that exceed maximum line count in the AST."""
        # Skip the 'script' field entirely - it only contains function definitions
        # which are handled by ScriptLongFunctionRule, not ScriptLongBlockRule
        if field_name == 'script':
            return
        
        # Skip function definitions - those are handled by ScriptLongFunctionRule
        if self._is_function_definition(ast):
            return
        
        # Use the same counting method as ScriptLongFunctionRule
        line_count = self._count_script_lines(ast)
        
        if line_count > self.max_lines:
            # Get line number from AST using standardized method
            line_number = self.get_line_from_tree_node(ast)
            
            message = f"Script block in '{field_name}' has {line_count} lines (max recommended: {self.max_lines}). Consider breaking it into smaller functions or extracting logic to separate methods."
            
            yield Violation(
                message=message,
                line=line_number
            )
    
    def _count_script_lines(self, ast: Tree) -> int:
        """Count the number of lines in a script block, excluding function definitions."""
        if not hasattr(ast, 'children'):
            return 1
        
        # Count actual lines by finding the range of line numbers, excluding functions
        min_line = None
        max_line = None
        
        # Traverse all nodes in the script block to find line number range
        def find_line_range(node):
            nonlocal min_line, max_line
            
            # Skip function definitions
            if self._is_function_definition(node):
                return
            
            # Check if this node has a line number
            if hasattr(node, 'line') and node.line is not None:
                if min_line is None or node.line < min_line:
                    min_line = node.line
                if max_line is None or node.line > max_line:
                    max_line = node.line
            
            # Recursively check children
            if hasattr(node, 'children'):
                for child in node.children:
                    find_line_range(child)
        
        find_line_range(ast)
        
        # Calculate line count
        if min_line is not None and max_line is not None:
            return max_line - min_line + 1
        
        # Fallback: count non-function statements if we can't determine line range
        non_function_count = 0
        if hasattr(ast, 'children'):
            for child in ast.children:
                if not self._is_function_definition(child):
                    non_function_count += 1
        
        return non_function_count if non_function_count > 0 else 1
    
    def _is_function_definition(self, ast: Tree) -> bool:
        """Check if the AST represents a function definition."""
        if not ast or not hasattr(ast, 'data'):
            return False
        
        # Check for function definition patterns
        if ast.data in ['function_declaration', 'function_expression', 'arrow_function']:
            return True
        
        # Check for variable statements that contain function expressions
        if ast.data == 'variable_statement':
            return self._variable_statement_contains_function(ast)
        
        # Check if any child is a function definition
        if hasattr(ast, 'children'):
            for child in ast.children:
                if hasattr(child, 'data') and child.data in ['function_declaration', 'function_expression', 'arrow_function']:
                    return True
                # Also check variable statements
                if hasattr(child, 'data') and child.data == 'variable_statement':
                    if self._variable_statement_contains_function(child):
                        return True
        
        return False
    
    def _variable_statement_contains_function(self, variable_statement: Tree) -> bool:
        """Check if a variable statement contains a function definition."""
        if not hasattr(variable_statement, 'children'):
            return False
        
        for child in variable_statement.children:
            if hasattr(child, 'data'):
                if child.data == 'variable_declaration':
                    # Check if the variable declaration has a function expression
                    if hasattr(child, 'children'):
                        for grandchild in child.children:
                            if hasattr(grandchild, 'data') and grandchild.data == 'function_expression':
                                return True
        
        return False
    
