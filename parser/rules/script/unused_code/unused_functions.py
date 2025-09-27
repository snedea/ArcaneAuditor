"""Script unused functions rule using unified architecture."""

from typing import Generator, Set
from ...script.shared import ScriptRuleBase
from ...base import Finding
from .unused_functions_detector import UnusedFunctionsDetector


class ScriptUnusedFunctionRule(ScriptRuleBase):
    """Validates that functions are not declared but never used."""

    DESCRIPTION = "Ensures functions are not declared but never used"
    SEVERITY = "WARNING"
    DETECTOR = UnusedFunctionsDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector."""
        # Parse the script content
        ast = self._parse_script_content(script_content, context)
        if not ast:
            return
        
        # For now, use empty sets - the complex function registry logic can be added later
        all_declared_functions = set()
        all_function_calls = set()
        
        # Use detector to find violations
        detector = self.DETECTOR(file_path, line_offset, all_declared_functions, all_function_calls)
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