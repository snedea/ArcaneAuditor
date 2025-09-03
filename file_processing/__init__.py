"""
File processing module for Workday Extend source files.
Provides functionality to extract and process zip archives containing source code.
"""

from .processor import FileProcessor, FileProcessingError, ZipProcessingError, FileReadError
from .config import FileProcessorConfig
from .models import SourceFile

__all__ = [
    'FileProcessor',
    'FileProcessingError', 
    'ZipProcessingError',
    'FileReadError',
    'FileProcessorConfig',
    'SourceFile'
]

# Version information
__version__ = "1.0.0"
