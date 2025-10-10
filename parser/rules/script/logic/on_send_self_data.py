"""Script rule for detecting anti-pattern in onSend scripts."""

from typing import Generator, List, Tuple
from ...script.shared import ScriptRuleBase
from ...base import Finding
from ....models import PMDModel
from .on_send_self_data_detector import OnSendSelfDataDetector


class ScriptOnSendSelfDataRule(ScriptRuleBase):
    """Detects the anti-pattern 'self.data = {:}' in outbound endpoint onSend scripts."""

    DESCRIPTION = "Detects anti-pattern 'self.data = {:}' in outbound endpoint onSend scripts"
    SEVERITY = "ADVICE"
    DETECTOR = OnSendSelfDataDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _analyze_pmd(self, pmd_model: PMDModel, context) -> Generator[Finding, None, None]:
        """Analyze PMD file specifically for outbound endpoint onSend scripts."""
        # Only check outbound endpoints
        if not pmd_model.outboundEndpoints or not isinstance(pmd_model.outboundEndpoints, list):
            return
        
        for i, endpoint in enumerate(pmd_model.outboundEndpoints):
            if not isinstance(endpoint, dict):
                continue
            
            endpoint_name = endpoint.get('name', f'unnamed_outbound_{i}')
            on_send = endpoint.get('onSend', '')
            
            if not on_send or not on_send.strip():
                continue
            
            # Get line offset for the onSend field
            line_offset = self._get_on_send_line_offset(pmd_model, endpoint_name)
            
            # Check the onSend script using the detector
            findings = self._check(on_send, f"outbound endpoint '{endpoint_name}'", pmd_model.file_path, line_offset, context)
            
            # Add endpoint name to the finding messages
            for finding in findings:
                # Update the message to include endpoint name
                finding.message = f"Outbound endpoint '{endpoint_name}' uses anti-pattern 'self.data = {{:}}' in onSend script. This pattern should be avoided."
                yield finding
    
    def _get_on_send_line_offset(self, pmd_model: PMDModel, endpoint_name: str) -> int:
        """Get line offset for onSend field in the source."""
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
                        # Return the line after "onSend": where the script starts
                        return i + 2  # +1 for 0-based to 1-based, +1 for script start
            
            return 1
        except Exception:
            return 1

