"""Script dead code rule using unified architecture."""

from typing import Generator, Dict, Any
from ...base import Finding
from ...script.shared import ScriptRuleBase
from .script_dead_code_detector import ScriptDeadCodeDetector


class ScriptDeadCodeRule(ScriptRuleBase):
    """Detects dead code in standalone script files (.script)."""

    DESCRIPTION = "Detects and removes dead code from standalone script files"
    SEVERITY = "ADVICE"
    DETECTOR = ScriptDeadCodeDetector

    def __init__(self, config: Dict[str, Any] = None, context=None):
        """Initialize the rule."""
        self.config = config or {}

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def analyze(self, context):
        """Analyze standalone script files for dead code."""
        # This rule only analyzes standalone script files, not PMD/POD embedded scripts
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model, context)

    def _analyze_script_file(self, script_model, context):
        """Analyze a single script file for dead code."""
        try:
            ast = self._parse_script_content(script_model.source, context)
            if not ast:
                return
            
            # Create detector with configuration
            detector = self.DETECTOR(script_model.file_path, 1, self.config)
            
            # Use detector to find violations
            violations = detector.detect(ast, "script")
            
            # Convert violations to findings
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=script_model.file_path
                )
                
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")