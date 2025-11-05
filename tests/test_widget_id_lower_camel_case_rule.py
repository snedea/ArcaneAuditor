#!/usr/bin/env python3
"""Unit tests for WidgetIdLowerCamelCaseRule."""

import pytest
from parser.rules.structure.widgets.widget_id_lower_camel_case import WidgetIdLowerCamelCaseRule
from parser.models import ProjectContext


class TestWidgetIdLowerCamelCaseRule:
    """Test cases for WidgetIdLowerCamelCaseRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = WidgetIdLowerCamelCaseRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "WidgetIdLowerCamelCaseRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "ADVICE"
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

    def test_widget_id_in_tabs_invalid_naming_flagged(self):
        """Test that widget IDs in tabs with invalid naming are flagged."""
        from parser.models import PMDModel
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "presentation": {
    "body": {},
    "tabs": [
      {
        "type": "section",
        "children": [
          {
            "type": "text",
            "id": "MyField",
            "value": "Hello"
          }
        ]
      }
    ]
  }
}''',
            "presentation": {
                "body": {},
                "tabs": [
                    {
                        "type": "section",
                        "children": [
                            {
                                "type": "text",
                                "id": "MyField",
                                "value": "Hello"
                            }
                        ]
                    }
                ]
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "MyField" in findings[0].message
        assert "lowercamelcase" in findings[0].message.lower() or "camelcase" in findings[0].message.lower()

    def test_widget_id_in_tabs_valid_naming_not_flagged(self):
        """Test that widget IDs in tabs with valid naming are not flagged."""
        from parser.models import PMDModel
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "source_content": '''{
  "presentation": {
    "body": {},
    "tabs": [
      {
        "type": "section",
        "children": [
          {
            "type": "text",
            "id": "myField",
            "value": "Hello"
          }
        ]
      }
    ]
  }
}''',
            "presentation": {
                "body": {},
                "tabs": [
                    {
                        "type": "section",
                        "children": [
                            {
                                "type": "text",
                                "id": "myField",
                                "value": "Hello"
                            }
                        ]
                    }
                ]
            }
        }
        pmd_model = PMDModel(**pmd_data)
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
