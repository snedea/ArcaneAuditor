#!/usr/bin/env python3
"""
Tests for ScriptOnSendSelfDataRule.
"""

import pytest
from parser.rules.script.logic.on_send_self_data import ScriptOnSendSelfDataRule
from parser.models import ProjectContext, PMDModel


class TestEndpointOnSendSelfDataRule:
    """Test cases for ScriptOnSendSelfDataRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptOnSendSelfDataRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly defined."""
        assert self.rule.DESCRIPTION == "Detects anti-pattern 'self.data = {:}' in outbound endpoint onSend scripts"
        assert self.rule.SEVERITY == "ADVICE"
    
    def test_outbound_endpoint_with_anti_pattern(self):
        """Test that outbound endpoints with self.data anti-pattern are flagged."""
        source_content = """{
  "id": "testPage",
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      self.data = {:};
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      self.data = {:};\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find the anti-pattern violation
        assert len(findings) == 1
        assert "Outbound endpoint 'SendData'" in findings[0].message
        assert "anti-pattern" in findings[0].message
        assert "self.data = {:}" in findings[0].message
    
    def test_outbound_endpoint_without_anti_pattern(self):
        """Test that outbound endpoints without anti-pattern are not flagged."""
        source_content = """{
  "id": "testPage",
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      return responseData;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      return responseData;\n    %>"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_inbound_endpoint_with_anti_pattern_not_flagged(self):
        """Test that inbound endpoints with self.data pattern are NOT flagged (rule only applies to outbound)."""
        source_content = """{
  "id": "testPage",
  "inboundEndpoints": [{
    "name": "ReceiveData",
    "onSend": "<%
      self.data = {:};
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            inboundEndpoints=[{
                "name": "ReceiveData",
                "onSend": "<%\n      self.data = {:};\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - rule only applies to outbound endpoints
        assert len(findings) == 0
    
    def test_mixed_endpoints_only_outbound_flagged(self):
        """Test that only outbound endpoints are checked, not inbound."""
        source_content = """{
  "id": "testPage",
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
            pageId="testPage",
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
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should only flag the outbound endpoint, not the inbound
        assert len(findings) == 1
        assert "Outbound endpoint 'SendData'" in findings[0].message
        assert "anti-pattern" in findings[0].message
    
    def test_no_endpoints(self):
        """Test PMD with no endpoints."""
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "test-page"}'
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_outbound_endpoint_without_on_send(self):
        """Test outbound endpoint without onSend script."""
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"id": "testPage"}',
            outboundEndpoints=[{
                "name": "SendData",
                "url": "/api/send"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations (no onSend to check)
        assert len(findings) == 0
    
    def test_anti_pattern_in_single_line_comment_not_flagged(self):
        """Test that anti-pattern in single-line comment (//) is NOT flagged."""
        source_content = """{
  "id": "testPage",
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      //self.data = {:};
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      //self.data = {:};\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should NOT flag commented code
        assert len(findings) == 0
    
    def test_anti_pattern_in_multi_line_comment_not_flagged(self):
        """Test that anti-pattern in multi-line comment (/* */) is NOT flagged."""
        source_content = """{
  "id": "testPage",
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      /*
      self.data = {:};
      */
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      /*\n      self.data = {:};\n      */\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should NOT flag commented code
        assert len(findings) == 0
    
    def test_anti_pattern_before_comment_is_flagged(self):
        """Test that anti-pattern before a comment on the same line IS flagged."""
        source_content = """{
  "id": "testPage",
  "outboundEndpoints": [{
    "name": "SendData",
    "onSend": "<%
      self.data = {:}; // This is the anti-pattern
      return self.data;
    %>"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            outboundEndpoints=[{
                "name": "SendData",
                "onSend": "<%\n      self.data = {:}; // This is the anti-pattern\n      return self.data;\n    %>"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should flag the anti-pattern since it appears before the comment
        assert len(findings) == 1
        assert "Outbound endpoint 'SendData'" in findings[0].message
        assert "anti-pattern" in findings[0].message


if __name__ == "__main__":
    pytest.main([__file__])
