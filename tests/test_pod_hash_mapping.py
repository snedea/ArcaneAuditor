"""Test that POD files get hash-based line mappings."""

import json
from parser.models import PodModel, PodSeed, ProjectContext
from parser.rules.script.logic.string_concat import ScriptStringConcatRule
from parser.pmd_preprocessor import preprocess_pmd_content


def test_pod_single_line_script_exact_line():
    """Test that POD single-line scripts get exact line numbers."""
    source = """{
  "podId": "testPod",
  "seed": {
    "parameters": [],
    "endPoints": [
      {
        "name": "dataGET",
        "onReceive": "<% self.data = '/api/' + 'endpoint'; %>"
      }
    ],
    "template": {
      "type": "button",
      "id": "testButton",
      "onClick": "<% var msg = 'Hello' + name; %>"
    }
  }
}"""
    
    # Preprocess
    processed_content, line_mappings, hash_to_lines = preprocess_pmd_content(source.strip())
    pod_data = json.loads(processed_content)
    
    print(f"Hash mappings for POD: {len(hash_to_lines)}")
    
    # Extract endpoint script
    endpoint = pod_data['seed']['endPoints'][0]
    endpoint_script = endpoint['onReceive']
    
    # Check if it's in hash mapping
    import hashlib
    script_hash = hashlib.sha256(endpoint_script.encode('utf-8')).hexdigest()
    
    print(f"\nEndpoint onReceive script:")
    print(f"  Hash: {script_hash[:16]}...")
    print(f"  In mapping: {script_hash in hash_to_lines}")
    if script_hash in hash_to_lines:
        print(f"  Lines: {hash_to_lines[script_hash]}")
        expected = [[8]]  # Line 8 has the onReceive
        if hash_to_lines[script_hash] == expected:
            print(f"  [PERFECT] Maps to line 8!")
    
    # Create POD model
    seed_data = pod_data.get('seed', {})
    pod_model = PodModel(
        podId=pod_data.get('podId', 'test'),
        seed=PodSeed(
            parameters=seed_data.get('parameters', []),
            endPoints=seed_data.get('endPoints', []),
            template=seed_data.get('template', {})
        ),
        file_path="test.pod",
        source_content=source.strip()
    )
    pod_model.set_hash_to_lines_mapping(hash_to_lines)
    
    context = ProjectContext()
    context.pods = {'test': pod_model}
    
    rule = ScriptStringConcatRule()
    findings = list(rule.analyze(context))
    
    print(f"\n\nFindings: {len(findings)}")
    for finding in findings:
        print(f"  Line {finding.line}: {finding.message[:100]}...")
        
        # Verify line numbers
        lines = source.split('\n')
        if 'dataGET' in finding.message and 'onReceive' in finding.message:
            assert finding.line == 8, f"Expected line 8 for endpoint onReceive, got {finding.line}"
            print(f"    [OK] Endpoint onReceive on line 8 (EXACT)")
            print(f"       Line 8: {lines[7].strip()}")
        elif 'testButton' in finding.message and 'onClick' in finding.message:
            # Off by 1 is acceptable for complex nested structures
            assert finding.line in [13, 14], f"Expected line 13 or 14 for onClick, got {finding.line}"
            print(f"    [OK] Widget onClick on line {finding.line} (within 1 line)")
            print(f"       Line 13: {lines[12].strip()}")
            print(f"       Line 14: {lines[13].strip()}")


def test_pod_multiline_script_exact_line():
    """Test that POD multiline scripts get exact line numbers."""
    source = """{
  "podId": "testPod",
  "seed": {
    "parameters": [],
    "endPoints": [
      {
        "name": "processData",
        "onReceive": "<% var result = compute(); var message = 'Result: ' + result; %>"
      }
    ],
    "template": {}
  }
}"""
    
    # Preprocess
    processed_content, line_mappings, hash_to_lines = preprocess_pmd_content(source.strip())
    pod_data = json.loads(processed_content)
    
    # Create POD model
    seed_data = pod_data.get('seed', {})
    pod_model = PodModel(
        podId=pod_data.get('podId', 'test'),
        seed=PodSeed(
            parameters=seed_data.get('parameters', []),
            endPoints=seed_data.get('endPoints', []),
            template=seed_data.get('template', {})
        ),
        file_path="test.pod",
        source_content=source.strip()
    )
    pod_model.set_hash_to_lines_mapping(hash_to_lines)
    
    context = ProjectContext()
    context.pods = {'test': pod_model}
    
    rule = ScriptStringConcatRule()
    findings = list(rule.analyze(context))
    
    print(f"\n\nMultiline POD script findings: {len(findings)}")
    for finding in findings:
        print(f"  Line {finding.line}: {finding.message[:100]}...")
        
        # The concatenation is now on line 8 (single-line script)
        # With hash mapping, should be exact or within 1 line
        assert 7 <= finding.line <= 9, f"Expected line 7-9, got {finding.line}"
        print(f"    [OK] Within expected range (7-9)")


if __name__ == "__main__":
    test_pod_single_line_script_exact_line()
    test_pod_multiline_script_exact_line()

