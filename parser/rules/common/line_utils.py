"""Shared line number utilities for all rule types."""

from typing import Any


def get_line_number(node: Any, line_offset: int = 1) -> int:
    """Get line number from AST node with offset."""
    if hasattr(node, 'meta') and hasattr(node.meta, 'line'):
        return node.meta.line + line_offset - 1
    return 1


def extract_line_from_source(source_content: str, search_text: str, start_line: int = 1) -> int:
    """Extract line number from source content by searching for text."""
    if not source_content or not search_text:
        return start_line
    
    lines = source_content.split('\n')
    for i, line in enumerate(lines):
        if search_text in line:
            return i + 1
    
    return start_line
