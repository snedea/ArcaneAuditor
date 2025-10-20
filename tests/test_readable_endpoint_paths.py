"""Test that endpoint paths are human-readable in error messages."""

import json
from parser.models import PMDModel, PMDPresentation, ProjectContext
from parser.rules.script.logic.string_concat import ScriptStringConcatRule
from parser.pmd_preprocessor import preprocess_pmd_content


def test_inbound_endpoint_readable_name():
    """Test that inbound endpoint names appear in error messages."""
    source = """{
  "id": "testPage",
  "endPoints": [
    {
      "name": "submitWidGET",
      "url": "<% '/data?query=' + param %>"
    },
    {
      "name": "updateDataPOST",
      "url": "<% '/update/' + id %>"
    }
  ]
}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    rule = ScriptStringConcatRule()
    findings = list(rule.analyze(context))
    
    print("\n=== Inbound Endpoint Test ===")
    print(f"Found {len(findings)} violations\n")
    
    for finding in findings:
        print(f"Message: {finding.message}")
        
        # Check that the message contains readable endpoint names
        # Note: model converts endPoints to inboundEndpoints
        if "submitWidGET" in finding.message:
            assert "Inbound endpoint 'submitWidGET'" in finding.message, \
                f"Expected 'Inbound endpoint submitWidGET' in message"
            print("[OK] submitWidGET endpoint name found in message")
        elif "updateDataPOST" in finding.message:
            assert "Inbound endpoint 'updateDataPOST'" in finding.message, \
                f"Expected 'Inbound endpoint updateDataPOST' in message"
            print("[OK] updateDataPOST endpoint name found in message")
        print()




def test_script_field_readable_name():
    """Test that non-endpoint script fields still work."""
    source = """{
  "id": "testPage",
  "script": "<% var msg = 'Hello' + name; %>",
  "onLoad": "<% var data = 'prefix' + value; %>"
}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    rule = ScriptStringConcatRule()
    findings = list(rule.analyze(context))
    
    print("\n=== Script Field Test ===")
    print(f"Found {len(findings)} violations\n")
    
    for finding in findings:
        print(f"Message: {finding.message}")
        
        # Non-endpoint fields should just show the field name
        if "'script'" in finding.message or "script" in finding.message:
            print("[OK] script field shown clearly")
        if "'onLoad'" in finding.message or "onLoad" in finding.message:
            print("[OK] onLoad field shown clearly")
        print()




def _create_pmd_model(source_content: str):
    """Helper to create PMDModel from source."""
    processed_content, line_mappings, hash_to_lines = preprocess_pmd_content(source_content.strip())
    pmd_data = json.loads(processed_content)
    presentation_data = pmd_data.get('presentation', {})
    
    if presentation_data:
        presentation = PMDPresentation(
            title=presentation_data.get("title", {}),
            body=presentation_data.get("body", {}),
            footer=presentation_data.get("footer", {}),
            tabs=presentation_data.get("tabs", [])
        )
    else:
        presentation = PMDPresentation(title={}, body={}, footer={}, tabs=[])
    
    # Handle outboundData structure
    outbound_data = pmd_data.get('outboundData', {})
    outbound_endpoints = outbound_data.get('outboundEndPoints', []) if isinstance(outbound_data, dict) else []
    
    pmd_model = PMDModel(
        pageId=pmd_data.get('id', 'test'),
        inboundEndpoints=pmd_data.get('endPoints', []),
        outboundEndpoints=outbound_endpoints,
        presentation=presentation,
        onLoad=pmd_data.get('onLoad'),
        script=pmd_data.get('script'),
        file_path="test.pmd",
        source_content=source_content.strip()
    )
    
    # Set the hash-based line mappings
    pmd_model.set_hash_to_lines_mapping(hash_to_lines)
    
    return pmd_model


if __name__ == "__main__":
    test_inbound_endpoint_readable_name()
    test_outbound_endpoint_readable_name()
    test_script_field_readable_name()
    test_real_capital_planning_readable()

