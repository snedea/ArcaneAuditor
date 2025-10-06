"""Script function return consistency rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .return_consistency_detector import ReturnConsistencyDetector


class ScriptFunctionReturnConsistencyRule(ScriptRuleBase):
    """Rule to check for consistent return patterns in script functions."""
    
    DESCRIPTION = "Functions should have consistent return patterns - either all code paths return a value or none do"
    SEVERITY = "ACTION"
    DETECTOR = ReturnConsistencyDetector
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION