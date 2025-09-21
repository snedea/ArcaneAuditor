from ...base import Rule, Finding
from ....models import PMDModel, PodModel


class ScriptConsoleLogRule(Rule):
    """Validates that scripts don't contain console statements."""
    
    DESCRIPTION = "Ensures scripts don't contain console statements (production code)"
    SEVERITY = "SEVERE"

    def analyze(self, context):
        """Main entry point - analyze all PMD models, POD models, and standalone script files in the context."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_console_logs(field_value, field_name, pmd_model.file_path, line_offset)

    def visit_pod(self, pod_model: PodModel):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_console_logs(field_value, field_name, pod_model.file_path, line_offset)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for console log statements."""
        try:
            yield from self._check_console_logs(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _check_console_logs(self, script_content, field_name, file_path, line_offset=1):
        """Check for console statements in script content using AST parsing."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            return
        
        # Find all console method calls
        yield from self._find_console_calls(ast, field_name, file_path, line_offset)

    def _find_console_calls(self, ast, field_name, file_path, line_offset=1):
        """Find all console method calls in the AST."""
        # Find all member_dot_expression nodes (e.g., console.debug, console.info)
        member_expressions = ast.find_data('member_dot_expression')
        
        for member_expr in member_expressions:
            if len(member_expr.children) >= 2:
                object_node = member_expr.children[0]
                method_node = member_expr.children[1]
                
                # Check if it's a console method call
                if self._is_console_method_call(object_node, method_node):
                    method_name = self._extract_method_name(method_node)
                    line_number = self._get_line_number_from_node(member_expr) + line_offset - 1
                    
                    yield Finding(
                        rule=self,
                        message=f"File section '{field_name}' contains console.{method_name} statement. Remove debug statements from production code.",
                        line=line_number,
                        column=1,  # Column detection could be improved if needed
                        file_path=file_path
                    )

    def _is_console_method_call(self, object_node, method_node):
        """Check if the member expression is a console method call."""
        # Check if the object is 'console'
        if (hasattr(object_node, 'children') and 
            len(object_node.children) > 0 and
            hasattr(object_node.children[0], 'value') and
            object_node.children[0].value == 'console'):
            
            # Check if the method is a known console method
            method_name = self._extract_method_name(method_node)
            console_methods = ['info', 'warn', 'error', 'debug']
            
            return method_name in console_methods
        
        return False

    def _extract_method_name(self, method_node):
        """Extract the method name from the method node."""
        if hasattr(method_node, 'value'):
            return method_node.value
        elif hasattr(method_node, 'children') and len(method_node.children) > 0:
            child = method_node.children[0]
            if hasattr(child, 'value'):
                return child.value
        else:
            # The method node might be a token without children
            return str(method_node)
        return str(method_node)

    def _get_line_number_from_node(self, node):
        """Get the line number from an AST node."""
        if hasattr(node, 'line'):
            return node.line
        elif hasattr(node, 'children') and len(node.children) > 0:
            # Try to get line from first child
            child = node.children[0]
            if hasattr(child, 'line'):
                return child.line
        return 1  # Default fallback
