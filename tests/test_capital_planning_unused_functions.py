"""
Test unused function detection with real Capital Planning PMD file.
Verifies that false positives are eliminated.
"""
import pytest
from parser.rules.script.unused_code.unused_functions import ScriptUnusedFunctionRule
from parser.models import ProjectContext, PMDModel
from parser.pmd_preprocessor import preprocess_pmd_content


class TestCapitalPlanningUnusedFunctions:
    """Test unused function detection with Capital Planning patterns."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedFunctionRule()
        self.context = ProjectContext()
    
    def test_add_service_function_not_flagged_as_unused(self):
        """
        Test the actual pattern from CapitalPlanningRequestEdit.pmd line 1181.
        This function should NOT be flagged as unused.
        """
        # Simplified version of the actual code
        script = """<%
            var addServiceToPageVariablebyWID = function (WID) {
                let service = pageVariables.allServices.find(serv => {
                    return serv.id == WID;
                });
                let serviceLkp = pageVariables.reqServices.find(serv => {
                    return serv.id == WID;
                });
                if (empty serviceLkp) {
                    pageVariables.reqServices.add({
                        'id': WID,
                        'descriptor': service.descriptor
                    });
                }
            };
            
            // Function is called later
            addServiceToPageVariablebyWID(widget.getValue());
        %>"""
        
        pmd_model = PMDModel(
            pageId="CapitalPlanningRequestEdit",
            script=script,
            file_path="CapitalPlanningRequestEdit.pmd"
        )
        self.context.pmds["CapitalPlanningRequestEdit"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Filter to only unused function violations (not other rules)
        unused_func_findings = [f for f in findings if 'addServiceToPageVariablebyWID' in f.message]
        
        assert len(unused_func_findings) == 0, \
            f"addServiceToPageVariablebyWID should not be flagged as unused. Got: {[f.message for f in findings]}"
    
    def test_violation_message_includes_variable_name(self):
        """Verify that violation messages now include the variable name."""
        script = """<%
            var myUnusedFunction = function(x) {
                return x * 2;
            };
            
            var result = 42;  // Never uses myUnusedFunction
        %>"""
        
        pmd_model = PMDModel(
            pageId="test",
            script=script,
            file_path="test.pmd"
        )
        self.context.pmds["test"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 1
        assert 'myUnusedFunction' in findings[0].message
        assert 'variable' in findings[0].message.lower()

