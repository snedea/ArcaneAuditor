#!/usr/bin/env python3
"""Long script block detection logic for LongScriptBlockRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class LongScriptBlockDetector(ScriptDetector):
    """Detects script blocks that exceed maximum line count."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1, max_lines: int = 30, skip_comments: bool = False, skip_blank_lines: bool = False, source_text: str = ""):
        super().__init__(file_path, line_offset, source_text)
        self.max_lines = max_lines
        self.skip_comments = skip_comments
        self.skip_blank_lines = skip_blank_lines  # Configurable threshold, default 30
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect script blocks that exceed maximum line count in the AST."""
        # Skip the 'script' field entirely - it only contains function definitions
        # which are handled by ScriptLongFunctionRule, not ScriptLongBlockRule
        if field_name == 'script':
            return  # Return empty generator
        
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
        """
        Count lines using source text (ESLint approach).
        
        For script blocks, we count from the first line to the last line
        of the entire block using the source text.
        """
        if not hasattr(ast, 'children'):
            return 1
        
        # Collect all line numbers from the AST
        counted_lines = set()
        
        def collect_lines(node):
            if hasattr(node, 'line') and node.line is not None:
                if self._should_count_line(node):
                    counted_lines.add(node.line)
            
            if hasattr(node, 'children'):
                for child in node.children:
                    collect_lines(child)
        
        collect_lines(ast)
        
        if not counted_lines:
            return 1
        
        # Get the range from AST
        min_line = min(counted_lines)
        max_line = max(counted_lines)
        
        # For script blocks, the end is max_line (no separate closing brace to find
        # since the block itself is the entire script content)
        # Use the shared helper to count physical lines
        return self.count_physical_lines(min_line, max_line)
    
    def _should_count_line(self, node) -> bool:
        """
        Determine if a node's line should be counted based on skip flags.
        
        Args:
            node: AST node to check
            
        Returns:
            True if the line should be counted, False otherwise
        """
        # Check if node has type attribute (Lark tokens)
        if hasattr(node, 'type'):
            # Always skip whitespace tokens
            if node.type == 'WHITESPACE':
                return False
            
            # Skip comment tokens if flag is set
            if self.skip_comments and node.type == 'COMMENT':
                return False
            
            # Skip newline/blank line tokens if flag is set
            if self.skip_blank_lines and node.type in ['NEWLINE', 'NL']:
                return False
            
            return True
        
        # Check if node has data attribute (Lark Tree nodes)
        if hasattr(node, 'data'):
            # Skip comment nodes if flag is set
            if self.skip_comments and node.data in ['line_comment', 'block_comment', 'comment']:
                return False
            
            # Skip template markers (always)
            if node.data in ['template_start', 'template_end']:
                return False
            
            # Skip empty statements (always)
            if node.data == 'empty_statement':
                return False
            
            return True
        
        return True
