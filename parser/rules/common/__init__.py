"""Shared utilities for all rule types."""

from .violation import Violation
from .line_utils import (
    get_line_number, 
    extract_line_from_source,
    ASTLineUtils,
    PMDLineUtils,
    LineNumberUtils  # Legacy compatibility
)

__all__ = [
    'Violation',
    'get_line_number', 
    'extract_line_from_source',
    'ASTLineUtils',
    'PMDLineUtils',
    'LineNumberUtils'  # Legacy compatibility
]
