"""
Shared components for structure rules using unified architecture.

This module provides base classes and utilities for structure validation rules
that analyze PMD and POD files for structural compliance issues.
"""
from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Any, Optional
from ...base import Rule, Finding
from ....models import PMDModel, PodModel, ProjectContext


class StructureRuleBase(Rule, ABC):
    """Base class for structure analysis rules with unified structure."""
    
    @abstractmethod
    def get_description(self) -> str:
        """Get rule description - must be implemented by subclasses."""
        pass
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Main analysis entry point."""
        # Analyze PMD files
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd(pmd_model, context)
        
        # Analyze POD files
        for pod_model in context.pods.values():
            yield from self._analyze_pod(pod_model, context)
        
        # Analyze AMD file if present
        if context.amd:
            yield from self._analyze_amd(context.amd, context)
    
    def _analyze_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD file - must be implemented by subclasses."""
        yield from self.visit_pmd(pmd_model, context)
    
    def _analyze_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD file - must be implemented by subclasses."""
        yield from self.visit_pod(pod_model, context)
    
    def _analyze_amd(self, amd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze AMD file - can be overridden by subclasses."""
        yield from self.visit_amd(amd_model, context)
    
    @abstractmethod
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit PMD model - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit POD model - must be implemented by subclasses."""
        pass
    
    def visit_amd(self, amd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit AMD model - can be overridden by subclasses."""
        # Default implementation does nothing
        return
        yield  # This line is never reached, but makes it a generator
    
    def _create_finding(self, message: str, file_path: str, line: int = 1) -> Finding:
        """Create a finding with consistent formatting."""
        return Finding(
            rule=self,
            message=message,
            line=line,
            file_path=file_path
        )
    
    # Unified line calculation methods
    def get_field_line_number(self, model, field_name: str, field_value: str) -> int:
        """Get line number for a specific field with a specific value."""
        from ...common import PMDLineUtils
        return PMDLineUtils.find_field_line_number(model, field_name, field_value)
    
    def get_section_line_number(self, model, section_name: str) -> int:
        """Get line number for a specific section."""
        from ...common import PMDLineUtils
        return PMDLineUtils.find_section_line_number(model, section_name)
    
    def get_field_after_entity_line_number(self, model, entity_field: str, entity_value: str, target_field: str) -> int:
        """Get line number for a field that appears after a specific entity."""
        from ...common import PMDLineUtils
        return PMDLineUtils.find_field_after_entity(model, entity_field, entity_value, target_field)
    
    def find_pattern_line_number(self, model, pattern: str, case_sensitive: bool = False) -> int:
        """Find line number where a pattern appears in the source content."""
        if not hasattr(model, 'source_content') or not model.source_content:
            return 1
        
        try:
            lines = model.source_content.split('\n')
            for i, line in enumerate(lines):
                if case_sensitive:
                    if pattern in line:
                        return i + 1
                else:
                    if pattern.lower() in line.lower():
                        return i + 1
            return 1
        except Exception:
            return 1
    
    def get_line_from_text_position(self, text: str, position: int) -> int:
        """Get line number from a text position (character offset)."""
        if not text or position < 0:
            return 1
        try:
            return text[:position].count('\n') + 1
        except Exception:
            return 1