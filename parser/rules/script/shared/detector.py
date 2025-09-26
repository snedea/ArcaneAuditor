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
        if hasattr(node, 'meta') and hasattr(node.meta, 'line'):
            return node.meta.line + self.line_offset - 1
        return 1
