from ...base import Rule, Finding
from ....models import PMDModel, PodModel


class ScriptEmptyFunctionRule(Rule):
    """Validates that functions have actual implementation (not empty bodies)."""
    
    DESCRIPTION = "Ensures functions have actual implementation (not empty bodies)"
    SEVERITY = "SEVERE"

    def analyze(self, context):
        """Main entry point - analyze all PMD models, POD models, and standalone script files in the context."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model, context)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model, context)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)

    def visit_pmd(self, pmd_model: PMDModel, context=None):
        """Analyzes script fields in a PMD model."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model, context)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_empty_functions(field_value, field_name, pmd_model.file_path, line_offset, context)

    def visit_pod(self, pod_model: PodModel, context=None):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_empty_functions(field_value, field_name, pod_model.file_path, line_offset, context)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for empty functions."""
        try:
            yield from self._check_empty_functions(script_model.source, "script", script_model.file_path, 1, None)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _check_empty_functions(self, script_content, field_name, file_path, line_offset=1, context=None):
        """Check for empty functions in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all function_expression nodes in the AST
        violations = []
        self._check_functions(ast, violations, line_offset)
        
        for violation in violations:
            yield Finding(
                rule=self,
                message=violation['message'],
                line=violation['line'],
                column=1,
                file_path=file_path
            )
    
    def _check_functions(self, node, violations, line_offset):
        """Recursively check functions in AST nodes."""
        if hasattr(node, 'data') and node.data == 'function_expression':
            self._analyze_function(node, violations, line_offset)
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                self._check_functions(child, violations, line_offset)
    
    def _analyze_function(self, function_node, violations, line_offset):
        """Analyze a specific function for empty body."""
        # Find the function body
        function_body = None
        
        if len(function_node.children) == 2:
            # Empty function: children are [function, function_body]
            function_body = function_node.children[1]
        elif len(function_node.children) == 3:
            # Non-empty function: children are [function, params, source_elements]
            function_body = function_node.children[2]
        
        # Check if function body is empty
        if function_body and self._is_empty_function_body(function_body):
            violations.append({
                'message': "Function has empty body - implement the function or remove it",
                'line': function_node.meta.line + line_offset - 1
            })
    
    def _is_empty_function_body(self, function_body):
        """Check if function body is empty (only whitespace/comments)"""
        if not hasattr(function_body, 'children'):
            return True
        
        # If the function body is a direct statement (like return_statement), it's not empty
        if hasattr(function_body, 'data') and function_body.data in ['return_statement', 'expression_statement']:
            return False
        
        # If the function body has no children, it's empty
        if len(function_body.children) == 0:
            return True
        
        # Check if body has any meaningful statements
        for child in function_body.children:
            if hasattr(child, 'data'):
                # If we find any statement that's not just whitespace, it's not empty
                if child.data in ['statement', 'expression_statement', 'return_statement', 
                                'if_statement', 'while_statement', 'for_statement',
                                'assignment_expression', 'call_expression', 'identifier_expression',
                                'literal_expression', 'binary_expression', 'unary_expression']:
                    return False
        
        return True
