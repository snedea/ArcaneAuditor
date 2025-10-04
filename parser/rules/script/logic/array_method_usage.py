"""Script array method usage rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .array_method_usage_detector import ArrayMethodUsageDetector


class ScriptArrayMethodUsageRule(ScriptRuleBase):
    """Rule to detect manual loops that could be replaced with array higher-order methods."""

    DESCRIPTION = "Detects manual loops that could be replaced with array higher-order methods like map, filter, forEach"
    SEVERITY = "ADVICE"
    DETECTOR = ArrayMethodUsageDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _check_manual_loops(self, script_content, field_name, file_path, line_offset=1, context=None):
        """Check for manual loops that could use array higher-order methods."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Create detector
        detector = self.DETECTOR(file_path, line_offset)
        
        # Use detector to find violations
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        for violation in violations:
            yield self._create_finding_from_violation(violation, file_path)