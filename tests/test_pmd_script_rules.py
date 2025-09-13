"""
Unit tests for PMD Script Rules.
"""
import pytest
from unittest.mock import Mock, patch
from parser.rules.script_validation_rules import ScriptVarUsageRule, ScriptUnusedFunctionParametersRule, ScriptEmptyFunctionRule, ScriptFunctionReturnConsistencyRule
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
        assert self.rule.ID == "PMD001"
        assert self.rule.DESCRIPTION == "Detects the use of 'var' in PMD Script."
        assert self.rule.SEVERITY == "INFO"
    
    def test_analyze_no_pmds(self):
        """Test analysis when no PMD models exist."""
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_analyze_pmd_no_onload_script(self):
        """Test analysis when PMD has no onLoad script."""
        # Create PMD model without onLoad script
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_analyze_pmd_with_var_declaration(self):
        """Test analysis when PMD contains 'var' declarations."""
        # Create PMD model with onLoad script containing 'var'
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% var x = 1; var y = 2; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        # Mock the AST to simulate 'var' declarations
        mock_ast = Mock()
        mock_var_node1 = Mock()
        mock_var_node1.line = 1
        mock_var_node1.column = 4
        mock_var_node2 = Mock()
        mock_var_node2.line = 1
        mock_var_node2.column = 12
        
        mock_ast.find_data.return_value = [mock_var_node1, mock_var_node2]
        
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=mock_ast):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 2
        assert all(isinstance(finding, Finding) for finding in findings)
        assert all(finding.rule == self.rule for finding in findings)
        assert all("Legacy 'var' declaration found" in finding.message for finding in findings)
        
        # Check line and column information
        assert findings[0].line == 1
        assert findings[0].column == 4
        assert findings[1].line == 1
        assert findings[1].column == 12
    
    def test_analyze_pmd_with_no_var_declaration(self):
        """Test analysis when PMD contains no 'var' declarations."""
        # Create PMD model with onLoad script without 'var'
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% let x = 1; const y = 2; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        # Mock the AST to simulate no 'var' declarations
        mock_ast = Mock()
        mock_ast.find_data.return_value = []  # No variable_statement nodes
        
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=mock_ast):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0
    
    def test_analyze_multiple_pmds(self):
        """Test analysis with multiple PMD models."""
        # Create multiple PMD models
        pmd_model1 = PMDModel(
            pageId="page1",
            onLoad="<% var x = 1; %>",
            file_path="page1.pmd"
        )
        pmd_model2 = PMDModel(
            pageId="page2",
            onLoad="<% let y = 2; %>",  # No 'var' here
            file_path="page2.pmd"
        )
        pmd_model3 = PMDModel(
            pageId="page3",
            onLoad="<% var a = 1; var b = 2; %>",
            file_path="page3.pmd"
        )
        
        self.context.pmds["page1"] = pmd_model1
        self.context.pmds["page2"] = pmd_model2
        self.context.pmds["page3"] = pmd_model3
        
        # Mock ASTs for each PMD
        mock_ast1 = Mock()
        mock_var_node1 = Mock()
        mock_var_node1.line = 1
        mock_var_node1.column = 4
        mock_ast1.find_data.return_value = [mock_var_node1]
        
        mock_ast2 = Mock()
        mock_ast2.find_data.return_value = []  # No 'var' declarations
        
        mock_ast3 = Mock()
        mock_var_node3a = Mock()
        mock_var_node3a.line = 1
        mock_var_node3a.column = 4
        mock_var_node3b = Mock()
        mock_var_node3b.line = 1
        mock_var_node3b.column = 12
        mock_ast3.find_data.return_value = [mock_var_node3a, mock_var_node3b]
        
        with patch.object(pmd_model1, 'get_onLoad_ast', return_value=mock_ast1), \
             patch.object(pmd_model2, 'get_onLoad_ast', return_value=mock_ast2), \
             patch.object(pmd_model3, 'get_onLoad_ast', return_value=mock_ast3):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 3  # 1 from page1 + 2 from page3
        assert all("Legacy 'var' declaration found" in finding.message for finding in findings)
    
    def test_analyze_pmd_ast_parsing_failure(self):
        """Test analysis when AST parsing fails."""
        # Create PMD model with onLoad script
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% var x = 1; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        # Mock get_onLoad_ast to return None (parsing failure)
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=None):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0
    
    def test_analyze_pmd_empty_onload_script(self):
        """Test analysis when onLoad script is empty."""
        # Create PMD model with empty onLoad script
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        # Mock get_onLoad_ast to return None for empty script
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=None):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0
    
    def test_analyze_pmd_whitespace_only_onload_script(self):
        """Test analysis when onLoad script contains only whitespace."""
        # Create PMD model with whitespace-only onLoad script
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="   \n\t   ",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        # Mock get_onLoad_ast to return None for whitespace-only script
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=None):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0
    
    def test_finding_message_content(self):
        """Test that finding messages contain the correct information."""
        # Create PMD model with onLoad script containing 'var'
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% var x = 1; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        # Mock the AST to simulate 'var' declaration
        mock_ast = Mock()
        mock_var_node = Mock()
        mock_var_node.line = 1
        mock_var_node.column = 4
        
        mock_ast.find_data.return_value = [mock_var_node]
        
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=mock_ast):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        finding = findings[0]
        assert "Legacy 'var' declaration found" in finding.message
        assert "Use 'let' or 'const' instead" in finding.message
        assert finding.rule_id == "PMD001"
        assert finding.severity == "INFO"
    
    def test_visit_pmd_method(self):
        """Test the visit_pmd method directly."""
        # Create PMD model with onLoad script containing 'var'
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% var x = 1; %>",
            file_path="test.pmd"
        )
        
        # Mock the AST to simulate 'var' declaration
        mock_ast = Mock()
        mock_var_node = Mock()
        mock_var_node.line = 1
        mock_var_node.column = 4
        
        mock_ast.find_data.return_value = [mock_var_node]
        
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=mock_ast):
            findings = list(self.rule.visit_pmd(pmd_model))
        
        assert len(findings) == 1
        finding = findings[0]
        assert isinstance(finding, Finding)
        assert finding.rule == self.rule
        assert "Legacy 'var' declaration found" in finding.message
        assert finding.line == 1
        assert finding.column == 4


