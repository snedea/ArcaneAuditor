"""Test cases for line number calculations with known line positions."""

import json
import tempfile
import os
from pathlib import Path
from parser.models import PMDModel, PMDPresentation, ProjectContext
from parser.rules.script.core.variable_naming import ScriptVariableNamingRule
from parser.rules.script.complexity.long_function import ScriptLongFunctionRule
from parser.rules.script.complexity.cyclomatic_complexity import ScriptComplexityRule
from parser.pmd_preprocessor import preprocess_pmd_content


def _create_pmd_model(source_content: str) -> PMDModel:
    """Create a PMDModel from source JSON content."""
    # Preprocess like the app parser does
    processed_content, line_mappings, hash_to_lines = preprocess_pmd_content(source_content.strip())
    pmd_data = json.loads(processed_content)
    
    # Extract presentation data
    presentation_data = pmd_data.get('presentation', {})
    
    # Create PMD model
    # Always provide a presentation object to satisfy Pydantic validation
    if presentation_data:
        presentation = PMDPresentation(
            title=presentation_data.get("title", {}),
            body=presentation_data.get("body", {}),
            footer=presentation_data.get("footer", {}),
            tabs=presentation_data.get("tabs", [])
        )
    else:
        # Create minimal presentation for validation
        presentation = PMDPresentation(
            title={},
            body={},
            footer={},
            tabs=[]
        )
    
    pmd_model = PMDModel(
        pageId=pmd_data.get('id', 'test'),
        inboundEndpoints=pmd_data.get('endPoints', []),
        presentation=presentation,
        onLoad=pmd_data.get('onLoad'),
        script=pmd_data.get('script'),
        file_path="test.pmd",
        source_content=source_content.strip()
    )
    
    # Set the hash-based line mappings
    pmd_model.set_hash_to_lines_mapping(hash_to_lines)
    
    return pmd_model


def test_line_number_single_line_script():
    """Test: <% code %> on line 3 should report line 3"""
    # Create a PMD file with script at known lines
    source = """{
  "id": "testPage",
  "onLoad": "<% const BadVar = 1; %>"
}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    # Run variable naming rule (should catch 'BadVar' variable - PascalCase violation)
    rule = ScriptVariableNamingRule()
    findings = list(rule.analyze(context))
    
    # Debug: Print all findings to see what's happening
    print(f"DEBUG: Found {len(findings)} total findings:")
    for i, finding in enumerate(findings):
        print(f"  {i+1}: {finding.message} (line {finding.line})")
    
    # Find variable naming violations
    var_violations = [f for f in findings if 'variable' in f.message.lower() and 'lowerCamelCase' in f.message]
    
    # Assert: violation should be on line 3 (where the script is)
    assert len(var_violations) > 0, "Should find variable naming violation"
    assert var_violations[0].line == 3, f"Expected line 3, got {var_violations[0].line}"


def test_line_number_multiline_script():
    """Test: Multiline script starting at line 3"""
    source = """{
  "id": "testPage",
  "script": "<%\\n        const BadVar1 = 1;\\n        const BadVar2 = 2;\\n        %>"
}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    # Run variable naming rule
    rule = ScriptVariableNamingRule()
    findings = list(rule.analyze(context))
    
    # Find variable naming violations
    var_violations = [f for f in findings if 'variable' in f.message.lower() and 'lowerCamelCase' in f.message]
    
    # Should find violations for both 'BadVar1' and 'BadVar2'
    assert len(var_violations) >= 2, f"Expected at least 2 violations, got {len(var_violations)}"
    
    # Check that violations are reported on lines 4 and 5 (script starts at line 3)
    violation_lines = [v.line for v in var_violations]
    assert 4 in violation_lines, f"Expected violation on line 4, got lines: {violation_lines}"
    assert 5 in violation_lines, f"Expected violation on line 5, got lines: {violation_lines}"


