"""
Rule to ensure endpoints do not use bestEffort.

Using bestEffort: true on endpoints can silently mask API failures, leading to data 
inconsistency and hard-to-debug issues.

This rule checks both inbound and outbound endpoints.
"""
from typing import Generator

from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class OnlyMaximumEffortRule(StructureRuleBase):
    """
    Ensures endpoints do not use bestEffort to prevent masked failures.
    
    This rule checks:
    - Inbound endpoints in PMD files
    - Outbound endpoints in PMD files
    - Endpoints in POD files
    """
    
    ID = "OnlyMaximumEffortRule"
    DESCRIPTION = "Ensures endpoints do not use bestEffort to prevent masked API failures"
    SEVERITY = "ACTION"
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for bestEffort on endpoints."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_best_effort(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_best_effort(endpoint, pmd_model, 'outbound', i)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for bestEffort on endpoints."""
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_best_effort(endpoint, pod_model, 'pod', i)
    
    def _check_endpoint_best_effort(self, endpoint, model, endpoint_type, index):
        """Check if an endpoint has bestEffort: true."""
        if not isinstance(endpoint, dict):
            return
        
        endpoint_name = endpoint.get('name', f'endpoint[{index}]')
        best_effort = endpoint.get('bestEffort')
        
        # Check if bestEffort is set to true (handle both boolean and string)
        if best_effort is True or (isinstance(best_effort, str) and best_effort.lower() == 'true'):
            line_number = self._get_endpoint_line_number(model, endpoint_name, endpoint_type)
            
            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' has bestEffort: true which can mask API failures. It is advised to avoid using bestEffort.",
                file_path=model.file_path,
                line=line_number
            )
    
    def _get_endpoint_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the endpoint."""
        if endpoint_name and hasattr(model, 'source_content'):
            # For PMD models, use the unified method
            if isinstance(model, PMDModel):
                return self.get_field_line_number(model, 'name', endpoint_name)
            elif isinstance(model, PodModel):
                return self.get_field_line_number(model, 'name', endpoint_name)
        return 1

