"""Script string concatenation rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .string_concat_detector import StringConcatDetector


class ScriptStringConcatRule(ScriptRuleBase):
    """Rule to check for string concatenation using + operator."""

    DESCRIPTION = "Detects string concatenation with + operator - use PMD templates with backticks and {{ }} instead"
    SEVERITY = "WARNING"
    DETECTOR = StringConcatDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
