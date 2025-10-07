#!/usr/bin/env python3
"""Integration tests for all script rules."""

import pytest
from parser.rules.script.core.var_usage import ScriptVarUsageRule
from parser.rules.script.core.console_log import ScriptConsoleLogRule
from parser.rules.script.core.variable_naming import ScriptVariableNamingRule
from parser.rules.script.complexity.nesting_level import ScriptNestingLevelRule
from parser.rules.script.complexity.cyclomatic_complexity import ScriptComplexityRule
from parser.rules.script.complexity.long_function import ScriptLongFunctionRule
from parser.rules.script.unused_code.unused_variables import ScriptUnusedVariableRule
from parser.rules.script.unused_code.unused_parameters import ScriptUnusedFunctionParametersRule
from parser.rules.script.unused_code.empty_functions import ScriptEmptyFunctionRule
from parser.rules.script.logic.magic_numbers import ScriptMagicNumberRule
from parser.rules.script.logic.null_safety import ScriptNullSafetyRule
from parser.rules.script.logic.verbose_boolean import ScriptVerboseBooleanCheckRule
from parser.rules.script.logic.return_consistency import ScriptFunctionReturnConsistencyRule
from parser.rules.base import Finding
from parser.models import ProjectContext, PMDModel


class TestAllScriptRulesIntegration:
    """Integration tests for all script rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = ProjectContext()
        
        # Create a PMD model with various violations
        self.pmd_model = PMDModel(
            pageId="test-page",
            script="<% var unusedVar = 1; console.debug('test'); let snake_case_var = 2; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = self.pmd_model
    
    def test_all_rules_can_be_instantiated(self):
        """Test that all script rules can be instantiated."""
        rules = [
            ScriptVarUsageRule(),
            ScriptConsoleLogRule(),
            ScriptVariableNamingRule(),
            ScriptNestingLevelRule(),
            ScriptComplexityRule(),
            ScriptLongFunctionRule(),
            ScriptUnusedVariableRule(),
            ScriptUnusedFunctionParametersRule(),
            ScriptEmptyFunctionRule(),
            ScriptMagicNumberRule(),
            ScriptNullSafetyRule(),
            ScriptVerboseBooleanCheckRule(),
            ScriptFunctionReturnConsistencyRule(),
        ]
        
        # Test that all rules have required attributes
        for rule in rules:
            assert hasattr(rule, 'ID')
            assert hasattr(rule, 'DESCRIPTION')
            assert hasattr(rule, 'SEVERITY')
            assert hasattr(rule, 'analyze')
            # ID is now the base class default since we removed hardcoded IDs
            assert rule.ID == 'RULE000'
    
    def test_all_rules_analyze_method(self):
        """Test that all rules can analyze without errors."""
        rules = [
            ScriptVarUsageRule(),
            ScriptConsoleLogRule(),
            ScriptVariableNamingRule(),
            ScriptNestingLevelRule(),
            ScriptComplexityRule(),
            ScriptLongFunctionRule(),
            ScriptUnusedVariableRule(),
            ScriptUnusedFunctionParametersRule(),
            ScriptEmptyFunctionRule(),
            ScriptMagicNumberRule(),
            ScriptNullSafetyRule(),
            ScriptVerboseBooleanCheckRule(),
            ScriptFunctionReturnConsistencyRule(),
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


if __name__ == '__main__':
    pytest.main([__file__])
