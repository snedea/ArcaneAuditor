#!/usr/bin/env python3
"""
Debug script to check visit_pmd method.
"""

from parser.rules.script.logic.functional_method_usage import ScriptFunctionalMethodUsageRule
from parser.models import PMDModel, ProjectContext

def debug_visit_pmd():
    """Debug visit_pmd method."""
    
    print("Debugging visit_pmd Method")
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
    
    print(f"PMD model onLoad: {pmd_model.onLoad}")
    
    # Test find_script_fields
    print("\nTesting find_script_fields:")
    script_fields = list(rule.find_script_fields(pmd_model))
    print(f"Found {len(script_fields)} script fields")
    
    for i, (field_path, field_value, field_name, line_offset) in enumerate(script_fields):
        print(f"  {i+1}: path={field_path}, name={field_name}, line_offset={line_offset}")
        print(f"    value: {field_value}")
    
    # Test visit_pmd
    print("\nTesting visit_pmd:")
    try:
        findings = list(rule.visit_pmd(pmd_model))
        print(f"Found {len(findings)} findings")
        for finding in findings:
            print(f"  Finding: {finding.message}")
    except Exception as e:
        print(f"ERROR in visit_pmd: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_visit_pmd()
