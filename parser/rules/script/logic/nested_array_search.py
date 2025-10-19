"""Script nested array search rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .nested_array_search_detector import NestedArraySearchDetector


class ScriptNestedArraySearchRule(ScriptRuleBase):
    """Rule to detect nested array search patterns that cause severe performance issues."""

    DESCRIPTION = "Detects nested array search patterns that cause severe performance issues"
    SEVERITY = "ADVICE"
    DETECTOR = NestedArraySearchDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
