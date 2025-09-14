from ...base import Rule, Finding
from ....models import PMDModel
from typing import Dict, Any, List


class EndpointOnSendSelfDataRule(Rule):
    """Validates that endpoints don't use the anti-pattern 'self.data = {:}' in onSend scripts."""
    
    DESCRIPTION = "Ensures endpoints don't use anti-pattern 'self.data = {:}' in onSend scripts"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes endpoints for anti-pattern usage."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_anti_pattern(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_anti_pattern(endpoint, pmd_model, 'outbound', i)

    def _check_endpoint_anti_pattern(self, endpoint, pmd_model, endpoint_type, index):
        """Check if an endpoint uses the anti-pattern in its onSend script."""
        on_send = endpoint.get('onSend', '')
        endpoint_name = endpoint.get('name', f'unnamed_{endpoint_type}_{index}')
        
        if on_send and 'self.data = {:}' in on_send:
            line_number = self._get_on_send_line_number(pmd_model, endpoint_name, endpoint_type)
            
            yield Finding(
                rule=self,
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' uses anti-pattern 'self.data = {{:}}' in onSend script. This pattern should be avoided.",
                line=line_number,
                column=1,
                file_path=pmd_model.file_path
            )

    def _get_on_send_line_number(self, pmd_model: PMDModel, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the onSend script containing the anti-pattern."""
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Look for the endpoint name first
            endpoint_line = -1
            for i, line in enumerate(lines):
                if f'"name": "{endpoint_name}"' in line or f'"name":"{endpoint_name}"' in line:
                    endpoint_line = i
                    break
            
            if endpoint_line >= 0:
                # Look for the onSend field after the endpoint name
                for i in range(endpoint_line, min(endpoint_line + 20, len(lines))):
                    if '"onSend"' in lines[i]:
                        # Look for the anti-pattern in the next few lines
                        for j in range(i, min(i + 10, len(lines))):
                            if 'self.data = {:}' in lines[j]:
                                return j + 1  # Convert to 1-based line numbering
            
            return endpoint_line + 1 if endpoint_line >= 0 else 1
            
        except Exception:
            return 1
