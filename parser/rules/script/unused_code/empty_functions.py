"""Script empty function rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .empty_function_detector import EmptyFunctionDetector


class ScriptEmptyFunctionRule(ScriptRuleBase):
    """Rule to check for empty function bodies."""

    DESCRIPTION = "Ensures functions have actual implementation (not empty bodies)"
    SEVERITY = "SEVERE"
    DETECTOR = EmptyFunctionDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
