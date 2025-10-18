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
        
        # For embedded script blocks (onChange, onLoad, etc.), count ALL lines
        # including inline functions, callbacks, and procedural code
        # The goal is to keep these blocks tiny and push logic to script section
        
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
        """Count the number of lines in a script block, including ALL code."""
        if not hasattr(ast, 'children'):
            return 1
        
        # Count actual lines by collecting all code line numbers
        counted_lines = set()
        
        # Traverse all nodes in the script block to collect line numbers
        def collect_lines(node):
            # Count ALL code lines - no exceptions for inline functions or callbacks
            # The goal is to keep embedded script blocks tiny
            if hasattr(node, 'line') and node.line is not None:
                # Only count actual code (not empty lines, comments, template markers)
                if self._is_code_line(node):
                    counted_lines.add(node.line)
            
            # Recursively check all children
            if hasattr(node, 'children'):
                for child in node.children:
                    collect_lines(child)
        
        collect_lines(ast)
        
        # Calculate line count based on actual counted lines
        if counted_lines:
            return len(counted_lines)
        
        # Fallback: count all statements if we can't determine line range
        total_count = 0
        if hasattr(ast, 'children'):
            for child in ast.children:
                total_count += 1
        
        return total_count if total_count > 0 else 1
    
    def _is_code_line(self, node: Tree) -> bool:
        """Check if a node represents actual code (not empty lines, comments, or template markers)."""
        # Check if node has type attribute (Lark tokens)
        if hasattr(node, 'type'):
            # Skip whitespace and comments (exclusion list approach)
            if node.type in ['WHITESPACE', 'COMMENT']:
                return False
            
            # Don't skip NEWLINE tokens - they represent actual line breaks that should be counted
            # The goal is to count procedural code lines, and NEWLINE tokens are part of that
            
            # Count actual code tokens (exclusion list approach)
            # Only exclude specific non-code types, everything else is code
            return True
        
        # Check if node has data attribute (Lark Tree nodes)
        if hasattr(node, 'data'):
            # Skip template markers
            if node.data in ['template_start', 'template_end']:
                return False
            
            # Skip comments
            if node.data in ['line_comment', 'block_comment']:
                return False
            
            # Skip empty statements
            if node.data == 'empty_statement':
                return False
            
            # Don't skip EOS tokens - they represent actual line breaks that should be counted
            # The goal is to count procedural code lines, and EOS tokens are part of that
            
            # Everything else is considered code
            return True
        
        return False
