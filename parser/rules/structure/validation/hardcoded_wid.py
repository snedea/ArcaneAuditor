"""
Rule to detect hardcoded WID (Workday ID) values in PMD and POD files.

WIDs should be configured in app attributes and not hardcoded in the app source.
There are two exceptions that are allowed in the code:
- Business process WIDs: "d9e41a8c446c11de98360015c5e6daf6" and "d9e4223e446c11de98360015c5e6daf6"

A WID can be identified as a 32 character long string that is alphanumeric.
"""
import re
from typing import Generator, List, Dict, Any, Optional
from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ...line_number_utils import LineNumberUtils
from ..shared import StructureRuleBase


class HardcodedWidRule(StructureRuleBase):
    """
    Detects hardcoded WID (Workday ID) values that should be configured in app attributes.
    
    This rule checks for:
    - 32-character alphanumeric strings that look like WIDs
    - Excludes allowed business process WIDs
    - Recommends using app attributes instead of hardcoded values
    """
    
    ID = "HardcodedWidRule"
    DESCRIPTION = "Detects hardcoded WID values that should be configured in app attributes"
    SEVERITY = "WARNING"
    
    # Allowed business process WIDs that are exceptions
    ALLOWED_WIDS = {
        "d9e41a8c446c11de98360015c5e6daf6",  # Business process WID
        "d9e4223e446c11de98360015c5e6daf6"   # Business process WID
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for hardcoded WIDs."""
        yield from self._check_pmd_hardcoded_wids(pmd_model)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for hardcoded WIDs."""
        yield from self._check_pod_hardcoded_wids(pod_model)
    
    def _check_pmd_hardcoded_wids(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Check PMD file for hardcoded WID values."""
        # Convert PMD model to dictionary for recursive checking
        pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_wids(pmd_dict, pmd_model.file_path, pmd_model=pmd_model)
    
    def _check_pod_hardcoded_wids(self, pod_model: PodModel) -> Generator[Finding, None, None]:
        """Check POD file for hardcoded WID values."""
        # Convert POD model to dictionary for recursive checking
        pod_dict = pod_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_wids(pod_dict, pod_model.file_path, pod_model=pod_model)
    
    def _check_string_values_for_wids(self, model: Any, file_path: str, pmd_model: PMDModel = None, pod_model: PodModel = None) -> Generator[Finding, None, None]:
        """Recursively check string values for hardcoded WIDs."""
        if isinstance(model, dict):
            for key, value in model.items():
                if isinstance(value, str):
                    yield from self._check_string_for_wids(value, file_path, key, pmd_model, pod_model)
                elif isinstance(value, (dict, list)):
                    yield from self._check_string_values_for_wids(value, file_path, pmd_model, pod_model)
        elif isinstance(model, list):
            for i, item in enumerate(model):
                if isinstance(item, str):
                    yield from self._check_string_for_wids(item, file_path, f"[{i}]", pmd_model, pod_model)
                elif isinstance(item, (dict, list)):
                    yield from self._check_string_values_for_wids(item, file_path, pmd_model, pod_model)
    
    def _check_string_for_wids(self, text: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None) -> Generator[Finding, None, None]:
        """Check a single string for hardcoded WID values."""
        if not text:
            return
        
        # Pattern to match 32-character alphanumeric strings (WIDs)
        # This will match strings that are exactly 32 characters long and contain only a-f and 0-9
        wid_pattern = r'\b[a-f0-9]{32}\b'
        
        matches = re.finditer(wid_pattern, text, re.IGNORECASE)
        for match in matches:
            wid_value = match.group().lower()
            
            # Skip if this is an allowed business process WID
            if wid_value in self.ALLOWED_WIDS:
                continue
            
            # Calculate line number by searching in source content
            line_num = self._find_wid_line_number(wid_value, pmd_model, pod_model)
            
            yield self._create_finding(
                message=f"Hardcoded WID '{wid_value}' found in {field_name}. Consider configuring WIDs in app attributes instead of hardcoding them.",
                file_path=file_path,
                line=line_num,
                column=1  # Column calculation is complex for extracted values, default to 1
            )
    
    def _find_wid_line_number(self, wid_value: str, pmd_model: PMDModel = None, pod_model: PodModel = None) -> int:
        """Find the line number where a WID value appears in the source content."""
        source_content = None
        
        if pmd_model and hasattr(pmd_model, 'source_content'):
            source_content = pmd_model.source_content
        elif pod_model and hasattr(pod_model, 'source_content'):
            source_content = pod_model.source_content
        
        if not source_content:
            return 1
        
        try:
            lines = source_content.split('\n')
            
            # Search for the WID value in the source content
            for i, line in enumerate(lines):
                if wid_value.lower() in line.lower():
                    return i + 1  # Convert to 1-based line numbering
            
            return 1  # Fallback if not found
        except Exception:
            return 1
