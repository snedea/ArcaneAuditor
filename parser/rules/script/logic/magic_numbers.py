"""Script magic number rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .magic_number_detector import MagicNumberDetector
from ...base import Finding


class ScriptMagicNumberRule(ScriptRuleBase):
    """Rule to check for magic numbers."""

    DESCRIPTION = "Ensures scripts don't contain magic numbers (use named constants)"
    SEVERITY = "ADVICE"
    DETECTOR = MagicNumberDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None):
        """Override to pass source text to detector for code context extraction."""
        # Strip <% %> tags from script content if present
        clean_script_content = self._strip_script_tags(script_content)
        
        # Parse the script content with context for caching
        ast = self._parse_script_content(clean_script_content, context)
        if not ast:
            return
        
        # Use detector to find violations, passing source text for code context
        detector = self.DETECTOR(file_path, line_offset, clean_script_content)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        if violations is not None and hasattr(violations, '__iter__') and not isinstance(violations, str):
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=file_path
                )

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
