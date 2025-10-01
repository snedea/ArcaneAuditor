from typing import Generator
from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class StringBooleanRule(StructureRuleBase):
    """Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans."""
    
    DESCRIPTION = "Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans"
    SEVERITY = "INFO"

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes the PMD model for string boolean values."""
        if not pmd_model.source_content:
            return
        
        # Check the raw source content for string boolean patterns
        yield from self._check_source_content_for_string_booleans(pmd_model)

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
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
                
                yield self._create_finding(
                    message=f"Field '{field_name}' has string value '{string_value}' instead of boolean {string_value}. Use boolean {string_value} instead of string '{string_value}'.",
                    file_path=model.file_path,
                    line=line_num
                )
