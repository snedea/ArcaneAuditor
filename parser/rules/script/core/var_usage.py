"""Script variable usage rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .var_usage_detector import VarUsageDetector


class ScriptVarUsageRule(ScriptRuleBase):
    """Rule to check for use of 'var' instead of 'let' or 'const'."""

    DESCRIPTION = "Ensures scripts use 'let' or 'const' instead of 'var' (best practice)"
    SEVERITY = "ADVICE"
    DETECTOR = VarUsageDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
