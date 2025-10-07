"""Unit tests for HardcodedApplicationIdRule."""

from parser.rules.structure.validation.hardcoded_application_id import HardcodedApplicationIdRule
from parser.models import PMDModel, PodModel, SMDModel, ProjectContext


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