class TestScriptVarUsageRuleIntegration:
    """Integration tests for ScriptVarUsageRule with real AST parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptVarUsageRule()
        self.context = ProjectContext()
    
    def test_real_ast_parsing_with_var(self):
        """Test with real AST parsing when 'var' is present."""
        # This test would require the actual PMD script parser to be working
        # For now, we'll mock it but structure it to work with real parsing later
        
        pmd_model = PMDModel(
            pageId="test-page",
            onLoad="<% var x = 1; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        # Mock the parser to simulate real AST parsing
        mock_ast = Mock()
        mock_var_node = Mock()
        mock_var_node.line = 1
        mock_var_node.column = 4
        
        mock_ast.find_data.return_value = [mock_var_node]
        
        with patch.object(pmd_model, 'get_onLoad_ast', return_value=mock_ast):
            findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding.rule_id == "PMD001"
        assert finding.severity == "INFO"
        assert "Legacy 'var' declaration found" in finding.message


class TestScriptUnusedFunctionParametersRule:
    """Test SCRIPT012 - Script Unused Function Parameters Rule"""
    
    def test_unused_function_parameter_violation(self):
        rule = ScriptUnusedFunctionParametersRule()
        context = ProjectContext()
        
        # Create PMD model with script containing unused parameter
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function processData(data, unusedParam, config) { return data.value; }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding.rule_id == "SCRIPT012"
        assert finding.severity == "WARNING"
        assert "unusedParam" in finding.message
    
    def test_no_unused_parameters(self):
        rule = ScriptUnusedFunctionParametersRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function processData(data, config) { return data.value + config.multiplier; }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 0
    
    def test_function_with_no_parameters(self):
        rule = ScriptUnusedFunctionParametersRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function getData() { return 'test'; }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 0
    
    def test_multiple_unused_parameters(self):
        rule = ScriptUnusedFunctionParametersRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function test(a, b, c) { return a; }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 2  # b and c are unused
        unused_params = [f.message for f in findings]
        assert any("b" in msg for msg in unused_params)
        assert any("c" in msg for msg in unused_params)


class TestScriptEmptyFunctionRule:
    """Test SCRIPT013 - Script Empty Function Rule"""
    
    def test_empty_function_violation(self):
        rule = ScriptEmptyFunctionRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function calculateTotal(items) { }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding.rule_id == "SCRIPT013"
        assert finding.severity == "WARNING"
        assert "empty body" in finding.message
    
    def test_function_with_implementation(self):
        rule = ScriptEmptyFunctionRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function calculateTotal(items) { let total = 0; return total; }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 0
    
    def test_function_with_comment_only(self):
        rule = ScriptEmptyFunctionRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function test() { // TODO: implement this }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 1  # Comment-only function is still considered empty
    
    def test_function_with_return_statement(self):
        rule = ScriptEmptyFunctionRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function getValue() { return 42; }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 0


class TestScriptFunctionReturnConsistencyRule:
    """Test SCRIPT014 - Script Function Return Consistency Rule"""
    
    def test_inconsistent_return_violation(self):
        rule = ScriptFunctionReturnConsistencyRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function processData(data) { if (data.isValid) { return data.value; } }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding.rule_id == "SCRIPT014"
        assert finding.severity == "WARNING"
        assert "inconsistent return pattern" in finding.message
    
    def test_consistent_no_returns(self):
        rule = ScriptFunctionReturnConsistencyRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function processData(data) { let result = data.value; console.log(result); }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 0
    
    def test_consistent_all_returns(self):
        rule = ScriptFunctionReturnConsistencyRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function processData(data) { if (data.isValid) { return data.value; } else { return null; } }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 0
    
    def test_single_return_statement(self):
        rule = ScriptFunctionReturnConsistencyRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="<%function getValue() { return 42; }%>"
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 0
    
    def test_complex_inconsistent_returns(self):
        rule = ScriptFunctionReturnConsistencyRule()
        context = ProjectContext()
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            onLoad="""<%function complex(data) { 
                if (data.type == 'A') { 
                    return data.value; 
                } else if (data.type == 'B') { 
                    let result = data.value * 2; 
                } 
            }%>"""
        )
        context.pmds["test-page"] = pmd_model
        
        findings = list(rule.analyze(context))
        
        assert len(findings) == 1


if __name__ == "__main__":
    pytest.main([__file__])
