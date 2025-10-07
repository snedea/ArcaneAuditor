"""Script long function rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .long_function_detector import LongFunctionDetector


class ScriptLongFunctionRule(ScriptRuleBase):
    """Rule to check for functions that exceed maximum line count."""

    DESCRIPTION = "Ensures functions don't exceed maximum line count (max 50 lines)"
    SEVERITY = "ADVICE"
    DETECTOR = LongFunctionDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
