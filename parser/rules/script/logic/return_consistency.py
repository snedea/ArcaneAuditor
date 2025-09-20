from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, PODModel


class ScriptFunctionReturnConsistencyRule(Rule):
    """Validates that functions consistently return values (all paths return or none return)."""
    
    DESCRIPTION = "Ensures functions consistently return values (all paths return or none return)"
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
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_return_consistency(field_value, field_name, pmd_model.file_path, line_offset)

    def visit_pod(self, pod_model: PODModel):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_return_consistency(field_value, field_name, pod_model.file_path, line_offset)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for return consistency."""
        try:
            yield from self._check_return_consistency(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _check_return_consistency(self, script_content, field_name, file_path, line_offset=1):
        """Check for return consistency in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
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
        """Analyze a specific function for return consistency."""
        # Find the function body
        function_body = None
        if len(function_node.children) > 2:  # function has body
            function_body = function_node.children[2]
        
        if function_body:
            return_analysis = self._analyze_return_consistency(function_body)
            if return_analysis == 'inconsistent':
                violations.append({
                    'message': "Function has inconsistent return pattern - some paths return values, others don't",
                    'line': function_node.line + line_offset - 1
                })
    
    def _analyze_return_consistency(self, node):
        """
        Analyze return consistency in a function body
        Returns: 'no_returns', 'all_returns', 'inconsistent'
        """
        if not hasattr(node, 'children'):
            return 'no_returns'
        
        has_returns = False
        has_non_returns = False
        
        for child in node.children:
            if hasattr(child, 'data'):
                if child.data == 'return_statement':
                    has_returns = True
                elif child.data in ['if_statement', 'while_statement', 'for_statement']:
                    # Check control flow statements for return consistency
                    child_analysis = self._analyze_control_flow_returns(child)
                    if child_analysis == 'inconsistent':
                        return 'inconsistent'
                    elif child_analysis == 'has_returns':
                        has_returns = True
                    elif child_analysis == 'has_non_returns':
                        has_non_returns = True
                else:
                    # Other statements that don't return
                    has_non_returns = True
        
        # Determine consistency
        if has_returns and has_non_returns:
            return 'inconsistent'
        elif has_returns:
            return 'all_returns'
        else:
            return 'no_returns'
    
    def _analyze_control_flow_returns(self, node):
        """Analyze return consistency in control flow statements"""
        if node.data == 'if_statement':
            # Check if-else consistency
            has_return_in_if = False
            has_return_in_else = False
            
            # Check if block
            if len(node.children) > 1:
                if_analysis = self._analyze_return_consistency(node.children[1])
                if if_analysis in ['has_returns', 'all_returns']:
                    has_return_in_if = True
            
            # Check else block if it exists
            if len(node.children) > 2:
                else_analysis = self._analyze_return_consistency(node.children[2])
                if else_analysis in ['has_returns', 'all_returns']:
                    has_return_in_else = True
            
            # If one branch returns and other doesn't, it's inconsistent
            if has_return_in_if and not has_return_in_else:
                return 'inconsistent'
            elif has_return_in_else and not has_return_in_if:
                return 'inconsistent'
            elif has_return_in_if or has_return_in_else:
                return 'has_returns'
            else:
                return 'no_returns'
        
        # For other control flow, just check if they contain returns
        return self._analyze_return_consistency(node)
