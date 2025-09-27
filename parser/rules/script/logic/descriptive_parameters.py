"""Script descriptive parameter rule using unified architecture."""

from typing import Generator, Dict, List
from ...script.shared import ScriptRuleBase
from .descriptive_parameters_detector import DescriptiveParameterDetector


class ScriptDescriptiveParameterRule(ScriptRuleBase):
    """Validates that functional method parameters use descriptive names instead of single letters."""

    DESCRIPTION = "Ensures functional method parameters use descriptive names (except 'i', 'j', 'k' for indices)"
    SEVERITY = "INFO"
    DETECTOR = DescriptiveParameterDetector

    # Expose constants for testing
    FUNCTIONAL_METHODS = {'map', 'filter', 'find', 'forEach', 'reduce', 'sort'}
    ALLOWED_SINGLE_LETTERS = {'i', 'j', 'k'}

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _check_parameter_names(self, script_content: str, field_name: str, file_path: str, line_offset: int, context=None):
        """Check for non-descriptive parameter names in functional methods."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Create detector and set original content for pattern-based analysis
        detector = self.DETECTOR(file_path, line_offset)
        detector.set_original_content(script_content)
        
        # Use detector to find violations
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        for violation in violations:
            yield self._create_finding_from_violation(violation, file_path)