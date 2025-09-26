"""Script magic number rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .magic_number_detector import MagicNumberDetector


class ScriptMagicNumberRule(ScriptRuleBase):
    """Rule to check for magic numbers."""

    DESCRIPTION = "Ensures scripts don't contain magic numbers (use named constants)"
    SEVERITY = "INFO"
    DETECTOR = MagicNumberDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
