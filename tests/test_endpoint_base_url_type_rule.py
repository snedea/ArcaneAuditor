#!/usr/bin/env python3
"""Unit tests for EndpointBaseUrlTypeRule."""

import pytest
from parser.rules.structure.endpoints.endpoint_url_base_url_type import EndpointBaseUrlTypeRule
from parser.models import ProjectContext


class TestEndpointBaseUrlTypeRule:
    """Test cases for EndpointBaseUrlTypeRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointBaseUrlTypeRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "url" in self.rule.DESCRIPTION.lower()
    
    def test_hardcoded_workday_url_flagged(self):
        """Test that hardcoded workday.com URLs are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "getWorker",
                "url": "https://api.workday.com/common/v1/workers/me"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "workday.com" in findings[0].message or "baseUrlType" in findings[0].message
        assert "duplication" in findings[0].message.lower()
    
    def test_base_url_type_usage_not_flagged(self):
        """Test that endpoints using baseUrlType are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "getWorker",
                "url": "/workers/me",
                "baseUrlType": "workday-common"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0

    def test_api_gateway_endpoint_usage_flagged(self):
        """Test that endpoints using apiGatewayEndpoint directly are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "getWorker",
                "url": "<% apiGatewayEndpoint + '/common/v1/workers/me' %>"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "apiGatewayEndpoint" in findings[0].message or "baseUrlType" in findings[0].message
        assert "duplication" in findings[0].message.lower()


if __name__ == '__main__':
    pytest.main([__file__])
