"""Script console log rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .console_log_detector import ConsoleLogDetector


class ScriptConsoleLogRule(ScriptRuleBase):
    """Rule to check for console statements in scripts."""

    DESCRIPTION = "Ensures scripts don't contain console statements (production code)"
    SEVERITY = "SEVERE"
    DETECTOR = ConsoleLogDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
