"""
Rule to detect embedded base64 images in PMD and POD files.

Images should be stored as external files and referenced by path, not embedded directly
as base64 data in the application files.

This rule checks for base64 encoded image data using the pattern:
data:image/[type];base64,[data]
"""
import re
from typing import Generator, Any

from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class EmbeddedImagesRule(StructureRuleBase):
    """
    Detects embedded base64 images that should be stored as external files.
    
    This rule checks for base64 encoded image data using the pattern:
    data:image/[type];base64,[data]
    
    Images should be stored as external files and referenced by path instead
    of being embedded directly in the application files.
    """
    
    ID = "EmbeddedImagesRule"
    DESCRIPTION = "Detects embedded images that should be stored as external files"
    SEVERITY = "ACTION"
    
    
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
        if not text:
            return
        
        # Pattern to match base64 encoded images (data:image/...)
        base64_image_pattern = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+'
        
        matches = list(re.finditer(base64_image_pattern, text, re.IGNORECASE))
        for match in matches:
            # Calculate line number using unified method
            line_num = self.get_line_from_text_position(text, match.start())
            
            yield self._create_finding(
                message=f"Embedded base64 image found in {field_name}. Consider storing the image as an external file and referencing it by path instead.",
                file_path=file_path,
                line=line_num
            )
    
