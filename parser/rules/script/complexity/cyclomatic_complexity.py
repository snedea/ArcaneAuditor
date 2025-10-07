"""Script cyclomatic complexity rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .cyclomatic_complexity_detector import CyclomaticComplexityDetector


class ScriptComplexityRule(ScriptRuleBase):
    """Rule to check for excessive cyclomatic complexity."""

    DESCRIPTION = "Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)"
    SEVERITY = "ADVICE"
    DETECTOR = CyclomaticComplexityDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
