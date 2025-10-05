"""Base detector class for script analysis."""

from abc import ABC, abstractmethod
from typing import Any, List
from .violation import Violation


class ScriptDetector(ABC):
    """Base class for script analysis detectors."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        """Initialize detector with file context."""
        self.file_path = file_path
        self.line_offset = line_offset
    
    @abstractmethod
    def detect(self, ast: Any) -> List[Violation]:
        """
        Analyze AST and return list of violations.
        
        Args:
            ast: Parsed AST node
            
        Returns:
            List of Violation objects
        """
        pass
    
    def get_line_number(self, node: Any) -> int:
        """Get line number from AST node with offset."""
        from ...common import ASTLineUtils
        return ASTLineUtils.get_line_number(node, self.line_offset)
    
    def get_line_number_from_token(self, token: Any) -> int:
        """Get line number from token with offset - more reliable than get_line_number()."""
        # First try direct token access (most reliable for Lark tokens)
        relative_line = getattr(token, 'line', 1) or 1
        return relative_line + self.line_offset - 1
    
    def get_line_from_tree_node(self, node: Any) -> int:
        """Get line number from a Tree node by finding the first token with line info."""
        if hasattr(node, 'children') and len(node.children) > 0:
            for child in node.children:
                # Check if child has line info directly
                if hasattr(child, 'line') and child.line is not None:
                    return child.line + self.line_offset - 1
                # If child is a Tree, recurse into it
                elif hasattr(child, 'children') and len(child.children) > 0:
                    for grandchild in child.children:
                        if hasattr(grandchild, 'line') and grandchild.line is not None:
                            return grandchild.line + self.line_offset - 1
        return self.line_offset