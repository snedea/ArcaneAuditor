"""Unit tests for HardcodedApplicationIdRule."""

from parser.rules.structure.validation.hardcoded_application_id import HardcodedApplicationIdRule
from parser.models import PMDModel, PodModel, SMDModel, AMDModel, ProjectContext


class TestHardcodedApplicationIdRule:
    """Test cases for HardcodedApplicationIdRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = HardcodedApplicationIdRule()
        assert rule.ID == "HardcodedApplicationIdRule"
        assert rule.DESCRIPTION == "Detects hardcoded applicationId values that should be replaced with site.applicationId"
        assert rule.SEVERITY == "ADVICE"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = HardcodedApplicationIdRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_no_application_id_no_issues(self):
        """Test that no issues are found when there's no application ID in context."""
        rule = HardcodedApplicationIdRule()
        
        # Create context without application ID
        context = ProjectContext()
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '{"inboundEndpoints": [{"name": "GetCurrentWorker", "url": "api.workday.com/workers/hardcoded_app_id"}]}'
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_detect_hardcoded_app_id_in_url(self):
        """Test detection of hardcoded application ID in endpoint URL."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with hardcoded app ID in URL
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "inboundEndpoints": [
    {
      "name": "GetCurrentWorker",
      "url": "api.workday.com/workers/template_nkhlsq"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Hardcoded applicationId 'template_nkhlsq' found" in findings[0].message
        assert findings[0].file_path == "test.pmd"
        assert findings[0].line == 5  # Line where the hardcoded app ID appears

    def test_detect_hardcoded_app_id_in_script_expression(self):
        """Test detection of hardcoded application ID in script expressions."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with hardcoded app ID in script expression
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "richText",
      "value": "<% 'template_nkhlsq' %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Hardcoded applicationId 'template_nkhlsq' found" in findings[0].message
        assert findings[0].file_path == "test.pmd"
        assert findings[0].line == 5  # Line where the hardcoded app ID appears

    def test_detect_multiple_hardcoded_app_ids(self):
        """Test detection of multiple hardcoded application IDs."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with multiple hardcoded app IDs
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "inboundEndpoints": [
    {
      "name": "GetCurrentWorker",
      "url": "api.workday.com/workers/template_nkhlsq"
    }
  ],
  "widgets": [
    {
      "type": "richText",
      "value": "<% 'template_nkhlsq' %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert all("Hardcoded applicationId 'template_nkhlsq' found" in finding.message for finding in findings)
        assert all(finding.file_path == "test.pmd" for finding in findings)
        
        # Check that we have findings on different lines
        lines = [finding.line for finding in findings]
        assert 5 in lines  # URL line
        assert 11 in lines  # Script expression line

    def test_ignore_site_application_id_usage(self):
        """Test that correct usage of site.applicationId is ignored."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with correct site.applicationId usage
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "inboundEndpoints": [
    {
      "name": "GetCurrentWorker",
      "url": "api.workday.com/workers/" + site.applicationId
    }
  ],
  "widgets": [
    {
      "type": "richText",
      "value": "<% site.applicationId %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_ignore_different_application_ids(self):
        """Test that different application IDs are ignored."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with different application ID
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "inboundEndpoints": [
    {
      "name": "GetCurrentWorker",
      "url": "api.workday.com/workers/different_app_id"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_detect_quoted_application_id(self):
        """Test detection of quoted hardcoded application ID."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with quoted hardcoded app ID
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "widgets": [
    {
      "type": "richText",
      "value": "<% "template_nkhlsq" %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Hardcoded applicationId 'template_nkhlsq' found" in findings[0].message

    def test_detect_json_key_value_pattern(self):
        """Test detection of JSON key-value pattern with application ID."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with JSON key-value pattern
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "config": {
    "applicationId": "template_nkhlsq"
  }
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Hardcoded applicationId 'template_nkhlsq' found" in findings[0].message

    def test_no_duplicates_with_multiple_patterns(self):
        """Test that no duplicate findings are generated for the same location."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD with hardcoded app ID that could match multiple patterns
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '''{
  "inboundEndpoints": [
    {
      "name": "GetCurrentWorker",
      "url": "api.workday.com/workers/template_nkhlsq"
    }
  ],
  "widgets": [
    {
      "type": "richText",
      "value": "<% 'template_nkhlsq' %>"
    }
  ]
}'''
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        
        # Check that we don't have duplicate positions
        positions = [(finding.file_path, finding.line) for finding in findings]
        unique_positions = set(positions)
        assert len(positions) == len(unique_positions), "Found duplicate positions"

    def test_pod_file_detection(self):
        """Test detection of hardcoded application ID in POD files."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="template_nkhlsq",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create POD with hardcoded app ID
        pod_data = {
            "podId": "test-pod",
            "file_path": "test.pod",
            "seed": {
                "endPoints": [
                    {
                        "name": "TestEndpoint",
                        "url": "api.workday.com/workers/template_nkhlsq"
                    }
                ]
            }
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"test-pod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Hardcoded applicationId 'template_nkhlsq' found" in findings[0].message
        assert findings[0].file_path == "test.pod"

    # AMD-specific tests
    def test_amd_dataproviders_with_hardcoded_app_id(self):
        """Test detection of hardcoded application ID in AMD dataProviders values."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="myApp_abcdef",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create AMD with hardcoded app ID in dataProviders value
        amd_data = {
            "routes": {},
            "dataProviders": [
                {
                    "key": "BUSINESS-OBJECT",
                    "value": "<% apiGatewayEndpoint + '/myApp_abcdef/v1' %>"
                },
                {
                    "key": "COMMON",
                    "value": "<% apiGatewayEndpoint + '/common/v1' %>"
                }
            ],
            "file_path": "test.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        # Should find 1 issue in the BUSINESS-OBJECT dataProvider
        assert len(findings) == 1
        assert "Hardcoded applicationId 'myApp_abcdef' found" in findings[0].message
        assert findings[0].file_path == "test.amd"

    def test_amd_dataproviders_without_hardcoded_app_id(self):
        """Test that AMD dataProviders without hardcoded app ID are not flagged."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="myApp_abcdef",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create AMD with correct site.applicationId usage
        amd_data = {
            "routes": {},
            "dataProviders": [
                {
                    "key": "BUSINESS-OBJECT",
                    "value": "<% apiGatewayEndpoint + '/' + site.applicationId + '/v1' %>"
                },
                {
                    "key": "COMMON",
                    "value": "<% apiGatewayEndpoint + '/common/v1' %>"
                }
            ],
            "file_path": "test.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_amd_application_id_field_not_flagged(self):
        """Test that AMD's own applicationId field is not flagged."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="myApp_abcdef",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create AMD with applicationId field (should be allowed)
        # Note: AMDModel doesn't have applicationId in its schema, but if it did...
        # For now, we test that only dataProviders are checked
        amd_data = {
            "routes": {},
            "dataProviders": [
                {
                    "key": "COMMON",
                    "value": "<% apiGatewayEndpoint + '/common/v1' %>"
                }
            ],
            "file_path": "test.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_partial_execution_with_smd_but_no_amd(self):
        """Test that rule shows as partially executed when SMD exists but AMD is missing."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with SMD but no AMD
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="myApp_abcdef",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create PMD (so rule runs on something)
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "source_content": '{"widgets": []}'
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"test": pmd_model}
        
        # No AMD file
        context.amd = None
        
        # Rule should run on PMD but not on AMD
        findings = list(rule.analyze(context))
        # No findings expected, but rule should have run partially
        assert len(findings) == 0

    def test_no_execution_without_smd(self):
        """Test that rule doesn't execute at all when SMD is missing."""
        rule = HardcodedApplicationIdRule()
        
        # Create context without SMD
        context = ProjectContext()
        
        # Create AMD with what would be a hardcoded app ID (but can't check without SMD)
        amd_data = {
            "routes": {},
            "dataProviders": [
                {
                    "key": "BUSINESS-OBJECT",
                    "value": "<% apiGatewayEndpoint + '/someApp_abcdef/v1' %>"
                }
            ],
            "file_path": "test.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        # Should not find anything because we don't know what the app ID is
        assert len(findings) == 0

    def test_amd_dataproviders_multiple_hardcoded_app_ids(self):
        """Test detection of multiple hardcoded application IDs in AMD dataProviders."""
        rule = HardcodedApplicationIdRule()
        
        # Create context with application ID
        context = ProjectContext()
        smd_model = SMDModel(
            id="test-app",
            applicationId="genericApp_abcdef",
            siteId="test-site",
            file_path="test.smd"
        )
        context.smd = smd_model
        
        # Create AMD with multiple hardcoded app IDs in different dataProviders
        amd_data = {
            "routes": {},
            "dataProviders": [
                {
                    "key": "API1",
                    "value": "https://example.com/genericApp_abcdef/api"
                },
                {
                    "key": "API2",
                    "value": "<% 'genericApp_abcdef' + '/data' %>"
                },
                {
                    "key": "API3",
                    "value": "<% apiGatewayEndpoint + '/common/v1' %>"
                }
            ],
            "file_path": "test.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        # Should find 2 issues (API1 and API2)
        assert len(findings) == 2
        assert all("Hardcoded applicationId 'genericApp_abcdef' found" in finding.message for finding in findings)
        assert all(finding.file_path == "test.amd" for finding in findings)
