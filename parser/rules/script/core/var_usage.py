from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, ScriptModel


class ScriptVarUsageRule(Rule):
    """Validates that scripts use 'let' or 'const' instead of 'var'."""
    
    DESCRIPTION = "Ensures scripts use 'let' or 'const' instead of 'var' (best practice)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models and standalone script files in the context."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_var_usage(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_var_usage(self, script_content, field_name, file_path, line_offset=1):
        """Check for use of 'var' in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all variable_statement nodes in the AST
        var_statements = ast.find_data('variable_statement')
        for var_stmt in var_statements:
            # Check if the variable statement uses VAR keyword
            if len(var_stmt.children) > 0 and hasattr(var_stmt.children[0], 'type') and var_stmt.children[0].type == 'VAR':
                # Get the variable declaration (second child)
                var_declaration = var_stmt.children[1]
                if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                        var_name = var_declaration.children[0].value
                        # Get line number from the VAR token (first child)
                        relative_line = getattr(var_stmt.children[0], 'line', 1) or 1
                        line_number = line_offset + relative_line - 1
                        
                        yield Finding(
                            rule=self,
                            message=f"File section '{field_name}' uses 'var' declaration for variable '{var_name}'. Consider using 'let' or 'const' instead.",
                            line=line_number,
                            column=1,
                            file_path=file_path
                        )

    def _analyze_script_file(self, script_model: ScriptModel) -> Generator[Finding, None, None]:
        """Analyze standalone script files for var usage."""
        try:
            yield from self._check_var_usage(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")
