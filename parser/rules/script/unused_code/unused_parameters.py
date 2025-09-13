from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


class ScriptUnusedFunctionParametersRule(Rule):
    """Validates that function parameters are actually used in the function body."""
    
    ID = "SCRIPT012"
    DESCRIPTION = "Ensures function parameters are actually used in the function body"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_unused_parameters(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_unused_parameters(self, script_content, field_name, file_path, line_offset=1):
        """Check for unused function parameters in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all function_expression nodes in the AST
        violations = []
        self._check_function_parameters(ast, violations, line_offset)
        
        for violation in violations:
            yield Finding(
                rule=self,
                message=violation['message'],
                line=violation['line'],
                column=1,
                file_path=file_path
            )
    
    def _check_function_parameters(self, node, violations, line_offset):
        """Recursively check function parameters in AST nodes."""
        if hasattr(node, 'data') and node.data == 'function_expression':
            self._analyze_function_parameters(node, violations, line_offset)
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                self._check_function_parameters(child, violations, line_offset)
    
    def _analyze_function_parameters(self, function_node, violations, line_offset):
        """Analyze a specific function for unused parameters."""
        # Find the function parameters
        params = []
        if len(function_node.children) > 1:  # function has parameters
            param_list = function_node.children[1]  # formal_parameter_list
            if hasattr(param_list, 'children'):
                for param in param_list.children:
                    if hasattr(param, 'data') and param.data == 'formal_parameter':
                        param_name = param.children[0].value
                        params.append((param_name, param))
        
        # Find the function body
        function_body = None
        if len(function_node.children) > 2:  # function has body
            function_body = function_node.children[2]
        
        # Check which parameters are used in the function body
        if function_body and params:
            used_params = set()
            self._collect_identifiers(function_body, used_params)
            
            # Check for unused parameters
            for param_name, param_node in params:
                if param_name not in used_params:
                    violations.append({
                        'message': f"Function parameter '{param_name}' is declared but never used",
                        'line': param_node.line + line_offset - 1
                    })
    
    def _collect_identifiers(self, node, identifiers):
        """Collect all identifier names from a node and its children"""
        if hasattr(node, 'value'):  # Leaf node with value
            identifiers.add(node.value)
        elif hasattr(node, 'children'):  # Node with children
            for child in node.children:
                self._collect_identifiers(child, identifiers)
