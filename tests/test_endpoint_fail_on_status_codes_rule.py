#!/usr/bin/env python3
"""Unit tests for EndpointFailOnStatusCodesRule."""

import pytest
from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import EndpointFailOnStatusCodesRule
from parser.models import ProjectContext


class TestEndpointFailOnStatusCodesRule:
    """Test cases for EndpointFailOnStatusCodesRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointFailOnStatusCodesRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ACTION"
        assert "status" in self.rule.DESCRIPTION.lower()
    
    def test_missing_fail_on_status_codes_flagged(self):
        """Test that endpoints without failOnStatusCodes are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "getUser",
                "url": "/users/me"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "failOnStatusCodes" in findings[0].message or "status" in findings[0].message.lower()
    
    def test_with_fail_on_status_codes_not_flagged(self):
        """Test that endpoints with failOnStatusCodes are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "getUser",
                "url": "/users/me",
                "failOnStatusCodes": [{"code": 400}, {"code": 403}]
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0
    
    def test_outbound_variables_with_variable_scope_skipped(self):
        """Test that outbound endpoints with variableScope are skipped (these are outboundVariables)."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            outboundEndpoints=[
                {
                    "name": "regularEndpoint",
                    "baseUrlType": "workday-app",
                    "url": "/api/test"
                    # No failOnStatusCodes - should trigger violation
                },
                {
                    "name": "outboundVariable",
                    "type": "outboundVariable",
                    "variableScope": "flow",
                    "values": [{"outboundPath": "test", "value": "test"}]
                    # No failOnStatusCodes - should NOT trigger violation due to variableScope
                }
            ]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should only find violation for regular endpoint, not outbound variable
        assert len(findings) == 1
        assert "regularEndpoint" in findings[0].message
        assert "outboundVariable" not in findings[0].message


if __name__ == '__main__':
    pytest.main([__file__])
