from ...base import Rule, Finding
from ....models import PMDModel, PODModel
from typing import Dict, Any, List


class StringBooleanRule(Rule):
    """Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans."""
    
    DESCRIPTION = "Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans"
    SEVERITY = "INFO"

    def analyze(self, context):
        """Main entry point - analyze all PMD models and POD models in the context."""
        # Analyze PMD models
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
        
        # Analyze POD models
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes the PMD model for string boolean values."""
        if not pmd_model.source_content:
            return
        
        # Check the raw source content for string boolean patterns
        yield from self._check_source_content_for_string_booleans(pmd_model)

    def visit_pod(self, pod_model: PODModel):
        """Analyzes the POD model for string boolean values."""
        if not pod_model.source_content:
            return
        
        # Check the raw source content for string boolean patterns
        yield from self._check_source_content_for_string_booleans(pod_model)

    def _check_source_content_for_string_booleans(self, model):
        """Check the source content for string boolean patterns."""
        import re
        
        lines = model.source_content.split('\n')
        
        # Pattern to match field: "true" or field: "false" or field:"true" or field:"false"
        pattern = r'"([^"]+)"\s*:\s*"(true|false)"'
        
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                field_name = match.group(1)
                string_value = match.group(2)
                
                yield Finding(
                    rule=self,
                    message=f"Field '{field_name}' has string value '{string_value}' instead of boolean {string_value}. Use boolean {string_value} instead of string '{string_value}'.",
                    line=line_num,
                    column=match.start() + 1,
                    file_path=model.file_path
                )
