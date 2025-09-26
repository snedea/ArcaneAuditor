"""Script variable naming rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .variable_naming_detector import VariableNamingDetector


class ScriptVariableNamingRule(ScriptRuleBase):
    """Rule to check for variable naming conventions."""

    DESCRIPTION = "Ensures variables follow lowerCamelCase naming convention"
    SEVERITY = "WARNING"
    DETECTOR = VariableNamingDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
