#!/usr/bin/env python3
"""Unit tests for EndpointNameLowerCamelCaseRule."""

import pytest
from parser.rules.structure.endpoints.endpoint_name_lower_camel_case import EndpointNameLowerCamelCaseRule
from parser.models import ProjectContext


class TestEndpointNameLowerCamelCaseRule:
    """Test cases for EndpointNameLowerCamelCaseRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointNameLowerCamelCaseRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "EndpointNameLowerCamelCaseRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "ADVICE"
        assert "endpoint" in self.rule.DESCRIPTION.lower()
    
    def test_snake_case_endpoint_flagged(self):
        """Test that snake_case endpoint names are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "get_user_data",
                "url": "/users"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "get_user_data" in findings[0].message
    
    def test_pascal_case_endpoint_flagged(self):
        """Test that PascalCase endpoint names are flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "GetUserData",
                "url": "/users"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert "GetUserData" in findings[0].message
    
    def test_lower_camel_case_endpoint_not_flagged(self):
        """Test that lowerCamelCase endpoint names are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            inboundEndpoints=[{
                "name": "getUserData",
                "url": "/users"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
