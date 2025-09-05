"""
Unit tests for PMD Structure Rules.
"""
import pytest
from parser.rules.pmd_structure_rules import (
    WidgetIdRequiredRule, WidgetTypeRequiredRule, ValidWidgetTypesRule,
    RequiredPageIdRule, PresentationStructureRule, EndpointStructureRule,
    ScriptStructureRule, IncludeValidationRule, EndpointNamingConventionRule
)
from parser.rules.base import Finding
from parser.models import ProjectContext, PMDModel, PMDPresentation, PMDIncludes


class TestWidgetIdRequiredRule:
    """Test cases for WidgetIdRequiredRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = WidgetIdRequiredRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "PMD_STRUCT001"
        assert self.rule.DESCRIPTION == "Ensures all widgets have an 'id' field set."
        assert self.rule.SEVERITY == "WARNING"
    
    def test_widget_with_id(self):
        """Test widget with valid ID."""
        pmd_model = PMDModel(
            pageId="test-page",
            presentation=PMDPresentation(
                body={"children": [{"type": "text", "id": "hello", "label": "Hello World!"}]}
            ),
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_widget_without_id(self):
        """Test widget without ID."""
        pmd_model = PMDModel(
            pageId="test-page",
            presentation=PMDPresentation(
                body={"children": [{"type": "text", "label": "Hello World!"}]}  # Missing 'id'
            ),
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "Widget of type 'text' is missing required 'id' field" in finding.message
        assert finding.file_path == "test.pmd"
    
    def test_multiple_widgets_mixed(self):
        """Test multiple widgets with mixed ID compliance."""
        pmd_model = PMDModel(
            pageId="test-page",
            presentation=PMDPresentation(
                body={"children": [
                    {"type": "text", "id": "hello", "label": "Hello"},  # Has ID
                    {"type": "button", "label": "Click me"},  # Missing ID
                    {"type": "input", "id": "userInput", "label": "Input"}  # Has ID
                ]}
            ),
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1  # Only the button is missing ID
        finding = findings[0]
        assert "Widget of type 'button' is missing required 'id' field" in finding.message


class TestPresentationStructureRule:
    """Test cases for PresentationStructureRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = PresentationStructureRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "PMD_STRUCT005"
        assert self.rule.DESCRIPTION == "Ensures PMD files have proper presentation structure."
        assert self.rule.SEVERITY == "WARNING"
    
    def test_valid_presentation(self):
        """Test PMD with valid presentation structure."""
        pmd_model = PMDModel(
            pageId="test-page",
            presentation=PMDPresentation(
                body={"children": [{"type": "text", "id": "hello"}]}
            ),
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_missing_presentation(self):
        """Test PMD without presentation section."""
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "PMD file is missing 'presentation' section" in finding.message


class TestEndpointStructureRule:
    """Test cases for EndpointStructureRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointStructureRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "PMD_STRUCT006"
        assert self.rule.DESCRIPTION == "Validates endpoint structure and required fields."
        assert self.rule.SEVERITY == "WARNING"
    
    def test_valid_endpoints(self):
        """Test PMD with valid endpoints."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "getData", "url": "/api/data"}
            ],
            outboundEndpoints=[
                {"name": "postData", "url": "/api/data"}
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_endpoint_missing_name(self):
        """Test endpoint missing name field."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"url": "/api/data"}  # Missing 'name'
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "Inbound endpoint is missing required 'name' field" in finding.message
    
    def test_endpoint_missing_url(self):
        """Test endpoint missing URL field."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "getData"}  # Missing 'url'
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "Inbound endpoint is missing required 'url' field" in finding.message
    
    def test_endpoint_invalid_url(self):
        """Test endpoint with invalid URL format."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "getData", "url": "api/data"}  # Missing leading '/'
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "Inbound endpoint URL should start with '/'" in finding.message


class TestScriptStructureRule:
    """Test cases for ScriptStructureRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptStructureRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "PMD_STRUCT007"
        assert self.rule.DESCRIPTION == "Validates script structure and syntax."
        assert self.rule.SEVERITY == "INFO"
    
    def test_valid_script(self):
        """Test PMD with valid script structure."""
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% pageVariables.isGood = true; %>",
            script="<% const x = 1; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_script_missing_opening_delimiter(self):
        """Test script missing opening delimiter."""
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="pageVariables.isGood = true; %>",  # Missing '<%'
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "onLoad script should start with '<%'" in finding.message
    
    def test_script_missing_closing_delimiter(self):
        """Test script missing closing delimiter."""
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% pageVariables.isGood = true;",  # Missing '%>'
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "onLoad script should end with '%>'" in finding.message
    
    def test_script_unbalanced_delimiters(self):
        """Test script with unbalanced delimiters."""
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% pageVariables.isGood = true; %> %>",  # Extra '%>'
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        finding = findings[0]
        assert "onLoad script has unbalanced delimiters" in finding.message


class TestIncludeValidationRule:
    """Test cases for IncludeValidationRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = IncludeValidationRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "PMD_STRUCT008"
        assert self.rule.DESCRIPTION == "Validates include references and file extensions."
        assert self.rule.SEVERITY == "WARNING"
    
    def test_valid_include(self):
        """Test PMD with valid include reference."""
        pmd_model = PMDModel(
            pageId="test-page",
            includes=PMDIncludes(scripts=["util.script"]),
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        self.context.scripts["util.script"] = None  # Mock script exists
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0


class TestEndpointNamingConventionRule:
    """Test cases for EndpointNamingConventionRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointNamingConventionRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "PMD_STRUCT009"
        assert self.rule.DESCRIPTION == "Ensures all endpoint names follow lower camel case convention."
        assert self.rule.SEVERITY == "WARNING"
    
    def test_valid_lower_camel_case_names(self):
        """Test endpoints with valid lower camel case names."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "getUserData", "url": "/api/user"},
                {"name": "postModelData", "url": "/api/model"},
                {"name": "fetchWorkerInfo", "url": "/api/worker"}
            ],
            outboundEndpoints=[
                {"name": "saveUserProfile", "url": "/api/profile"},
                {"name": "updateModelState", "url": "/api/state"}
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_invalid_pascal_case_names(self):
        """Test endpoints with Pascal case names (should fail)."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "GetUserData", "url": "/api/user"},  # Pascal case
                {"name": "PostModelData", "url": "/api/model"}  # Pascal case
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2
        assert all("should follow lower camel case convention" in finding.message for finding in findings)
    
    def test_invalid_snake_case_names(self):
        """Test endpoints with snake case names (should fail)."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "get_user_data", "url": "/api/user"},  # Snake case
                {"name": "post_model_data", "url": "/api/model"}  # Snake case
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2
        assert all("should follow lower camel case convention" in finding.message for finding in findings)
    
    def test_invalid_all_lowercase_names(self):
        """Test endpoints with all lowercase names (should fail)."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "getuserdata", "url": "/api/user"},  # All lowercase
                {"name": "postmodeldata", "url": "/api/model"}  # All lowercase
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2
        assert all("should follow lower camel case convention" in finding.message for finding in findings)
    
    def test_invalid_uppercase_names(self):
        """Test endpoints with all uppercase names (should fail)."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "GETUSERDATA", "url": "/api/user"},  # All uppercase
                {"name": "POSTMODELDATA", "url": "/api/model"}  # All uppercase
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2
        assert all("should follow lower camel case convention" in finding.message for finding in findings)
    
    def test_invalid_names_with_special_characters(self):
        """Test endpoints with special characters (should fail)."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "get-user-data", "url": "/api/user"},  # Hyphens
                {"name": "get.user.data", "url": "/api/model"},  # Dots
                {"name": "get user data", "url": "/api/data"}    # Spaces
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 3
        assert all("should follow lower camel case convention" in finding.message for finding in findings)
    
    def test_valid_names_with_numbers(self):
        """Test endpoints with valid names containing numbers."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "getUserData2", "url": "/api/user"},
                {"name": "postModelData2023", "url": "/api/model"},
                {"name": "fetchWorkerInfo1", "url": "/api/worker"}
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_mixed_valid_and_invalid_names(self):
        """Test endpoints with mixed valid and invalid names."""
        pmd_model = PMDModel(
            pageId="test-page",
            inboundEndpoints=[
                {"name": "getUserData", "url": "/api/user"},      # Valid
                {"name": "GetUserData", "url": "/api/user2"},     # Invalid (Pascal case)
                {"name": "postModelData", "url": "/api/model"},   # Valid
                {"name": "get_user_data", "url": "/api/user3"}   # Invalid (snake case)
            ],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2  # Only the invalid ones should be flagged
        assert all("should follow lower camel case convention" in finding.message for finding in findings)

if __name__ == "__main__":
    pytest.main([__file__])
