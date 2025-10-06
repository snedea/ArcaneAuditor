"""Script unused function parameters rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from ...base import Finding
from .unused_parameters_detector import UnusedParametersDetector


class ScriptUnusedFunctionParametersRule(ScriptRuleBase):
    """Validates that function parameters are actually used in the function body."""

    DESCRIPTION = "Ensures function parameters are actually used in the function body"
    SEVERITY = "ACTION"
    DETECTOR = UnusedParametersDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION