"""Script unused variables rule using unified architecture."""

from typing import Generator, Set
from ...script.shared import ScriptRuleBase
from ...base import Finding
from ....models import PMDModel, PodModel
from .unused_variables_detector import UnusedVariableDetector


class ScriptUnusedVariableRule(ScriptRuleBase):
    """Validates that all declared variables are used with proper scoping."""

    DESCRIPTION = "Ensures all declared variables are used (prevents dead code) with proper scoping awareness"
    SEVERITY = "WARNING"
    DETECTOR = UnusedVariableDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector with scope awareness."""
        # Parse the script content
        ast = self._parse_script_content(script_content, context)
        if not ast:
            return
        
        # Determine scope information
        is_global_scope = (field_name == 'script')
        global_functions = self._get_global_functions_for_file(file_path)
        
        # Use detector to find violations
        detector = self.DETECTOR(file_path, line_offset, is_global_scope, global_functions)
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

    def _get_global_functions_for_file(self, file_path: str) -> Set[str]:
        """Get global functions available for the given file."""
        # For now, return empty set - the complex global function logic can be added later
        # This maintains the basic functionality while using the unified architecture
        return set()