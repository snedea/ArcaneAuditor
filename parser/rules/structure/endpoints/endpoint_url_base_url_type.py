from ...base import Rule, Finding
from ...common import PMDLineUtils
from ....models import PMDModel, PodModel


class EndpointBaseUrlTypeRule(Rule):
    """Ensures endpoint URLs don't include hardcoded workday.com or apiGatewayEndpoint values."""
    
    DESCRIPTION = "Ensures endpoint URLs don't include hardcoded workday.com or apiGatewayEndpoint values"
    SEVERITY = "ADVICE"

    def analyze(self, context):
        """Main entry point - analyze all PMD models and POD models in the context."""
        # Analyze PMD models
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
        
        # Analyze POD models
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes endpoints for hardcoded URL violations."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_url(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_url(endpoint, pmd_model, 'outbound', i)

    def visit_pod(self, pod_model: PodModel):
        """Analyzes endpoints in POD seed configuration."""
        # Check POD endpoints for URL violations
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_url(endpoint, pod_model, 'pod', i)

    def _check_endpoint_url(self, endpoint, model, endpoint_type, index):
        """Check if an endpoint URL contains hardcoded values."""
        endpoint_name = endpoint.get('name')
        url = endpoint.get('url', '')
        base_url_type = endpoint.get('baseUrlType', '')
        
        if not url:
            return
        
        # Check for hardcoded workday.com or apiGatewayEndpoint
        hardcoded_patterns = ['workday.com', 'apigatewayendpoint']
        found_patterns = []
        
        for pattern in hardcoded_patterns:
            if pattern in url.lower():
                found_patterns.append(pattern)
        
        if found_patterns:
            line_number = self._get_endpoint_url_line_number(model, endpoint_name, endpoint_type)
            
            # Create helpful message with baseUrlType suggestion
            pattern_list = ', '.join(found_patterns)
            suggestion = ""
            if base_url_type:
                suggestion = f" (current baseUrlType: '{base_url_type}')"
            else:
                suggestion = " (consider adding baseUrlType like 'workday-common' or 'workday-app')"
            
            yield Finding(
                rule=self,
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' has URL containing hardcoded values: {pattern_list}. Use baseUrlType instead of hardcoded URLs{suggestion}.",
                line=line_number,
                file_path=model.file_path
            )

    def _get_endpoint_url_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the endpoint URL field."""
        if endpoint_name and isinstance(model, PMDModel):
            return self.get_field_after_entity_line_number(model, 'name', endpoint_name, 'url')
        return 1
