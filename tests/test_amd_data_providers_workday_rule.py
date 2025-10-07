#!/usr/bin/env python3
"""Unit tests for AMD dataProviders workday.com rule."""

import pytest
from parser.rules.structure.validation.amd_data_providers_workday import AMDDataProvidersWorkdayRule
from parser.rules.base import Finding
from parser.models import AMDModel, ProjectContext


class TestAMDDataProvidersWorkdayRule:
    """Test cases for AMD dataProviders workday.com rule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule = AMDDataProvidersWorkdayRule()

    def test_rule_metadata(self):
        """Test rule metadata."""
        assert self.rule.ID == "AMDDataProvidersWorkdayRule"
        assert self.rule.DESCRIPTION == "Ensures AMD dataProviders don't use hardcoded *.workday.com URLs"
        assert self.rule.SEVERITY == "ACTION"

    def test_valid_data_providers_with_api_gateway(self):
        """Test valid dataProviders using apiGatewayEndpoint."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[
                {
                    "key": "workday-app",
                    "value": "<% apiGatewayEndpoint + '/apps/' + site.applicationId + '/v1/' %>"
                },
                {
                    "key": "custom-api",
                    "value": "<% apiGatewayEndpoint + '/custom/v1/' %>"
                }
            ],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 0

    def test_invalid_data_providers_with_hardcoded_workday_com(self):
        """Test invalid dataProviders with hardcoded *.workday.com URLs."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[
                {
                    "key": "workday-common",
                    "value": "https://api.workday.com/common/v1/"
                },
                {
                    "key": "workday-hcm",
                    "value": "https://api.workday.com/hcm/v1/"
                }
            ],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 2
        
        # Check first finding
        assert findings[0].rule == self.rule
        assert findings[0].line == 1
        assert findings[0].file_path == "test.amd"
        assert "workday-common" in findings[0].message
        assert "https://api.workday.com/common/v1/" in findings[0].message
        
        # Check second finding
        assert findings[1].rule == self.rule
        assert findings[1].line == 1
        assert findings[1].file_path == "test.amd"
        assert "workday-hcm" in findings[1].message
        assert "https://api.workday.com/hcm/v1/" in findings[1].message

    def test_mixed_valid_and_invalid_data_providers(self):
        """Test mixed valid and invalid dataProviders."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[
                {
                    "key": "workday-app",
                    "value": "<% apiGatewayEndpoint + '/apps/' + site.applicationId + '/v1/' %>"
                },
                {
                    "key": "workday-common",
                    "value": "https://api.workday.com/common/v1/"
                }
            ],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 1
        
        assert findings[0].rule == self.rule
        assert findings[0].line == 1
        assert findings[0].file_path == "test.amd"
        assert "workday-common" in findings[0].message

    def test_no_data_providers(self):
        """Test AMD file with no dataProviders."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 0

    def test_empty_data_providers(self):
        """Test AMD file with empty dataProviders array."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 0

    def test_data_providers_with_non_workday_urls(self):
        """Test dataProviders with non-workday.com URLs."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[
                {
                    "key": "external-api",
                    "value": "https://api.example.com/v1/"
                },
                {
                    "key": "local-api",
                    "value": "http://localhost:3000/api/"
                }
            ],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 0

    def test_data_providers_with_different_workday_subdomains(self):
        """Test dataProviders with different *.workday.com subdomains."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[
                {
                    "key": "api-workday",
                    "value": "https://api.workday.com/common/v1/"
                },
                {
                    "key": "services-workday",
                    "value": "https://api.us.workday.com/hcm/v1/"
                }
            ],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 2
        
        for finding in findings:
            assert finding.rule == self.rule
            assert finding.line == 1
            assert finding.file_path == "test.amd"

    def test_finding_message_content(self):
        """Test that finding messages contain helpful information."""
        amd_model = AMDModel(
            routes={},
            dataProviders=[
                {
                    "key": "workday-common",
                    "value": "https://api.workday.com/common/v1/"
                }
            ],
            file_path="test.amd"
        )
        
        context = ProjectContext()
        findings = list(self.rule.visit_amd(amd_model, context))
        assert len(findings) == 1
        
        message = findings[0].message
        assert "workday-common" in message
        assert "https://api.workday.com/common/v1/" in message
        assert "apiGatewayEndpoint" in message
        assert "recommended" in message.lower() or "should" in message.lower() or "consider" in message.lower()