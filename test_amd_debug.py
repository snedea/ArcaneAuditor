#!/usr/bin/env python3
"""Test AMD finding to see what broke."""

from parser.rules.structure.validation.hardcoded_workday_api import HardCodedWorkdayAPIRule
from parser.models import AMDModel, ProjectContext

# Test with an AMD that has hardcoded URLs
rule = HardCodedWorkdayAPIRule()
amd_model = AMDModel(
    routes={},
    file_path='test.amd',
    source_content='''{
  "routes": {},
  "dataProviders": [
    {
      "key": "workdayApi",
      "value": "https://api.workday.com/hcm/v1"
    }
  ]
}''',
    dataProviders=[
        {
            "key": "workdayApi",
            "value": "https://api.workday.com/hcm/v1"
        }
    ]
)

context = ProjectContext()
context.pmds = {}
context.pods = {}
context.scripts = {}
context.amd = amd_model

print("Testing AMD analysis...")
findings = list(rule.analyze(context))
print(f"Found {len(findings)} findings")

for finding in findings:
    print(f'Rule: {finding.rule.ID if hasattr(finding.rule, "ID") else type(finding.rule).__name__}')
    print(f'Line {finding.line}: {finding.message}')
    print(f'File: {finding.file_path}')
    print('---')

