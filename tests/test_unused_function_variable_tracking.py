"""
Unit tests for ScriptUnusedFunctionRule - variable tracking.

Tests that the rule correctly identifies functions assigned to variables
and tracks them by variable name, not function name (since all functions
in PMD Script are anonymous).
"""
import pytest
from parser.rules.script.unused_code.unused_functions import ScriptUnusedFunctionRule
from parser.models import ProjectContext, PMDModel


class TestUnusedFunctionVariableTracking:
    """Test that unused function detection tracks variable names correctly."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedFunctionRule()
        self.context = ProjectContext()
    
    def test_function_assigned_to_variable_and_used_no_violation(self):
        """Function assigned to variable and called by variable name should NOT be flagged."""
        script = """<%
            var addServiceToPageVariable = function(WID) {
                return WID + 1;
            };
            
            var result = addServiceToPageVariable(123);
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0, "Used function should not be flagged as unused"
    
    def test_function_assigned_to_variable_not_used_has_violation(self):
        """Function assigned to variable but never called should be flagged."""
        script = """<%
            var unusedFunction = function(x) {
                return x * 2;
            };
            
            var result = 42;
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1, "Unused function should be flagged"
        assert "unusedFunction" in findings[0].message, "Variable name should be in message"
    
    def test_multiple_functions_mixed_usage(self):
        """Multiple functions with mixed usage should correctly identify only unused ones."""
        script = """<%
            var helper1 = function(a) { return a + 1; };
            var helper2 = function(b) { return b * 2; };
            var helper3 = function(c) { return c - 1; };
            
            var x = helper1(5);
            var y = helper3(10);
            // helper2 is never called
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1, "Only unused function should be flagged"
        assert "helper2" in findings[0].message, "helper2 should be flagged as unused"
    
    def test_function_used_in_callback(self):
        """Function used as a callback should not be flagged."""
        script = """<%
            var processItem = function(item) {
                return item.id;
            };
            
            var items = [{id: 1}, {id: 2}];
            var ids = items.map(processItem);
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0, "Function used as callback should not be flagged"
    
    def test_function_called_multiple_times(self):
        """Function called multiple times should not be flagged."""
        script = """<%
            var calculate = function(x) { return x * 2; };
            
            var a = calculate(1);
            var b = calculate(2);
            var c = calculate(3);
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0, "Function used multiple times should not be flagged"
    
    def test_nested_function_calls(self):
        """Functions used in nested calls should not be flagged."""
        script = """<%
            var double = function(x) { return x * 2; };
            var triple = function(x) { return x * 3; };
            
            var result = double(triple(5));
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0, "Nested function calls should not be flagged"
    
    def test_function_in_conditional(self):
        """Function used in conditional should not be flagged."""
        script = """<%
            var validator = function(val) { return val > 0; };
            
            if (validator(x)) {
                console.log("valid");
            }
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0, "Function in conditional should not be flagged"
    
    def test_let_and_const_function_declarations(self):
        """Functions declared with let/const should also be tracked."""
        script = """<%
            let helper1 = function(x) { return x; };
            const helper2 = function(y) { return y; };
            
            var result = helper1(5);
            // helper2 is unused
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1, "Unused const function should be flagged"
        assert "helper2" in findings[0].message
    
    def test_arrow_function_assigned_to_variable(self):
        """Arrow functions assigned to variables should also be tracked."""
        script = """<%
            var arrowFunc = (x) => { return x * 2; };
            var unusedArrow = (y) => { return y * 3; };
            
            var result = arrowFunc(10);
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1, "Unused arrow function should be flagged"
        assert "unusedArrow" in findings[0].message
    
    def test_real_world_example_from_capital_planning(self):
        """Test with the actual code pattern from CapitalPlanningRequestEdit.pmd."""
        script = """<%
            // This function is used later
            var addServiceToPageVariablebyWID = function (WID) {
                let service = pageVariables.allServices.find(serv => {
                    serv.id == WID
                });
                if (empty serviceLkp) {
                    pageVariables.reqServices.add({
                        'id': WID,
                        'descriptor': service.descriptor
                    });
                }
            };
            
            // Later in the code, it's called
            addServiceToPageVariablebyWID(someWID);
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0, "Actually used function should not be flagged"

