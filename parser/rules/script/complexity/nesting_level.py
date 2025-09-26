"""Script nesting level rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .nesting_level_detector import NestingLevelDetector


class ScriptNestingLevelRule(ScriptRuleBase):
    """Rule to check for excessive nesting levels."""

    DESCRIPTION = "Ensures scripts don't have excessive nesting levels (max 4 levels)"
    SEVERITY = "WARNING"
    DETECTOR = NestingLevelDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
