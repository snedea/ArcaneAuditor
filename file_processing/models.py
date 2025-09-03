"""
Data models for file processing operations.
"""

from dataclasses import dataclass
from pathlib import Path

@dataclass
class SourceFile:
    """A data class to hold a file's path and its content."""
    path: Path
    content: str
    size: int
    encoding: str = "utf-8"
    
    def __post_init__(self):
        """Validate the source file data after initialization."""
        if not self.path or not self.content:
            raise ValueError("Path and content must be provided")
        if self.size <= 0:
            raise ValueError("File size must be positive")

    def __repr__(self):
        return f"SourceFile(path='{self.path.name}', size={self.size} bytes)"
