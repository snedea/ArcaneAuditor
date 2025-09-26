"""Shared violation handling for script rules."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Violation:
    """Represents a code violation with consistent structure."""
    message: str
    line: int
    column: int = 1
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Ensure metadata is always a dict."""
        if self.metadata is None:
            self.metadata = {}
