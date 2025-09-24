from typing import Generator, Set
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


class ScriptUnusedScriptIncludesRule(Rule):
    """Validates that included script files are actually used in PMD files."""
    
    DESCRIPTION = "Ensures included script files are actually used (via script.function() calls)"
    SEVERITY = "WARNING"

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD files for unused script includes."""
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_script_includes(pmd_model)

    def _analyze_pmd_script_includes(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze a PMD file for unused script includes."""
        try:
            # Get included script files
            included_scripts = self._get_included_scripts(pmd_model)
            if not included_scripts:
                return
            
            # Get all script calls in the PMD
            script_calls = self._get_script_calls_in_pmd(pmd_model)
            
            # Find unused includes
            # Convert included scripts to base names for comparison
            included_base_names = set()
            for script_file in included_scripts:
                base_name = self._get_script_prefix(script_file)
                included_base_names.add(base_name)
            
            unused_scripts = included_base_names - script_calls
            
            for script_name in unused_scripts:
                # Find the original script file name for the error message
                original_script_file = None
                for script_file in included_scripts:
                    if self._get_script_prefix(script_file) == script_name:
                        original_script_file = script_file
                        break
                
                yield Finding(
                    rule=self,
                    message=f"Script file '{original_script_file or script_name}' is included but never used. Consider removing from include array or add calls like '{script_name}.functionName()'.",
                    line=self._get_include_line_number(pmd_model, original_script_file or script_name),
                    column=1,
                    file_path=pmd_model.file_path
                )
                
        except Exception as e:
            print(f"Warning: Failed to analyze script includes in {pmd_model.file_path}: {e}")

    def _get_included_scripts(self, pmd_model: PMDModel) -> Set[str]:
        """Extract script files from the include array."""
        included_scripts = set()
        
        if pmd_model.includes and pmd_model.includes.scripts:
            for script_file in pmd_model.includes.scripts:
                included_scripts.add(script_file)
        
        return included_scripts

    def _get_script_calls_in_pmd(self, pmd_model: PMDModel) -> Set[str]:
        """Find all script file calls in the PMD (script.function() pattern)."""
        script_calls = set()
        
        # Get all script fields in the PMD
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                script_calls.update(self._extract_script_calls_from_content(field_value))
        
        return script_calls

    def _extract_script_calls_from_content(self, script_content: str) -> Set[str]:
        """Extract script file calls from script content."""
        script_calls = set()
        
        try:
            ast = self._parse_script_content(script_content)
            if not ast:
                return script_calls
            
            # Look for member dot expressions that match script.function() pattern
            for member_expr in ast.find_data('member_dot_expression'):
                if len(member_expr.children) >= 2:
                    obj_node = member_expr.children[0]
                    
                    # Check if the object is an identifier (script name)
                    if hasattr(obj_node, 'data') and obj_node.data == 'identifier_expression':
                        if len(obj_node.children) > 0:
                            script_name = obj_node.children[0].value
                            
                            # Check if this looks like a script file name
                            if self._is_likely_script_name(script_name):
                                # Don't add .script extension - script calls use the base name
                                script_calls.add(script_name)
        
        except Exception:
            pass
        
        return script_calls

    def _is_likely_script_name(self, name: str) -> bool:
        """Check if a name is likely a script file reference."""
        # Script names are typically camelCase identifiers
        # Common patterns: util, helper, common, etc.
        common_script_names = {'util', 'helper', 'common', 'utils', 'helpers', 'bootstrapdata'}
        
        # Check if it's a known script name or follows script naming patterns
        return (
            name.lower() in common_script_names or
            name.endswith('.script') or
            (name.islower() and len(name) > 2) or  # Simple heuristic for script names
            (name[0].islower() and any(c.isupper() for c in name[1:]))  # camelCase pattern
        )

    def _get_script_prefix(self, script_file: str) -> str:
        """Get the prefix used for script calls (filename without .script extension)."""
        if script_file.endswith('.script'):
            return script_file[:-7]  # Remove .script extension
        return script_file

    def _get_include_line_number(self, pmd_model: PMDModel, script_name: str) -> int:
        """Get the line number where the script is included."""
        # This would ideally use line number utilities to find the exact line
        # For now, return a reasonable default
        try:
            from ...line_number_utils import LineNumberUtils
            return LineNumberUtils.find_field_line_number(pmd_model, 'include', script_name)
        except:
            return 1  # Fallback to line 1
