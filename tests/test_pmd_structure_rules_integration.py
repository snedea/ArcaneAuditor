"""
Integration tests for PMD Structure Rules with real PMD files.
"""
import pytest
from parser.rules.pmd_structure_rules import (
    WidgetIdRequiredRule,EndpointStructureRule,EndpointNamingConventionRule
)
from parser.rules.base import Finding
from parser.models import ProjectContext, PMDModel, PMDPresentation, PMDIncludes


class TestPMDStructureRulesIntegration:
    """Integration tests for PMD Structure Rules with real PMD content."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = ProjectContext()
        
        # Create PMD model based on sample.pmd structure
        self.sample_pmd = PMDModel(
            pageId="sample",
            securityDomains=[],
            inboundEndpoints=[
                {
                    "allowEmptyValue": True,
                    "name": "getCurrentWorker",
                    "baseUrlType": "workday-common",
                    "url": "/workers/me",
                    "failOnStatusCodes": [
                        {"code": "400"},
                        {"code": "403"}
                    ]
                }
            ],
            outboundEndpoints=[
                {
                    "name": "postModelData",
                    "baseUrlType": "workday-app",
                    "url": "/someModel",
                    "failOnStatusCodes": [
                        {"code": "400"},
                        {"code": "403"}
                    ]
                }
            ],
            presentation=PMDPresentation(body=
                # Body widget (text)
                {
                    "type": "section",
                    "children": [
                        {
                            "type": "text",
                            "id": "hello",
                            "label": "Hello World!",
                            "value": "Welcome from Workday!"
                        },
                        {
                            "type": "text",
                            "label": "Goodbye World!",
                            "value": "Goodbye from Workday!"
                        }
                    ]
                }
            ),
            onLoad="<% pageVariables.isGood = true; %>",
            onSubmit="<%\n                  if(!pageVariables.isGood){\n                      textWidget.setError('Not good!')\n                  }\n                 %>",
            script="<%\n                const myFunc = function(){\n                    return true;\n                }\n               %>",
            includes=PMDIncludes(scripts=["util.script"]),
            file_path="sample_extend_code/presentation/sample.pmd"
        )
        
        # Add sample PMD to context
        self.context.pmds["sample"] = self.sample_pmd
        
        # Add referenced script to context
        self.context.scripts["util.script"] = None  # Mock script exists
    
    def test_sample_pmd_widget_id_validation(self):
        """Test widget ID validation against sample.pmd."""
        rule = WidgetIdRequiredRule()
        findings = list(rule.analyze(self.context))
        
        # Should find 1 issue. Goodbye World! widget is missing an ID.
        assert len(findings) == 1
        finding = findings[0]
        assert "Widget of type 'text' is missing required 'id' field" in finding.message
        assert finding.file_path == "sample_extend_code/presentation/sample.pmd"
    
    def test_sample_pmd_endpoint_naming_convention(self):
        """Test endpoint naming convention against sample.pmd."""
        rule = EndpointNamingConventionRule()
        findings = list(rule.analyze(self.context))
        
        # Sample PMD has valid endpoint names: "getCurrentWorker" and "postModelData"
        assert len(findings) == 0
    
    def test_comprehensive_sample_pmd_analysis(self):
        """Test all structural rules against sample.pmd."""
        rules = [
            WidgetIdRequiredRule(),
            EndpointStructureRule(),
            EndpointNamingConventionRule()
        ]
        
        all_findings = []
        for rule in rules:
            findings = list(rule.analyze(self.context))
            all_findings.extend(findings)
        
        # Should only find 1 issue: missing ID on richText widget
        assert len(all_findings) == 1
        finding = all_findings[0]
        assert finding.rule_id == "PMD_STRUCT001"
        assert "text" in finding.message


class TestPMDStructureRulesWithIssues:
    """Integration tests for PMD Structure Rules with known issues."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = ProjectContext()

    def test_pmd_with_endpoint_naming_issues(self):
        """Test PMD with endpoint naming convention violations."""
        naming_issues_pmd = PMDModel(
            pageId="naming-issues",
            inboundEndpoints=[
                {"name": "GetUserData", "url": "/api/user"},      # Pascal case
                {"name": "get_user_data", "url": "/api/user2"},   # Snake case
                {"name": "getuserdata", "url": "/api/user3"},     # All lowercase
                {"name": "getUserData", "url": "/api/user4"}     # Valid
            ],
            outboundEndpoints=[
                {"name": "PostModelData", "url": "/api/model"},   # Pascal case
                {"name": "post_model_data", "url": "/api/model2"}, # Snake case
                {"name": "postModelData", "url": "/api/model3"}   # Valid
            ],
            file_path="naming-issues.pmd"
        )
        
        self.context.pmds["naming-issues"] = naming_issues_pmd
        
        rule = EndpointNamingConventionRule()
        findings = list(rule.analyze(self.context))
        
        # Should find 5 issues: 3 inbound + 2 outbound naming violations
        assert len(findings) == 5
        assert all("should follow lower camel case convention" in finding.message for finding in findings)
        
        # Check that we have findings for both inbound and outbound endpoints
        inbound_findings = [f for f in findings if "Inbound" in f.message]
        outbound_findings = [f for f in findings if "Outbound" in f.message]
        
        assert len(inbound_findings) == 3
        assert len(outbound_findings) == 2


if __name__ == "__main__":
    pytest.main([__file__])
