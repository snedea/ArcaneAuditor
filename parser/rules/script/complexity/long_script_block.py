#!/usr/bin/env python3
"""Long script block rule for PMD/POD files."""

from ...script.shared import ScriptRuleBase
from ...base import Finding
from .long_script_block_detector import LongScriptBlockDetector


class ScriptLongBlockRule(ScriptRuleBase):
    """Rule to check for script blocks that exceed maximum line count."""

    ID = "ScriptLongBlockRule"
    DESCRIPTION = "Ensures non-function script blocks in PMD/POD files don't exceed maximum line count (max 30 lines). Excludes function definitions which are handled by ScriptLongFunctionRule."
    SEVERITY = "ADVICE"
    DETECTOR = LongScriptBlockDetector

    def __init__(self):
        super().__init__()
        self.max_lines = 30  # Default threshold

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def apply_settings(self, custom_settings: dict):
        """Apply custom settings from configuration."""
        if 'max_lines' in custom_settings:
            self.max_lines = custom_settings['max_lines']
    
    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None):
        """Override to pass custom max_lines to detector."""
        # Parse the script content with context for caching
        ast = self._parse_script_content(script_content, context)
        if not ast:
            return
        
        # Use detector to find violations, passing the custom max_lines
        detector = self.DETECTOR(file_path, line_offset, self.max_lines)
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
