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
    
    def _analyze_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD file - must be implemented by subclasses."""
        yield from self.visit_pmd(pmd_model, context)
    
    def _analyze_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD file - must be implemented by subclasses."""
        yield from self.visit_pod(pod_model, context)
    
    @abstractmethod
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit PMD model - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit POD model - must be implemented by subclasses."""
        pass
    
    def _create_finding(self, message: str, file_path: str, line: int = 1) -> Finding:
        """Create a finding with consistent formatting."""
        return Finding(
            rule=self,
            message=message,
            line=line,
            file_path=file_path
        )
