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
    SEVERITY = "ADVICE"
    
    
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
        
        # Check if this is a script field (contains <% %>)
        if '<%' in text and '%>' in text:
            # Use AST-based detection for script fields (respects comments)
            yield from self._check_script_for_embedded_images_ast(text, file_path, field_name)
        else:
            # Use regex for plain JSON values (no comments possible)
            yield from self._check_string_for_embedded_images_regex(text, file_path, field_name)
    
    def _check_string_for_embedded_images_regex(self, text: str, file_path: str, field_name: str) -> Generator[Finding, None, None]:
        """Check a plain string (non-script) for embedded images using regex."""
        # Pattern to match base64 encoded images (data:image/...) with minimum length
        base64_image_pattern = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]{20,}'
        
        matches = list(re.finditer(base64_image_pattern, text, re.IGNORECASE))
        for match in matches:
            # Calculate line number using unified method
            line_num = self.get_line_from_text_position(text, match.start())
            
            yield self._create_finding(
                message=f"Embedded base64 image found in {field_name}. Large files can cause performance issues and/or cause pages to exceed the file size limits. Consider linking to an external image file, instead of embedding it directly.",
                file_path=file_path,
                line=line_num
            )
    
    def _check_script_for_embedded_images_ast(self, script_content: str, file_path: str, field_name: str) -> Generator[Finding, None, None]:
        """Check a script field for embedded images using AST (ignores comments)."""
        from ....pmd_script_parser import pmd_script_parser
        
        try:
            # Strip script tags
            script_code = script_content.replace('<%', '').replace('%>', '').strip()
            if not script_code:
                return
            
            # Parse with AST
            ast = pmd_script_parser.parse(script_code)
            
            # Pattern to match base64 encoded images (with minimum length to avoid false positives)
            base64_image_pattern = r'^data:image/[^;]+;base64,[A-Za-z0-9+/=]{20,}$'
            
            # Extract all string literals from AST with context
            for variable_decl in ast.find_data('variable_declaration'):
                # Extract variable name
                var_name = None
                for child in variable_decl.children:
                    if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                        var_name = child.value
                        break
                
                # Check string literals in this variable declaration
                for literal_expr in variable_decl.find_data('literal_expression'):
                    if hasattr(literal_expr, 'children') and len(literal_expr.children) > 0:
                        token = literal_expr.children[0]
                        if hasattr(token, 'value'):
                            literal_value = token.value.strip('\'"')
                            
                            if re.match(base64_image_pattern, literal_value, re.IGNORECASE):
                                context = f"in variable '{var_name}' in {field_name}" if var_name else f"in {field_name}"
                                
                                yield self._create_finding(
                                    message=f"Embedded base64 image found {context}. Large files can cause performance issues and/or cause pages to exceed the file size limits. Consider linking to an external image file, instead of embedding it directly.",
                                    file_path=file_path,
                                    line=1  # Would need more sophisticated line tracking for AST
                                )
            # Success! Don't fall back to regex
        except Exception as e:
            # If AST parsing fails, fall back to regex (but this means comments won't be filtered)
            # Only fall back on parse errors, not on finding no matches
            import traceback
            if 'parse' in str(e).lower() or 'syntax' in str(e).lower():
                yield from self._check_string_for_embedded_images_regex(script_content, file_path, field_name)
    
