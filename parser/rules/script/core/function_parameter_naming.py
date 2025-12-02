"""Script function parameter naming rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .function_parameter_naming_detector import FunctionParameterNamingDetector


class ScriptFunctionParameterNamingRule(ScriptRuleBase):
    """Rule to check for function parameter naming conventions."""

    DESCRIPTION = "Ensures function parameters follow lowerCamelCase naming convention"
    SEVERITY = "ADVICE"
    DETECTOR = FunctionParameterNamingDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
