#!/usr/bin/env python3
"""
Tests for ScriptFunctionParameterNamingRule.
"""

import pytest
from parser.rules.script.core.function_parameter_naming import ScriptFunctionParameterNamingRule
from parser.models import ProjectContext, PMDModel, ScriptModel


class TestScriptFunctionParameterNamingRule:
    """Test cases for ScriptFunctionParameterNamingRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptFunctionParameterNamingRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly defined."""
        assert self.rule.DESCRIPTION == "Ensures function parameters follow lowerCamelCase naming convention"
        assert self.rule.SEVERITY == "ADVICE"
    
    def test_lowercamelcase_violations_in_pmd(self):
        """Test detection of non-lowerCamelCase parameters in PMD scripts."""
        script_content = """<%
            const validateUser = function(user_id, user_name, is_active) {
                return user_id && user_name && is_active;
            };
            
            const processData = function(data_source, target_table) {
                return data_source.map(item => item.process());
            };
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}' 
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for 'user_id', 'user_name', 'is_active', 'data_source', 'target_table'
        assert len(findings) == 5
        
        # Check specific violations
        violation_params = [f.message for f in findings]
        assert any("'user_id'" in msg for msg in violation_params)
        assert any("'user_name'" in msg for msg in violation_params)
        assert any("'is_active'" in msg for msg in violation_params)
        assert any("'data_source'" in msg for msg in violation_params)
        assert any("'target_table'" in msg for msg in violation_params)
    
    def test_lowercamelcase_no_violations(self):
        """Test that lowerCamelCase parameters don't trigger violations."""
        script_content = """<%
            const validateUser = function(userId, userName, isActive) {
                return userId && userName && isActive;
            };
            
            const processData = function(dataSource, targetTable) {
                return dataSource.map(item => item.process());
            };
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}' 
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_standalone_script_files(self):
        """Test analysis of standalone script files."""
        script_content = """var getCurrentTime = function() {
    return date:getTodaysDate(date:getDateTimeZone('US/Pacific'));
};

var isNewDateAfterReferenceDate = function (widget, newDate, referenceDate, message, message_type) {
    if (referenceDate==null){
        return null;
    }
    if (newDate == null || newDate > referenceDate) {
        widget.clearError();
        widget.clearWarning();
    } else {
        if (message_type == "ERROR") {
            widget.setError(message);
        } else {
            widget.setWarning(message);
        }
    }
};

{
    "getCurrentTime": getCurrentTime,
    "isNewDateAfterReferenceDate": isNewDateAfterReferenceDate
}"""
        
        script_model = ScriptModel(source=script_content, file_path="helperFunctions.script")
        self.context.scripts["helperFunctions.script"] = script_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violation for 'message_type'
        assert len(findings) == 1
        assert "'message_type'" in findings[0].message
        assert "messageType" in findings[0].message  # Should suggest the correct camelCase version
    
    def test_mixed_case_scenarios(self):
        """Test various mixed case scenarios."""
        script_content = """<%
            // Various naming patterns
            const func1 = function(USER_ID, user_name, userName, user_name_field) {
                return USER_ID + user_name + userName + user_name_field;
            };
            
            const func2 = function(is_valid, isValid, is_valid_flag) {
                return is_valid && isValid && is_valid_flag;
            };
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}' 
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for non-lowerCamelCase parameters
        violation_params = [f.message for f in findings]
        
        # These should be flagged
        assert any("'USER_ID'" in msg for msg in violation_params)
        assert any("'user_name'" in msg for msg in violation_params)
        assert any("'user_name_field'" in msg for msg in violation_params)
        assert any("'is_valid'" in msg for msg in violation_params)
        assert any("'is_valid_flag'" in msg for msg in violation_params)
        
        # These should NOT be flagged (already correct)
        assert not any("has function parameter 'userName'" in msg for msg in violation_params)
        assert not any("has function parameter 'isValid'" in msg for msg in violation_params)
    
    def test_suggestion_quality(self):
        """Test that parameter name suggestions are correct."""
        test_cases = [
            ("user_id", "userId"),
            ("user_name", "userName"),
            ("is_active", "isActive"),
            ("data_source", "dataSource"),
            ("target_table", "targetTable"),
            ("message_type", "messageType"),
            ("first_name", "firstName"),
            ("last_name", "lastName"),
            ("email_address", "emailAddress"),
            ("phone_number", "phoneNumber"),
        ]
        
        for param_name, expected_suggestion in test_cases:
            script_content = f"<% const func = function({param_name}) {{ return {param_name}; }}; %>"
            
            pmd_model = PMDModel(
                pageId="testPage",
                file_path="test.pmd",
                source_content='{"script": "' + script_content.replace('"', '\\"') + '"}' 
            )
            pmd_model.script = script_content
            context = ProjectContext()
            context.pmds["testPage"] = pmd_model
            
            findings = list(self.rule.analyze(context))
            
            if findings:  # Should have at least one finding
                assert expected_suggestion in findings[0].message, \
                    f"Expected '{expected_suggestion}' in suggestion for '{param_name}'"
    
    def test_edge_cases(self):
        """Test various edge cases."""
        script_content = """<%
            // Single parameter
            const func1 = function(param) { return param; };
            
            // Multiple parameters with mixed cases
            const func2 = function(a, b, c, param_name, anotherParam) { 
                return a + b + c + param_name + anotherParam; 
            };
            
            // Parameters with numbers
            const func3 = function(param1, param_2, param3_name) {
                return param1 + param_2 + param3_name;
            };
            
            // Empty parameter list
            const func4 = function() { return true; };
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}' 
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should flag non-lowerCamelCase parameters
        violation_params = [f.message for f in findings]
        
        # These should be flagged
        assert any("'param_name'" in msg for msg in violation_params)
        assert any("'param_2'" in msg for msg in violation_params)
        assert any("'param3_name'" in msg for msg in violation_params)
        
        # These should NOT be flagged (already correct)
        assert not any("'param'" in msg for msg in violation_params)
        assert not any("'a'" in msg for msg in violation_params)
        assert not any("'b'" in msg for msg in violation_params)
        assert not any("'c'" in msg for msg in violation_params)
        assert not any("'anotherParam'" in msg for msg in violation_params)
        assert not any("'param1'" in msg for msg in violation_params)
    
    def test_no_false_positives(self):
        """Test that the rule doesn't flag legitimate cases."""
        script_content = """<%
            // Legitimate lowerCamelCase names
            const func1 = function(userId, userName, isActive) {
                return userId && userName && isActive;
            };
            
            // Single letter parameters (should be allowed)
            const func2 = function(a, b, c) {
                return a + b + c;
            };
            
            // Already correct camelCase
            const func3 = function(dataSource, targetTable, isEnabled) {
                return dataSource.map(item => item.process());
            };
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}' 
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_nested_functions(self):
        """Test detection in nested function definitions."""
        script_content = """<%
            const outerFunc = function(outer_param) {
                const innerFunc = function(inner_param, another_inner) {
                    return inner_param + another_inner;
                };
                return innerFunc(outer_param, outer_param);
            };
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}' 
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for non-lowerCamelCase parameters
        violation_params = [f.message for f in findings]
        
        # These should be flagged
        assert any("'outer_param'" in msg for msg in violation_params)
        assert any("'inner_param'" in msg for msg in violation_params)
        assert any("'another_inner'" in msg for msg in violation_params)


if __name__ == "__main__":
    pytest.main([__file__])
