#!/usr/bin/env python3
"""
Debug script to check rule execution for filtering loop.
"""

from parser.rules.script.logic.functional_method_usage import ScriptFunctionalMethodUsageRule
from parser.models import PMDModel, ProjectContext

def debug_rule_execution():
    """Debug rule execution for filtering loop."""
    
    print("Debugging Rule Execution")
    print("=" * 25)
    
    # Create the rule
    rule = ScriptFunctionalMethodUsageRule()
    
    # The failing test case
    test_script = '''
let evenNumbers = [];
for(let i = 0; i < numbers.length; i++) {
    if(numbers[i] % 2 == 0) {
        evenNumbers.push(numbers[i]);
    }
}'''
    
    print(f"Test script: {test_script}")
    
    # Create PMD model
    pmd_model = PMDModel(
        pageId="testPage",
        file_path="test.pmd",
        onLoad=f"<% {test_script} %>",
        script="",
        inboundEndpoints=[],
        outboundEndpoints=[],
        presentation={}
    )
    
    context = ProjectContext()
    context.pmds = {"test": pmd_model}
    
    # Test the _check_manual_loops method directly
    print("\nTesting _check_manual_loops method:")
    try:
        findings = list(rule._check_manual_loops(test_script, "onLoad", "test.pmd", 1))
        print(f"Found {len(findings)} findings")
        for finding in findings:
            print(f"  Finding: {finding.message}")
    except Exception as e:
        print(f"ERROR in _check_manual_loops: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test the full rule execution
    print("\nTesting full rule execution:")
    try:
        findings = list(rule.analyze(context))
        print(f"Found {len(findings)} findings")
        for finding in findings:
            print(f"  Finding: {finding.message}")
    except Exception as e:
        print(f"ERROR in rule.analyze: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rule_execution()
