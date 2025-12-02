"""
Rule to detect isCollection: true on inbound endpoints.

Using isCollection: true on inbound endpoints can cause severe tenant-wide performance 
degradation. This should be avoided.

Note: Outbound endpoints are not checked as the performance impact is different.
"""
from typing import Generator

from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class NoIsCollectionOnEndpointsRule(StructureRuleBase):
    """
    Detects isCollection: true on inbound endpoints which can cause performance issues.
    
    This rule checks:
    - Inbound endpoints in PMD files
    - Endpoints in POD files (treated as inbound)
    
    Note: Outbound endpoints are not checked.
    """
    
    ID = "NoIsCollectionOnEndpointsRule"
    DESCRIPTION = "Detects isCollection: true on inbound endpoints which can cause tenant-wide performance issues"
    SEVERITY = "ACTION"
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for isCollection on inbound endpoints."""
        # Only check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_is_collection(endpoint, pmd_model, 'inbound', i)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for isCollection on endpoints."""
        # POD endpoints are treated as inbound-type
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_is_collection(endpoint, pod_model, 'pod', i)
    
    def _check_endpoint_is_collection(self, endpoint, model, endpoint_type, index):
        """Check if an endpoint has isCollection: true."""
        if not isinstance(endpoint, dict):
            return
        
        endpoint_name = endpoint.get('name', f'endpoint[{index}]')
        is_collection = endpoint.get('isCollection')
        
        # Check if isCollection is set to true (handle both boolean and string)
        if is_collection is True or (isinstance(is_collection, str) and is_collection.lower() == 'true'):
            line_number = self._get_endpoint_line_number(model, endpoint_name, endpoint_type)
            
            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' has isCollection: true which can cause tenant-wide performance issues. Remove this property or restructure the endpoint.",
                file_path=model.file_path,
                line=line_number
            )
    
    def _get_endpoint_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the isCollection field."""
        if hasattr(model, 'source_content'):
            # Use pattern search to find the isCollection field
            return self.find_pattern_line_number(model, '"isCollection": true')
        return 1

