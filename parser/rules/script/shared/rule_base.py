"""Base rule class for script analysis rules."""

from abc import ABC, abstractmethod
from typing import Any, Generator, List, Tuple
from ...base import Rule, Finding
from ....models import PMDModel, PodModel, ScriptModel
from .violation import Violation
from .detector import ScriptDetector


class ScriptRuleBase(Rule, ABC):
    """Base class for script analysis rules with unified structure."""
    
    # Subclasses must define these
    DETECTOR: type[ScriptDetector]
    
    @abstractmethod
    def get_description(self) -> str:
        """Get rule description - must be implemented by subclasses."""
        pass
    
    def analyze(self, context) -> Generator[Finding, None, None]:
        """Main analysis entry point."""
        # Analyze PMD files
        for pmd in context.pmds.values():
            yield from self._analyze_pmd(pmd, context)
        
        # Analyze POD files
        for pod in context.pods.values():
            yield from self._analyze_pod(pod, context)
        
        # Analyze script files
        for script in context.scripts.values():
            yield from self._analyze_script(script, context)
    
    def _analyze_pmd(self, pmd_model: PMDModel, context) -> Generator[Finding, None, None]:
        """Analyze PMD file for script fields."""
        script_fields = self.find_script_fields(pmd_model, context)
        yield from self._analyze_fields(pmd_model, script_fields, context)
    
    def _analyze_pod(self, pod_model: PodModel, context=None) -> Generator[Finding, None, None]:
        """Analyze POD file for script fields."""
        script_fields = self.find_pod_script_fields(pod_model)
        yield from self._analyze_fields(pod_model, script_fields, context)
    
    def _analyze_script(self, script_model: ScriptModel, context=None) -> Generator[Finding, None, None]:
        """Analyze standalone script file."""
        try:
            yield from self._check(
                script_model.source, 
                "script", 
                script_model.file_path, 
                1,
                context
            )
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")
    
    def _analyze_fields(self, model, script_fields: List[Tuple[str, str, str, int]], context=None) -> Generator[Finding, None, None]:
        """Analyze script fields from a model."""
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                yield from self._check(field_value, field_name, model.file_path, line_offset, context)
    
    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector."""
        # Parse the script content with context for caching
        ast = self._parse_script_content(script_content, context)
        if not ast:
            return
        
        # Use detector to find violations
        detector = self.DETECTOR(file_path, line_offset)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        # Handle both List[Violation] and Generator[Violation, None, None]
        if hasattr(violations, '__iter__') and not isinstance(violations, str):
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    column=violation.column,
                    file_path=file_path
                )
