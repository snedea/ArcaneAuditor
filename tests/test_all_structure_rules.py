"""
Comprehensive unit tests for all PMD Structure Rules.
"""
import pytest
from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule
from parser.rules.structure.widgets.widget_id_lower_camel_case import WidgetIdLowerCamelCaseRule
from parser.rules.structure.endpoints.endpoint_name_lower_camel_case import EndpointNameLowerCamelCaseRule
from parser.rules.structure.endpoints.endpoint_on_send_self_data import EndpointOnSendSelfDataRule
from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import EndpointFailOnStatusCodesRule
from parser.rules.structure.endpoints.endpoint_url_base_url_type import EndpointBaseUrlTypeRule
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
        assert self.rule.SEVERITY == "ACTION"
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
        assert self.rule.SEVERITY == "ACTION"
        assert "widget" in self.rule.DESCRIPTION.lower()
    
    def test_script_syntax_detection(self):
        """Test detection of script syntax in widget IDs."""
        # Valid script syntax cases
        assert self.rule._is_script_syntax("<% 'myField' + value %>")
        assert self.rule._is_script_syntax("<% `question{{id}}`  %>")
        assert self.rule._is_script_syntax("<% someVariable %>")
        
        # Non-script cases
        assert not self.rule._is_script_syntax("myField")
        assert not self.rule._is_script_syntax("MyField")
        assert not self.rule._is_script_syntax("")
        assert not self.rule._is_script_syntax(None)
    
    def test_string_concatenation_extraction(self):
        """Test extraction of static parts from string concatenation patterns."""
        # Single string concatenation
        result = self.rule._extract_static_parts_from_script("<% 'myField' + value %>")
        assert result == ["myField"]
        
        # Double quotes
        result = self.rule._extract_static_parts_from_script('<% "myField" + value %>')
        assert result == ["myField"]
        
        # Multiple string literals
        result = self.rule._extract_static_parts_from_script("<% 'prefix' + variable + 'suffix' %>")
        assert result == ["prefix", "suffix"]
        
        # Mixed case strings
        result = self.rule._extract_static_parts_from_script("<% 'field' + var1 + 'Name' + var2 %>")
        assert result == ["field", "Name"]
        
        # Single string literal
        result = self.rule._extract_static_parts_from_script("<% 'field' %>")
        assert result == ["field"]
    
    def test_variable_starting_script_extraction(self):
        """Test extraction when script starts with a variable (should be ignored)."""
        # Script starting with variable - should return empty list (pass)
        result = self.rule._extract_static_parts_from_script("<% someVariable %>")
        assert result == []
        
        # Script starting with variable and concatenation - should ignore entire script
        result = self.rule._extract_static_parts_from_script("<% someVariable + 'suffix' %>")
        assert result == []  # Ignore entire script when starting with variable
        
        # Script starting with variable and multiple parts
        result = self.rule._extract_static_parts_from_script("<% someVariable + 'middle' + anotherVar %>")
        assert result == []  # Ignore entire script when starting with variable
        
        # Script with variable followed by assignment
        result = self.rule._extract_static_parts_from_script("<% myField = 'value' %>")
        assert result == []  # Ignore entire script when starting with variable
        
        # Script with just a variable (no quotes) - should be ignored
        result = self.rule._extract_static_parts_from_script("<% myField %>")
        assert result == []  # Variable - ignore for validation
    
    def test_backtick_template_extraction(self):
        """Test extraction of static parts from backtick template patterns."""
        # Backtick with template variables
        result = self.rule._extract_static_parts_from_script("<% `question{{id}}`  %>")
        assert result == ["question"]
        
        # Backtick with PascalCase
        result = self.rule._extract_static_parts_from_script("<% `Question{{id}}`  %>")
        assert result == ["Question"]
        
        # Backtick with no static prefix
        result = self.rule._extract_static_parts_from_script("<% `{{id}}`  %>")
        assert result == [""]
    
    def test_simple_static_text_extraction(self):
        """Test extraction of simple static text."""
        # This is actually a variable (no quotes) - should return empty list
        result = self.rule._extract_static_parts_from_script("<% someVariable %>")
        assert result == []
        
        # This is a string literal (with quotes) - should extract the string
        result = self.rule._extract_static_parts_from_script("<% 'someStaticText' %>")
        assert result == ["someStaticText"]
        
    
    def test_script_validation_valid_cases(self):
        """Test validation of valid script syntax widget IDs."""
        # Valid string concatenation with camelCase
        errors = self.rule._validate_script_id_naming("<% 'myField' + value %>")
        assert errors == []
        
        # Valid multiple strings with camelCase
        errors = self.rule._validate_script_id_naming("<% 'prefix' + variable + 'suffix' %>")
        assert errors == []
        
        # Valid backtick template
        errors = self.rule._validate_script_id_naming("<% `question{{id}}`  %>")
        assert errors == []
        
        # Script starting with variable (should pass - no validation)
        errors = self.rule._validate_script_id_naming("<% someVariable %>")
        assert errors == []
        
        # Script starting with variable and string concatenation (should pass - ignore entire script)
        errors = self.rule._validate_script_id_naming("<% someVariable + 'suffix' %>")
        assert errors == []
        
        # Script starting with variable and PascalCase string (should pass - ignore entire script)
        errors = self.rule._validate_script_id_naming("<% someVariable + 'Suffix' %>")
        assert errors == []
    
    def test_script_validation_invalid_cases(self):
        """Test validation of invalid script syntax widget IDs."""
        # Invalid string concatenation with PascalCase
        errors = self.rule._validate_script_id_naming("<% 'MyField' + value %>")
        assert len(errors) == 1
        assert "Static prefix 'MyField' should follow lowerCamelCase convention" in errors[0]
        
        # Invalid multiple strings with PascalCase
        errors = self.rule._validate_script_id_naming("<% 'prefix' + variable + 'Suffix' %>")
        assert len(errors) == 1
        assert "Static prefix 'Suffix' should follow lowerCamelCase convention" in errors[0]
        
        # Invalid backtick template with PascalCase
        errors = self.rule._validate_script_id_naming("<% `Question{{id}}`  %>")
        assert len(errors) == 1
        assert "Static prefix 'Question' should follow lowerCamelCase convention" in errors[0]
    
    def test_lower_camel_case_validation(self):
        """Test lowerCamelCase validation helper method."""
        # Valid camelCase
        assert self.rule._is_lower_camel_case("myField")
        assert self.rule._is_lower_camel_case("question")
        assert self.rule._is_lower_camel_case("field123")
        assert self.rule._is_lower_camel_case("")
        
        # Invalid cases
        assert not self.rule._is_lower_camel_case("MyField")
        assert not self.rule._is_lower_camel_case("my_field")
        assert not self.rule._is_lower_camel_case("my-field")
        assert not self.rule._is_lower_camel_case("123field")


class TestEndpointNameLowerCamelCaseRule:
    """Test cases for EndpointNameLowerCamelCaseRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointNameLowerCamelCaseRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "EndpointNameLowerCamelCaseRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "ACTION"
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
        assert self.rule.SEVERITY == "ADVICE"
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
        assert self.rule.SEVERITY == "ACTION"
        assert "status" in self.rule.DESCRIPTION.lower()


class TestEndpointBaseUrlTypeRule:
    """Test cases for EndpointUrlBaseUrlTypeRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = EndpointBaseUrlTypeRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
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
        assert self.rule.SEVERITY == "ADVICE"
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
        assert self.rule.SEVERITY == "ADVICE"
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
            EndpointBaseUrlTypeRule(),
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
            EndpointBaseUrlTypeRule(),
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
