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
        # Skip function definitions - those are handled by ScriptLongFunctionRule
        if self._is_function_definition(ast):
            return
        
        # Use the same counting method as ScriptLongFunctionRule
        line_count = self._count_script_lines(ast)
        
        if line_count > self.max_lines:
            # Get line number from AST
            line_number = self._get_ast_line_number(ast)
            
            message = f"Script block in '{field_name}' has {line_count} lines (max recommended: {self.max_lines}). Consider breaking it into smaller functions or extracting logic to separate methods."
            
            yield Violation(
                message=message,
                line=line_number
            )
    
    def _count_script_lines(self, ast: Tree) -> int:
        """Count the number of lines in a script block using the same method as ScriptLongFunctionRule."""
        # Count the number of statements in the script (same as function body counting)
        if hasattr(ast, 'children'):
            return len(ast.children)
        return 1
    
    def _is_function_definition(self, ast: Tree) -> bool:
        """Check if the AST represents a function definition."""
        if not ast or not hasattr(ast, 'data'):
            return False
        
        # Check for function definition patterns
        if ast.data in ['function_declaration', 'function_expression', 'arrow_function']:
            return True
        
        # Check if any child is a function definition
        if hasattr(ast, 'children'):
            for child in ast.children:
                if hasattr(child, 'data') and child.data in ['function_declaration', 'function_expression', 'arrow_function']:
                    return True
        
        return False
    
    def _get_ast_line_number(self, ast: Tree) -> int:
        """Get line number from AST node using the same method as LongFunctionDetector."""
        if not ast:
            return self.line_offset
        
        # Try to get line number from the AST node itself
        if hasattr(ast, 'line') and ast.line is not None:
            return self.line_offset + ast.line - 1
        
        # Try to get line number from children (same approach as LongFunctionDetector)
        if hasattr(ast, 'children'):
            for child in ast.children:
                if hasattr(child, 'line') and child.line is not None:
                    return self.line_offset + child.line - 1
                # Also check grandchildren for line numbers
                if hasattr(child, 'children'):
                    for grandchild in child.children:
                        if hasattr(grandchild, 'line') and grandchild.line is not None:
                            return self.line_offset + grandchild.line - 1
        
        return self.line_offset
