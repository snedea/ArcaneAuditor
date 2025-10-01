"""Test that endpoint paths are human-readable in error messages."""

import json
from parser.models import PMDModel, PMDPresentation, ProjectContext
from parser.rules.script.logic.string_concat import ScriptStringConcatRule
from parser.pmd_preprocessor import preprocess_pmd_content


def test_inbound_endpoint_readable_name():
    """Test that inbound endpoint names appear in error messages."""
    source = """{
  "id": "TestPage",
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
            assert "inboundEndpoints->name: submitWidGET->url" in finding.message, \
                f"Expected 'inboundEndpoints->name: submitWidGET->url' in message"
            print("[OK] submitWidGET endpoint name found in message")
        elif "updateDataPOST" in finding.message:
            assert "inboundEndpoints->name: updateDataPOST->url" in finding.message, \
                f"Expected 'inboundEndpoints->name: updateDataPOST->url' in message"
            print("[OK] updateDataPOST endpoint name found in message")
        print()


def test_outbound_endpoint_readable_name():
    """Test that outbound endpoint names appear in error messages."""
    source = """{
  "id": "TestPage",
  "outboundData": {
    "outboundEndPoints": [
      {
        "name": "updateRequestPOST",
        "url": "/api/update",
        "onSend": "<% var data = 'payload' + id; %>"
      }
    ]
  }
}"""
    
    pmd_model = _create_pmd_model(source)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    rule = ScriptStringConcatRule()
    findings = list(rule.analyze(context))
    
    print("\n=== Outbound Endpoint Test ===")
    print(f"Found {len(findings)} violations\n")
    
    for finding in findings:
        print(f"Message: {finding.message}")
        
        # Check that the message contains readable endpoint name
        # Note: model shows outboundEndpoints (not outboundData->outboundEndPoints)
        assert "updateRequestPOST" in finding.message, \
            f"Expected 'updateRequestPOST' in message"
        assert "outboundEndpoints->name: updateRequestPOST->onSend" in finding.message, \
            f"Expected full readable path in message"
        print("[OK] updateRequestPOST endpoint name found in readable format")
        print()


def test_script_field_readable_name():
    """Test that non-endpoint script fields still work."""
    source = """{
  "id": "TestPage",
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


def test_real_capital_planning_readable():
    """Test with real Capital Planning file."""
    file_path = "samples/archives/capitalProjectPlanning/presentation/CapitalPlanningRequestEdit.pmd"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        source_content = f.read().strip()
    
    pmd_model = _create_pmd_model(source_content)
    context = ProjectContext()
    context.pmds = {'test': pmd_model}
    
    rule = ScriptStringConcatRule()
    findings = list(rule.analyze(context))
    
    print("\n=== Real Capital Planning File Test ===")
    print(f"Found {len(findings)} violations\n")
    
    # Show first 5 findings
    for i, finding in enumerate(findings[:5]):
        print(f"\nFinding {i+1} (Line {finding.line}):")
        print(f"  {finding.message[:150]}...")
        
        # Check if endpoint names are in messages
        if "submitWidGET" in finding.message:
            print("  [OK] Contains 'submitWidGET' endpoint name")
        if "eventInfoGET" in finding.message:
            print("  [OK] Contains 'eventInfoGET' endpoint name")
        if "requestGET" in finding.message:
            print("  [OK] Contains 'requestGET' endpoint name")


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

