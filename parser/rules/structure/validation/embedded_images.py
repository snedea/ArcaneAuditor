"""
Rule to detect embedded images in PMD and POD files.

Images should be stored as external files and referenced by path, not embedded directly
as base64 data or inline image data in the application files.

This rule checks for:
- Base64 encoded image data (data:image/...)
- Large inline image data that should be external files
- Image widgets with embedded content instead of file references
"""
import re
import base64
from typing import Generator, List, Dict, Any, Optional

from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class EmbeddedImagesRule(StructureRuleBase):
    """
    Detects embedded images that should be stored as external files.
    
    This rule checks for:
    - Base64 encoded image data (data:image/...)
    - Large inline image data in image widgets
    - Image content that should be referenced by file path instead
    """
    
    ID = "EmbeddedImagesRule"
    DESCRIPTION = "Detects embedded images that should be stored as external files"
    SEVERITY = "WARNING"
    
    # Minimum size threshold for considering content as potentially embedded image data
    MIN_IMAGE_SIZE_THRESHOLD = 100  # characters
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for embedded images."""
        yield from self._check_pmd_embedded_images(pmd_model)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for embedded images."""
        yield from self._check_pod_embedded_images(pod_model)
    
    def _check_pmd_embedded_images(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Check PMD file for embedded images."""
        # Convert PMD model to dictionary for recursive checking
        pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_embedded_images(pmd_dict, pmd_model.file_path)
    
    def _check_pod_embedded_images(self, pod_model: PodModel) -> Generator[Finding, None, None]:
        """Check POD file for embedded images."""
        # Convert POD model to dictionary for recursive checking
        pod_dict = pod_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_embedded_images(pod_dict, pod_model.file_path)
    
    def _check_string_values_for_embedded_images(self, model: Any, file_path: str) -> Generator[Finding, None, None]:
        """Recursively check string values for embedded images."""
        if isinstance(model, dict):
            for key, value in model.items():
                if isinstance(value, str):
                    yield from self._check_string_for_embedded_images(value, file_path, key)
                elif isinstance(value, (dict, list)):
                    yield from self._check_string_values_for_embedded_images(value, file_path)
        elif isinstance(model, list):
            for i, item in enumerate(model):
                if isinstance(item, str):
                    yield from self._check_string_for_embedded_images(item, file_path, f"[{i}]")
                elif isinstance(item, (dict, list)):
                    yield from self._check_string_values_for_embedded_images(item, file_path)
    
    def _check_string_for_embedded_images(self, text: str, file_path: str, field_name: str) -> Generator[Finding, None, None]:
        """Check a single string for embedded image data."""
        if not text or len(text) < self.MIN_IMAGE_SIZE_THRESHOLD:
            return
        
        # Pattern to match base64 encoded images (data:image/...)
        base64_image_pattern = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+'
        
        matches = list(re.finditer(base64_image_pattern, text, re.IGNORECASE))
        for match in matches:
            # Calculate line number
            line_num = text[:match.start()].count('\n') + 1
            
            yield self._create_finding(
                message=f"Embedded base64 image found in {field_name}. Consider storing the image as an external file and referencing it by path instead.",
                file_path=file_path,
                line=line_num,
                column=match.start() - text.rfind('\n', 0, match.start()) if '\n' in text[:match.start()] else match.start() + 1
            )
        
        # Check for large binary-like content that might be embedded image data
        # Look for long strings of base64-like characters or binary data
        # Only check if we haven't already found base64 images
        if not matches and self._is_potentially_embedded_image_data(text):
            # Calculate approximate line number (this is a heuristic)
            line_num = text[:len(text)//2].count('\n') + 1
            
            yield self._create_finding(
                message=f"Large embedded content found in {field_name} that appears to be image data. Consider storing images as external files and referencing them by path.",
                file_path=file_path,
                line=line_num
            )
    
    def _is_potentially_embedded_image_data(self, text: str) -> bool:
        """Check if text appears to be embedded image data."""
        if len(text) < self.MIN_IMAGE_SIZE_THRESHOLD:
            return False
        
        # Check for high ratio of base64 characters (A-Z, a-z, 0-9, +, /, =)
        base64_chars = sum(1 for c in text if c.isalnum() or c in '+/=')
        base64_ratio = base64_chars / len(text)
        
        # If more than 80% of characters are base64-like, it might be embedded image data
        if base64_ratio > 0.8:
            return True
        
        # Check for common image file signatures in the text
        image_signatures = [
            b'\xFF\xD8\xFF',  # JPEG
            b'\x89PNG',       # PNG
            b'GIF8',          # GIF
            b'BM',            # BMP
        ]
        
        # Convert text to bytes for signature checking
        try:
            text_bytes = text.encode('utf-8')
            for signature in image_signatures:
                if signature in text_bytes:
                    return True
        except UnicodeEncodeError:
            pass
        
        return False
