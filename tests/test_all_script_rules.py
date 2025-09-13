"""
Comprehensive unit tests for all PMD Script Rules.
"""
import pytest
from unittest.mock import Mock, patch
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


class TestScriptVarUsageRule:
    """Test cases for ScriptVarUsageRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptVarUsageRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT001"
        assert self.rule.SEVERITY == "WARNING"
        assert "var" in self.rule.DESCRIPTION.lower()
    
    def test_analyze_no_pmds(self):
        """Test analysis when no PMD models exist."""
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_analyze_pmd_with_var_declaration(self):
        """Test analysis when PMD contains 'var' declarations."""
        pmd_model = PMDModel(
            pageId="test-page",
            script="<% var x = 1; var y = 2; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2
        assert all(f.rule_id == "SCRIPT001" for f in findings)


class TestScriptConsoleLogRule:
    """Test cases for ScriptConsoleLogRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptConsoleLogRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT005"
        assert self.rule.SEVERITY == "WARNING"
        assert "console" in self.rule.DESCRIPTION.lower()


class TestScriptVariableNamingRule:
    """Test cases for ScriptVariableNamingRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptVariableNamingRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT008"
        assert self.rule.SEVERITY == "WARNING"
        assert "naming" in self.rule.DESCRIPTION.lower()


class TestScriptNestingLevelRule:
    """Test cases for ScriptNestingLevelRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptNestingLevelRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT002"
        assert self.rule.SEVERITY == "WARNING"
        assert "nesting" in self.rule.DESCRIPTION.lower()


class TestScriptComplexityRule:
    """Test cases for ScriptComplexityRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptComplexityRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT003"
        assert self.rule.SEVERITY == "WARNING"
        assert "complexity" in self.rule.DESCRIPTION.lower()


class TestScriptLongFunctionRule:
    """Test cases for ScriptLongFunctionRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptLongFunctionRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT007"
        assert self.rule.SEVERITY == "WARNING"
        assert "function" in self.rule.DESCRIPTION.lower()


class TestScriptUnusedVariableRule:
    """Test cases for ScriptUnusedVariableRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedVariableRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT004"
        assert self.rule.SEVERITY == "WARNING"
        assert "variable" in self.rule.DESCRIPTION.lower()


class TestScriptUnusedFunctionParametersRule:
    """Test cases for ScriptUnusedFunctionParametersRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedFunctionParametersRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT012"
        assert self.rule.SEVERITY == "WARNING"
        assert "parameter" in self.rule.DESCRIPTION.lower()


class TestScriptEmptyFunctionRule:
    """Test cases for ScriptEmptyFunctionRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptEmptyFunctionRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT013"
        assert self.rule.SEVERITY == "WARNING"
        assert "empty" in self.rule.DESCRIPTION.lower()


class TestScriptMagicNumberRule:
    """Test cases for ScriptMagicNumberRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptMagicNumberRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT006"
        assert self.rule.SEVERITY == "INFO"
        assert "magic" in self.rule.DESCRIPTION.lower()


class TestScriptNullSafetyRule:
    """Test cases for ScriptNullSafetyRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptNullSafetyRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT010"
        assert self.rule.SEVERITY == "WARNING"
        assert "null" in self.rule.DESCRIPTION.lower()


class TestScriptVerboseBooleanCheckRule:
    """Test cases for ScriptVerboseBooleanCheckRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptVerboseBooleanCheckRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT011"
        assert self.rule.SEVERITY == "WARNING"
        assert "boolean" in self.rule.DESCRIPTION.lower()


class TestScriptFunctionReturnConsistencyRule:
    """Test cases for ScriptFunctionReturnConsistencyRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptFunctionReturnConsistencyRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "SCRIPT014"
        assert self.rule.SEVERITY == "WARNING"
        assert "return" in self.rule.DESCRIPTION.lower()


class TestAllRulesIntegration:
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
            assert rule.ID.startswith('SCRIPT')
    
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
