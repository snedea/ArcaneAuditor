from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


class ScriptLongFunctionRule(Rule):
    """Validates that functions don't exceed maximum line count."""
    
    DESCRIPTION = "Ensures functions don't exceed maximum line count (max 50 lines)"
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
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_long_functions(field_value, field_name, pmd_model.file_path, line_offset)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for function length."""
        try:
            yield from self._check_long_functions(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _check_long_functions(self, script_content, field_name, file_path, line_offset=1):
        """Check for overly long functions in script content."""
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        max_lines = 50
        long_functions = self._find_long_functions(ast, max_lines)
        
        for func_info in long_functions:
            # Use line_offset as base, add relative line if available
            relative_line = func_info.get('line', 1) or 1
            line_number = line_offset + relative_line - 1
            
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' contains function '{func_info['name']}' with {func_info['lines']} lines (max recommended: {max_lines}). Consider breaking it into smaller functions.",
                line=line_number,
                column=1,
                file_path=file_path
            )
    
    def _find_long_functions(self, node, max_lines):
        """Find functions that exceed the maximum line count."""
        long_functions = []
        
        if hasattr(node, 'data'):
            if node.data == 'variable_declaration':
                # Check if this variable declaration contains a function expression
                if len(node.children) >= 2:
                    var_name = node.children[0].value if hasattr(node.children[0], 'value') else "unknown"
                    func_expr = node.children[1]
                    
                    if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                        # Find function body
                        func_body = None
                        for child in func_expr.children:
                            if hasattr(child, 'data') and child.data == 'source_elements':
                                func_body = child
                                break
                        
                        if func_body:
                            line_count = self._count_function_lines(func_body)
                            if line_count > max_lines:
                                # Get line number from the first token in the node
                                line_number = None
                                if hasattr(node, 'children') and len(node.children) > 0:
                                    for child in node.children:
                                        if hasattr(child, 'line') and child.line is not None:
                                            line_number = child.line
                                            break
                                
                                long_functions.append({
                                    'name': var_name,
                                    'lines': line_count,
                                    'line': line_number
                                })
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                child_functions = self._find_long_functions(child, max_lines)
                long_functions.extend(child_functions)
        
        return long_functions
    
    def _count_function_lines(self, func_body):
        """Count the number of lines in a function body."""
        # Count the number of statements in the function body
        if hasattr(func_body, 'children'):
            return len(func_body.children)
        return 1
