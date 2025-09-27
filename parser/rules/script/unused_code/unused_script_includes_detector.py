"""Detector for unused script includes in PMD files."""

from typing import Any, List, Set
from ...script.shared import ScriptDetector, Violation
from ...script.shared.ast_utils import get_line_number


class UnusedScriptIncludesDetector(ScriptDetector):
    """Detects unused script includes in PMD files."""

    def __init__(self, file_path: str = "", line_offset: int = 1, included_scripts: Set[str] = None, script_calls: Set[str] = None):
        """Initialize detector with file context and script registry."""
        super().__init__(file_path, line_offset)
        self.included_scripts = included_scripts or set()
        self.script_calls = script_calls or set()

    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """
        Analyze AST and return list of unused script include violations.
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Find unused script includes
        unused_scripts = self.included_scripts - self.script_calls
        
        for script_name in unused_scripts:
            violations.append(Violation(
                message=f"Script file '{script_name}' is included but never used. Consider removing from include array or add calls like '{script_name}.functionName()'.",
                line=1,  # This will be overridden by the rule
                column=1,
                metadata={
                    'script_name': script_name
                }
            ))
        
        return violations

    def _get_script_prefix(self, script_file: str) -> str:
        """Extract script prefix from script file name."""
        if not script_file:
            return ""
        
        # Remove .js extension if present
        if script_file.endswith('.js'):
            script_file = script_file[:-3]
        
        # Return the base name
        return script_file
