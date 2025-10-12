"""Script descriptive parameter rule using unified architecture."""

from typing import Generator, Dict, List
from ...script.shared import ScriptRuleBase
from ...base import Finding
from .descriptive_parameters_detector import DescriptiveParameterDetector


class ScriptDescriptiveParameterRule(ScriptRuleBase):
    """Validates that function parameters use descriptive names when functions take function parameters."""

    DESCRIPTION = "Ensures function parameters use descriptive names when functions take function parameters (except 'a', 'b' for sort)"
    SEVERITY = "ADVICE"
    DETECTOR = DescriptiveParameterDetector

    # Expose constants for testing
    FUNCTIONAL_METHODS = {'map', 'filter', 'find', 'forEach', 'reduce', 'sort'}
    ALLOWED_SINGLE_LETTERS = set()  # Empty set - only 'a','b' are allowed for sort (handled separately)

    def __init__(self, config=None):
        """Initialize the rule with optional configuration."""
        super().__init__()
        if config:
            # Update functional methods if provided
            if 'additional_functional_methods' in config:
                self.FUNCTIONAL_METHODS = self.FUNCTIONAL_METHODS.union(config['additional_functional_methods'])
            
            # Update allowed single letters if provided
            if 'allowed_single_letters' in config:
                self.ALLOWED_SINGLE_LETTERS = set(config['allowed_single_letters'])

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector with rule-specific configuration."""
        # Parse the script content with context for caching
        ast = self._parse_script_content(script_content, context)
        if not ast:
            yield from []
            return
        
        # Create detector with rule-specific configuration
        detector = self.DETECTOR(file_path, line_offset, self.FUNCTIONAL_METHODS, self.ALLOWED_SINGLE_LETTERS)
        detector.set_original_content(script_content)
        
        # Use detector to find violations
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        # Handle both List[Violation] and Generator[Violation, None, None]
        if hasattr(violations, '__iter__') and not isinstance(violations, str):
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=file_path
                )