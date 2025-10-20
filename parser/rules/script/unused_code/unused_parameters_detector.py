"""Detector for unused function parameters in script code."""

from typing import Any, List
from ...script.shared import ScriptDetector, Violation
from ...common import ASTLineUtils


class UnusedParametersDetector(ScriptDetector):
    """Detects unused function parameters in script code."""

    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """
        Analyze AST and return list of unused parameter violations.
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Find all function expressions
        for function_node in ast.find_data('function_expression'):
            function_name = self._get_function_name(function_node, ast)
            parameters = self._get_function_parameters(function_node)
            function_body = self._get_function_body(function_node)
            
            if not function_body:
                continue
            
            # Find which parameters are used in the function body
            used_parameters = self._find_used_parameters(function_body)
            
            # Check for unused parameters
            for param_name in parameters:
                if param_name not in used_parameters:
                    # Get line number from the parameter token or function node
                    line_number = self._get_function_line_number(function_node)
                    violations.append(Violation(
                        message=f"Unused parameter '{param_name}' in function '{function_name}'",
                        line=line_number,
                        metadata={
                            'function_name': function_name,
                            'parameter_name': param_name
                        }
                    ))
        
        return violations

    def _get_function_name(self, node: Any, ast: Any) -> str:
        """Extract function name from a function expression node."""
        # In PMD Script, functions are anonymous and assigned to variables
        # We need to find the variable declaration that contains this function
        # Use the function context mapping to get the correct function name
        return self.get_function_context_for_node(node, ast) or "anonymous"

    def _get_function_parameters(self, node: Any) -> List[str]:
        """Extract parameter names from a function expression node."""
        parameters = []
        if hasattr(node, 'children') and len(node.children) >= 2:
            # Check if the second child is a parameter list or a single parameter
            params_node = node.children[1]
            
            # If it's a single parameter token
            if hasattr(params_node, 'value'):
                parameters.append(params_node.value)
            # If it's a parameter list node
            elif hasattr(params_node, 'children'):
                for param in params_node.children:
                    if hasattr(param, 'children') and param.children:
                        param_name = param.children[0]
                        if hasattr(param_name, 'value'):
                            parameters.append(param_name.value)
                    elif hasattr(param, 'value'):
                        parameters.append(param.value)
        return parameters

    def _get_function_body(self, node: Any) -> Any:
        """Extract function body from a function expression node."""
        if hasattr(node, 'children') and len(node.children) >= 3:
            return node.children[2]
        return None

    def _find_used_parameters(self, body_node: Any) -> set:
        """Find all parameter names used in the function body."""
        used_params = set()
        
        # Traverse the function body to find identifier expressions
        for node in body_node.find_data('identifier_expression'):
            if hasattr(node, 'children') and node.children:
                identifier = node.children[0]
                if hasattr(identifier, 'value'):
                    used_params.add(identifier.value)
        
        return used_params
    
    def _get_function_line_number(self, function_node: Any) -> int:
        """Get line number from function expression node using standardized method."""
        return self.get_line_from_tree_node(function_node)
