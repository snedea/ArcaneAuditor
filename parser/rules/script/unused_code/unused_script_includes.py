"""Script unused script includes rule using unified architecture."""

from typing import Generator, Set, Any
from ...script.shared import ScriptRuleBase
from ...base import Finding
from ....models import PMDModel
from .unused_script_includes_detector import UnusedScriptIncludesDetector


class ScriptUnusedScriptIncludesRule(ScriptRuleBase):
    """Validates that included script files are actually used in PMD files."""

    DESCRIPTION = "Ensures included script files are actually used (via script.function() calls)"
    SEVERITY = "WARNING"
    DETECTOR = UnusedScriptIncludesDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def analyze(self, context) -> Generator[Finding, None, None]:
        """Analyze PMD files for unused script includes."""
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_script_includes(pmd_model, context)

    def _analyze_pmd_script_includes(self, pmd_model: PMDModel, context=None) -> Generator[Finding, None, None]:
        """Analyze a PMD file for unused script includes."""
        try:
            # Get included script files
            included_scripts = self._get_included_scripts(pmd_model)
            if not included_scripts:
                return
            
            # Get all script calls in the PMD
            script_calls = self._get_script_calls_in_pmd(pmd_model, context)
            
            # Convert included scripts to base names for comparison
            included_base_names = set()
            for script_file in included_scripts:
                base_name = self._get_script_prefix(script_file)
                included_base_names.add(base_name)
            
            # Use detector to find violations
            detector = self.DETECTOR(pmd_model.file_path, 1, included_base_names, script_calls)
            violations = detector.detect(None, "script_includes")
            
            # Convert violations to findings
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=self._get_include_line_number(pmd_model, violation.metadata.get('script_name', '')),
                    column=1,
                    file_path=pmd_model.file_path
                )
                
        except Exception as e:
            print(f"Warning: Failed to analyze script includes in {pmd_model.file_path}: {e}")

    def _get_included_scripts(self, pmd_model: PMDModel) -> Set[str]:
        """Get included script files from PMD model."""
        included_scripts = set()
        
        if hasattr(pmd_model, 'includes') and pmd_model.includes and pmd_model.includes.scripts:
            for script_file in pmd_model.includes.scripts:
                if script_file:
                    included_scripts.add(script_file)
        
        return included_scripts

    def _get_script_calls_in_pmd(self, pmd_model: PMDModel, context=None) -> Set[str]:
        """Get all script calls in the PMD."""
        script_calls = set()
        
        # Analyze all script fields
        script_fields = self.find_script_fields(pmd_model, context)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                try:
                    ast = self._parse_script_content(field_value, context)
                    if ast:
                        # Find script calls (script.function() pattern)
                        for node in ast.find_data('arguments_expression'):
                            if self._is_script_call(node):
                                script_name = self._extract_script_name(node)
                                if script_name:
                                    script_calls.add(script_name)
                except Exception:
                    continue
        
        return script_calls

    def _is_script_call(self, node: Any) -> bool:
        """Check if a call expression is a script call."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return False
        
        # Check if it's a member expression (script.function)
        member_expr = node.children[0]
        if hasattr(member_expr, 'data') and member_expr.data == 'member_dot_expression':
            return True
        
        return False

    def _extract_script_name(self, node: Any) -> str:
        """Extract script name from a script call node."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return ""
        
        member_expr = node.children[0]
        if hasattr(member_expr, 'data') and member_expr.data == 'member_dot_expression':
            if hasattr(member_expr, 'children') and len(member_expr.children) >= 2:
                obj_node = member_expr.children[0]
                if hasattr(obj_node, 'data') and obj_node.data == 'identifier_expression':
                    if hasattr(obj_node, 'children') and obj_node.children:
                        identifier = obj_node.children[0]
                        if hasattr(identifier, 'value'):
                            return identifier.value
        
        return ""

    def _get_script_prefix(self, script_file: str) -> str:
        """Extract script prefix from script file name."""
        if not script_file:
            return ""
        
        # Remove .js or .script extension if present
        if script_file.endswith('.js'):
            script_file = script_file[:-3]
        elif script_file.endswith('.script'):
            script_file = script_file[:-7]
        
        # Return the base name
        return script_file

    def _get_include_line_number(self, pmd_model: PMDModel, script_name: str) -> int:
        """Get line number for script include."""
        # For now, return 1 - this could be enhanced to find the actual line
        return 1