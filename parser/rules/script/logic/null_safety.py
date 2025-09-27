"""Script null safety rule using unified architecture."""

from typing import Generator, Set
from ...script.shared import ScriptRuleBase
from ...base import Finding
from ....models import PMDModel
from .null_safety_detector import NullSafetyDetector


class ScriptNullSafetyRule(ScriptRuleBase):
    """Validates that property access chains are properly null-safe."""

    DESCRIPTION = "Ensures property access chains are protected against null reference exceptions"
    SEVERITY = "WARNING"
    DETECTOR = NullSafetyDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1) -> Generator[Finding, None, None]:
        """Check script content using the detector with context awareness."""
        # Parse the script content
        ast = self._parse_script_content(script_content)
        if not ast:
            return
        
        # Determine safe variables based on field context
        safe_variables = self._get_safe_variables_for_field(field_name, file_path)
        
        # Use detector to find violations
        detector = self.DETECTOR(file_path, line_offset, safe_variables)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        for violation in violations:
            yield Finding(
                rule=self,
                message=violation.message,
                line=violation.line,
                column=violation.column,
                file_path=file_path
            )

    def _get_safe_variables_for_field(self, field_name: str, file_path: str) -> Set[str]:
        """Determine which variables are safe based on the field context (exclude/render conditions)."""
        safe_variables = set()
        
        # For now, return empty set - the complex context logic can be added later
        # This maintains the basic functionality while using the unified architecture
        return safe_variables