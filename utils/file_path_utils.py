"""
Utility functions for file path processing.
"""

import re
import os


def strip_uuid_prefix(file_path: str) -> str:
    """
    Strip UUID prefix from filename if present.
    
    Workday Extend files uploaded via the web interface may have UUID prefixes
    added to prevent filename conflicts (format: uuid_filename.ext).
    
    This function only strips actual UUIDs (8-4-4-4-12 hex digits), not arbitrary
    hex sequences. This prevents incorrectly stripping prefixes like 'e_' or 'a_'.
    
    Args:
        file_path: Full file path or just filename
        
    Returns:
        File path with UUID prefix removed, or original path if no UUID prefix found
        
    Examples:
        >>> strip_uuid_prefix('50356922-5e0c-454f-a39a-2b8ca88c379c_myPage.pmd')
        'myPage.pmd'
        >>> strip_uuid_prefix('e_TestArrayNesting.pmd')
        'e_TestArrayNesting.pmd'  # Not a UUID, so not stripped
        >>> strip_uuid_prefix('presentation/myPage.pmd')
        'presentation/myPage.pmd'  # No UUID prefix
    """
    if not file_path:
        return file_path
    
    # Extract just the filename (without path)
    filename_with_ext = os.path.basename(file_path)
    dir_path = os.path.dirname(file_path)
    
    # Strip UUID prefix if present (format: uuid_filename.ext)
    # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (8-4-4-4-12 hex digits)
    # Only match actual UUIDs, not arbitrary hex sequences
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_'
    cleaned_filename = re.sub(uuid_pattern, '', filename_with_ext)
    
    # Reconstruct path if there was a directory component
    if dir_path:
        return os.path.join(dir_path, cleaned_filename)
    
    return cleaned_filename