def test_line_number_nested_functions():
    """Test: Nested function line numbers"""
    source = """{
  "id": "testPage",
  "script": "<%\\n        const outerFunc = function() {\\n            const innerFunc = function() {\\n                const BadVar = 1;\\n            };\\n        };\\n        %>"
}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    # Run variable naming rule
    rule = ScriptVariableNamingRule()
    findings = list(rule.analyze(context))
    
    # Debug: Print all findings to see what's happening
    print(f"DEBUG: Found {len(findings)} total findings:")
    for i, finding in enumerate(findings):
        print(f"  {i+1}: {finding.message} (line {finding.line})")
    
    # Find variable naming violations
    var_violations = [f for f in findings if 'variable' in f.message.lower() and 'lowerCamelCase' in f.message]
    
    # Should find violation for 'BadVar' (PascalCase violation)
    assert len(var_violations) > 0, "Should find variable naming violation for BadVar"
    
    # The violation should be on the line where 'BadVar' is declared
    # This should be around line 5-6 depending on JSON formatting
    violation_line = var_violations[0].line
    assert 4 <= violation_line <= 7, f"Expected violation around line 5-6, got {violation_line}"


def test_line_number_long_function():
    """Test: Long function detection line numbers"""
    # Create a function with many lines to trigger long function rule
    function_lines = []
    for i in range(55):  # More than 50 lines to trigger the rule
        function_lines.append(f"        const var{i} = {i};")
    
    script_content = "<%\\n        const longFunction = function() {\\n" + "\\n".join(function_lines) + "\\n        };\\n        %>"
    source = f"""{{
  "id": "testPage",
  "script": "{script_content}"
}}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    # Run long function rule
    rule = ScriptLongFunctionRule()
    findings = list(rule.analyze(context))
    
    # Find long function violations
    long_func_violations = [f for f in findings if 'long function' in f.message.lower() or 'lines' in f.message.lower()]
    
    # Should find violation for the long function
    assert len(long_func_violations) > 0, "Should find long function violation"
    
    # The violation should be on the line where the function starts
    violation_line = long_func_violations[0].line
    assert 4 <= violation_line <= 6, f"Expected violation around line 5, got {violation_line}"


def test_line_number_complexity():
    """Test: Cyclomatic complexity line numbers"""
    source = """{
  "id": "testPage",
  "script": "<%\\n        const complexFunction = function() {\\n            if (true) {\\n                if (false) {\\n                    if (1) {\\n                        if (2) {\\n                            if (3) {\\n                                if (4) {\\n                                    if (5) {\\n                                        if (6) {\\n                                            if (7) {\\n                                                if (8) {\\n                                                    if (9) {\\n                                                        return true;\\n                                                    }\\n                                                }\\n                                            }\\n                                        }\\n                                    }\\n                                }\\n                            }\\n                        }\\n                    }\\n                }\\n            }\\n        };\\n        %>"
}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    # Run complexity rule
    rule = ScriptComplexityRule()
    findings = list(rule.analyze(context))
    
    # Find complexity violations
    complexity_violations = [f for f in findings if 'complexity' in f.message.lower()]
    
    # Should find violation for the complex function
    assert len(complexity_violations) > 0, "Should find complexity violation"
    
    # The violation should be on the line where the function starts
    violation_line = complexity_violations[0].line
    assert 4 <= violation_line <= 6, f"Expected violation around line 5, got {violation_line}"


if __name__ == "__main__":
    # Run tests
    test_line_number_single_line_script()
    print("✓ Single line script test passed")
    
    test_line_number_multiline_script()
    print("✓ Multiline script test passed")
    
    test_line_number_nested_functions()
    print("✓ Nested functions test passed")
    
    test_line_number_long_function()
    print("✓ Long function test passed")
    
    test_line_number_complexity()
    print("✓ Complexity test passed")
    
    print("\n🎉 All line number tests passed!")
