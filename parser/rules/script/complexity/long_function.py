"""Script long function rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .long_function_detector import LongFunctionDetector
from ...base import Finding


class ScriptLongFunctionRule(ScriptRuleBase):
    """Rule to check for functions that exceed maximum line count."""

    DESCRIPTION = "Ensures functions don't exceed maximum line count (max 50 lines)"
    SEVERITY = "ADVICE"
    DETECTOR = LongFunctionDetector
    AVAILABLE_SETTINGS = {
        'max_lines': {'type': 'int', 'default': 50, 'description': 'Maximum lines allowed'},
        'skip_comments': {'type': 'bool', 'default': False, 'description': 'Skip comment lines when counting'},
        'skip_blank_lines': {'type': 'bool', 'default': False, 'description': 'Skip blank lines when counting'}
    }

    def __init__(self):
        super().__init__()
        self.max_lines = 50
        self.skip_comments = False  # Default to ESLint behavior
        self.skip_blank_lines = False  # Default to ESLint behavior

    def apply_settings(self, custom_settings: dict):
        """Apply custom settings from configuration."""
        if 'max_lines' in custom_settings:
            self.max_lines = custom_settings['max_lines']
        if 'skip_comments' in custom_settings:
            self.skip_comments = custom_settings['skip_comments']
        if 'skip_blank_lines' in custom_settings:
            self.skip_blank_lines = custom_settings['skip_blank_lines']

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None):
        """Override to pass custom settings to detector."""
        # Only analyze functions in the 'script' section
        if field_name and field_name != 'script':
            return
        
        # Strip <% %> tags from script content if present
        clean_script_content = self._strip_script_tags(script_content)
        
        # Parse the script content with context for caching
        ast = self._parse_script_content(clean_script_content, context)
        if not ast:
            return
        
        # Use detector to find violations, passing custom settings AND stripped content
        detector = self.DETECTOR(file_path, line_offset, self.skip_comments, self.skip_blank_lines, clean_script_content)
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
