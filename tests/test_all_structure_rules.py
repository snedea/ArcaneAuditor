"""
Comprehensive unit tests for all PMD Structure Rules.
"""
import pytest
from unittest.mock import Mock, patch
from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule
from parser.rules.structure.widgets.widget_id_lower_camel_case import WidgetIdLowerCamelCaseRule
from parser.rules.structure.endpoints.endpoint_name_lower_camel_case import EndpointNameLowerCamelCaseRule
from parser.rules.structure.endpoints.endpoint_on_send_self_data import EndpointOnSendSelfDataRule
from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import EndpointFailOnStatusCodesRule
from parser.rules.structure.endpoints.endpoint_url_base_url_type import EndpointUrlBaseUrlTypeRule
from parser.rules.structure.validation.footer_pod_required import FooterPodRequiredRule
from parser.rules.structure.validation.string_boolean import StringBooleanRule
from parser.rules.base import Finding
from parser.models import ProjectContext, PMDModel, PMDPresentation


class TestWidgetIdRequiredRule:
    """Test cases for WidgetIdRequiredRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = WidgetIdRequiredRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "WARNING"
        assert "widget" in self.rule.DESCRIPTION.lower()


class TestWidgetIdLowerCamelCaseRule:
    """Test cases for WidgetIdLowerCamelCaseRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = WidgetIdLowerCamelCaseRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "WidgetIdLowerCamelCaseRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "WARNING"
        assert "widget" in self.rule.DESCRIPTION.lower()


class TestEndpointNameLowerCamelCaseRule:
    """Test cases for EndpointNameLowerCamelCaseRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointNameLowerCamelCaseRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "EndpointNameLowerCamelCaseRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "WARNING"
        assert "endpoint" in self.rule.DESCRIPTION.lower()


class TestEndpointOnSendSelfDataRule:
    """Test cases for EndpointOnSendSelfDataRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointOnSendSelfDataRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "WARNING"
        assert "self.data" in self.rule.DESCRIPTION.lower()


class TestEndpointFailOnStatusCodesRule:
    """Test cases for EndpointFailOnStatusCodesRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointFailOnStatusCodesRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "WARNING"
        assert "status" in self.rule.DESCRIPTION.lower()


class TestEndpointUrlBaseUrlTypeRule:
    """Test cases for EndpointUrlBaseUrlTypeRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointUrlBaseUrlTypeRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "WARNING"
        assert "url" in self.rule.DESCRIPTION.lower()


class TestFooterPodRequiredRule:
    """Test cases for FooterPodRequiredRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = FooterPodRequiredRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "WARNING"
        assert "footer" in self.rule.DESCRIPTION.lower()


class TestStringBooleanRule:
    """Test cases for StringBooleanRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = StringBooleanRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "WARNING"
        assert "string" in self.rule.DESCRIPTION.lower()


class TestAllStructureRulesIntegration:
    """Integration tests for all structure rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = ProjectContext()
        
        # Create a PMD model with various structure violations
        self.pmd_model = PMDModel(
            pageId="test-page",
            presentation=PMDPresentation(
                body={"children": [{"type": "text", "value": "test"}]}
            ),
            inboundEndpoints=[{"name": "GetData", "url": "test"}],
            outboundEndpoints=[{"name": "PostData", "url": "test"}],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = self.pmd_model
    
    def test_all_rules_can_be_instantiated(self):
        """Test that all structure rules can be instantiated."""
        rules = [
            WidgetIdRequiredRule(),
            WidgetIdLowerCamelCaseRule(),
            EndpointNameLowerCamelCaseRule(),
            EndpointOnSendSelfDataRule(),
            EndpointFailOnStatusCodesRule(),
            EndpointUrlBaseUrlTypeRule(),
            FooterPodRequiredRule(),
            StringBooleanRule(),
        ]
        
        # Test that all rules have required attributes
        for rule in rules:
            assert hasattr(rule, 'ID')
            assert hasattr(rule, 'DESCRIPTION')
            assert hasattr(rule, 'SEVERITY')
            assert hasattr(rule, 'analyze')
            # ID is now either RULE000 (base class) or class name (ValidationRule)
            assert rule.ID in ('RULE000', 'WidgetIdLowerCamelCaseRule', 'EndpointNameLowerCamelCaseRule')
    
    def test_all_rules_analyze_method(self):
        """Test that all rules can analyze without errors."""
        rules = [
            WidgetIdRequiredRule(),
            WidgetIdLowerCamelCaseRule(),
            EndpointNameLowerCamelCaseRule(),
            EndpointOnSendSelfDataRule(),
            EndpointFailOnStatusCodesRule(),
            EndpointUrlBaseUrlTypeRule(),
            FooterPodRequiredRule(),
            StringBooleanRule(),
        ]
        
        # Test that all rules can analyze without throwing exceptions
        for rule in rules:
            try:
                findings = list(rule.analyze(self.context))
                # Should return a list of Finding objects or empty list
                assert isinstance(findings, list)
                for finding in findings:
                    assert isinstance(finding, Finding)
            except Exception as e:
                pytest.fail(f"Rule {rule.ID} failed to analyze: {e}")
