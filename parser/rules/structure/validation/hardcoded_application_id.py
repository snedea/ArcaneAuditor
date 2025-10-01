"""
Rule to detect hardcoded applicationId values in PMD and POD files.

The applicationId value from the SMD file should never be hardcoded in PMD or POD files.
Instead, users should use the site.applicationId variable.

Note: AMD files are allowed to have applicationId as they are application configuration files.
"""
import re
from typing import Generator, List, Dict, Any, Optional

from ...base import Rule, Finding
from ....models import PMDModel, PodModel, ProjectContext


class HardcodedApplicationIdRule(Rule):
    """
    Detects hardcoded applicationId values that should be replaced with site.applicationId.
    
    This rule checks for:
    - Hardcoded applicationId strings in JSON values
    - Hardcoded applicationId strings in script expressions
    - Any string literal containing the applicationId value
    """
    
    ID = "HardcodedApplicationIdRule"
    DESCRIPTION = "Detects hardcoded applicationId values that should be replaced with site.applicationId"
    SEVERITY = "WARNING"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD and POD files for hardcoded applicationId values."""
        if not context.application_id:
            return  # No applicationId to check against
        
        app_id = context.application_id
        
        # Check PMD files
        for pmd_model in context.pmds.values():
            yield from self._check_pmd_hardcoded_app_id(pmd_model, app_id)
        
        # Check POD files  
        for pod_model in context.pods.values():
            yield from self._check_pod_hardcoded_app_id(pod_model, app_id)
    
    def _check_pmd_hardcoded_app_id(self, pmd_model: PMDModel, app_id: str) -> Generator[Finding, None, None]:
        """Check PMD file for hardcoded applicationId values."""
        # Check all string values in the PMD model
        yield from self._check_string_values_for_app_id(pmd_model, app_id, pmd_model.file_path)
    
    def _check_pod_hardcoded_app_id(self, pod_model: PodModel, app_id: str) -> Generator[Finding, None, None]:
        """Check POD file for hardcoded applicationId values."""
        # Check all string values in the POD model
        yield from self._check_string_values_for_app_id(pod_model, app_id, pod_model.file_path)
    
    def _check_string_values_for_app_id(self, model: Any, app_id: str, file_path: str) -> Generator[Finding, None, None]:
        """Recursively check string values for hardcoded applicationId."""
        if isinstance(model, dict):
            for key, value in model.items():
                if isinstance(value, str):
                    yield from self._check_string_for_app_id(value, app_id, file_path, key)
                elif isinstance(value, (dict, list)):
                    yield from self._check_string_values_for_app_id(value, app_id, file_path)
        elif isinstance(model, list):
            for i, item in enumerate(model):
                if isinstance(item, str):
                    yield from self._check_string_for_app_id(item, app_id, file_path, f"[{i}]")
                elif isinstance(item, (dict, list)):
                    yield from self._check_string_values_for_app_id(item, app_id, file_path)
    
    def _check_string_for_app_id(self, text: str, app_id: str, file_path: str, field_name: str) -> Generator[Finding, None, None]:
        """Check a single string for hardcoded applicationId values."""
        if not text or not app_id:
            return
        
        # Pattern to match hardcoded applicationId values
        # This will match:
        # - "applicationId": "actual_app_id"
        # - 'applicationId': 'actual_app_id'  
        # - applicationId: "actual_app_id"
        # - Any string literal containing the exact app_id value
        patterns = [
            # JSON key-value patterns
            rf'["\']applicationId["\']\s*:\s*["\']?{re.escape(app_id)}["\']?',
            # Direct string literals
            rf'["\']{re.escape(app_id)}["\']',
            # Script expressions with hardcoded app_id
            rf'["\']{re.escape(app_id)}["\']',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Skip if this is already using site.applicationId correctly
                context_before = text[max(0, match.start() - 50):match.start()]
                context_after = text[match.end():min(len(text), match.end() + 50)]
                
                # If we see site.applicationId nearby, this might be correct usage
                if 'site.applicationId' in context_before or 'site.applicationId' in context_after:
                    continue
                
                # Calculate line number
                line_num = text[:match.start()].count('\n') + 1
                
                yield Finding(
                    rule=self,
                    message=f"Hardcoded applicationId '{app_id}' found in {field_name}. Use site.applicationId instead.",
                    line=line_num,
                    file_path=file_path
                )
