"""Script variable naming rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .variable_naming_detector import VariableNamingDetector


class ScriptVariableNamingRule(ScriptRuleBase):
    """Rule to check for variable naming conventions."""

    DESCRIPTION = "Ensures variables follow lowerCamelCase naming convention"
    SEVERITY = "ADVICE"
    DETECTOR = VariableNamingDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
