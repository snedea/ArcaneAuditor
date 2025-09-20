#!/usr/bin/env python3
"""
Tests for EndpointOnSendSelfDataRule.
"""

import pytest
from parser.rules.structure.endpoints.endpoint_on_send_self_data import EndpointOnSendSelfDataRule
from parser.models import ProjectContext, PMDModel


class TestEndpointOnSendSelfDataRule:
    """Test cases for EndpointOnSendSelfDataRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointOnSendSelfDataRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly defined."""
        assert self.rule.DESCRIPTION == "Ensures outbound endpoints don't use anti-pattern 'self.data = {:}' in onSend scripts"
        assert self.rule.SEVERITY == "WARNING"
    
    def test_outbound_endpoint_with_anti_pattern(self):
        """Test that outbound endpoints with self.data anti-pattern are flagged."""
        source_content = """{
  "id": "test-page",
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      self.data = {:};
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content=source_content,
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      self.data = {:};\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find the anti-pattern violation
        assert len(findings) == 1
        assert "SendData" in findings[0].message
        assert "anti-pattern" in findings[0].message
        assert "self.data = {:}" in findings[0].message
    
    def test_outbound_endpoint_without_anti_pattern(self):
        """Test that outbound endpoints without anti-pattern are not flagged."""
        source_content = """{
  "id": "test-page",
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      return responseData;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content=source_content,
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      return responseData;\n    %>"
            }]
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_inbound_endpoint_with_anti_pattern_not_flagged(self):
        """Test that inbound endpoints with self.data pattern are NOT flagged (rule only applies to outbound)."""
        source_content = """{
  "id": "test-page",
  "inboundEndpoints": [{
    "name": "ReceiveData",
    "onSend": "<%
      self.data = {:};
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content=source_content,
            inboundEndpoints=[{
                "name": "ReceiveData",
                "onSend": "<%\n      self.data = {:};\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - rule only applies to outbound endpoints
        assert len(findings) == 0
    
    def test_mixed_endpoints_only_outbound_flagged(self):
        """Test that only outbound endpoints are checked, not inbound."""
        source_content = """{
  "id": "test-page",
  "inboundEndpoints": [{
    "name": "ReceiveData",
    "onSend": "<%
      self.data = {:};
      return self.data;
    %>"
  }],
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      self.data = {:};
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content=source_content,
            inboundEndpoints=[{
                "name": "ReceiveData",
                "onSend": "<%\n      self.data = {:};\n      return self.data;\n    %>"
            }],
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      self.data = {:};\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should only flag the outbound endpoint, not the inbound
        assert len(findings) == 1
        assert "SendData" in findings[0].message
        assert "outbound" in findings[0].message.lower()
    
    def test_no_endpoints(self):
        """Test PMD with no endpoints."""
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"id": "test-page"}'
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_outbound_endpoint_without_on_send(self):
        """Test outbound endpoint without onSend script."""
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"id": "test-page"}',
            outboundEndpoints=[{
                "name": "SendData",
                "url": "/api/send"
            }]
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations (no onSend to check)
        assert len(findings) == 0


if __name__ == "__main__":
    pytest.main([__file__])
