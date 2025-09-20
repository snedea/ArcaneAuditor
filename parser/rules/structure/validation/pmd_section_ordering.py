from typing import Generator, List, Dict, Any
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel
import json


class PMDSectionOrderingRule(Rule):
    """Validates that PMD file sections follow the configured ordering."""
    
    DESCRIPTION = "Ensures PMD file root-level sections follow consistent ordering for better readability"
    SEVERITY = "INFO"

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configurable section order."""
        # Default section order based on updated PMD standards
        default_order = [
            "id",
            "securityDomains",
            "include", 
            "script",
            "endPoints",
            "onSubmit",
            "outboundData",
            "onLoad",
            "presentation"
        ]
        
        self.section_order = config.get("section_order", default_order) if config else default_order

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD files for section ordering."""
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_section_order(pmd_model)

    def _analyze_pmd_section_order(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze a single PMD file for section ordering."""
        try:
            # Parse the PMD source to get the actual key order
            actual_order = self._extract_root_key_order(pmd_model)
            
            if not actual_order:
                return
            
            # Check ordering
            yield from self._check_section_ordering(actual_order, pmd_model)
            
        except Exception as e:
            print(f"Warning: Failed to analyze section ordering in {pmd_model.file_path}: {e}")

    def _extract_root_key_order(self, pmd_model: PMDModel) -> List[str]:
        """Extract the order of root-level keys from the PMD source."""
        try:
            # Parse the JSON to get the actual key order
            # Note: Python's json.loads() preserves order in Python 3.7+
            pmd_data = json.loads(pmd_model.source_content)
            return list(pmd_data.keys())
        except (json.JSONDecodeError, AttributeError):
            # Fallback: try to extract from raw content
            return self._extract_keys_from_raw_content(pmd_model.source_content)

    def _extract_keys_from_raw_content(self, content: str) -> List[str]:
        """Extract root-level keys from raw PMD content as fallback."""
        import re
        keys = []
        
        # Find all root-level keys (at the beginning of lines, accounting for whitespace)
        pattern = r'^\s*"([^"]+)"\s*:'
        
        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                key = match.group(1)
                if key not in keys:  # Avoid duplicates
                    keys.append(key)
        
        return keys

    def _check_section_ordering(self, actual_order: List[str], pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Check if the actual order matches the configured order."""
        
        # Get expected order for the keys that are actually present
        expected_order = self._get_expected_order_for_keys(actual_order)
        
        # Find ordering violations
        violations = self._find_ordering_violations(actual_order, expected_order)
        
        for violation in violations:
            yield Finding(
                rule=self,
                message=f"PMD section '{violation['key']}' is in wrong position. Expected order: {', '.join(expected_order)}. Current position: {violation['actual_pos']}, Expected position: {violation['expected_pos']}.",
                line=self._get_key_line_number(pmd_model, violation['key']),
                column=1,
                file_path=pmd_model.file_path
            )

    def _get_expected_order_for_keys(self, actual_keys: List[str]) -> List[str]:
        """Get the expected order for only the keys that are actually present."""
        expected_order = []
        
        # Add keys in the configured order if they exist in the actual PMD
        for key in self.section_order:
            if key in actual_keys:
                expected_order.append(key)
        
        # Add any keys that aren't in the configured order at the end
        for key in actual_keys:
            if key not in expected_order:
                expected_order.append(key)
        
        return expected_order

    def _find_ordering_violations(self, actual_order: List[str], expected_order: List[str]) -> List[Dict[str, Any]]:
        """Find keys that are in the wrong position."""
        violations = []
        
        for i, key in enumerate(actual_order):
            expected_index = expected_order.index(key) if key in expected_order else i
            
            if i != expected_index:
                violations.append({
                    'key': key,
                    'actual_pos': i + 1,
                    'expected_pos': expected_index + 1
                })
        
        return violations

    def _get_key_line_number(self, pmd_model: PMDModel, key: str) -> int:
        """Get the line number where a root-level key is defined."""
        try:
            from ...line_number_utils import LineNumberUtils
            return LineNumberUtils.find_field_line_number(pmd_model, key, None)
        except:
            # Fallback: search for the key in the source content
            if pmd_model.source_content:
                lines = pmd_model.source_content.split('\n')
                for i, line in enumerate(lines):
                    if f'"{key}"' in line and line.strip().startswith(f'"{key}"'):
                        return i + 1
            return 1  # Fallback to line 1
