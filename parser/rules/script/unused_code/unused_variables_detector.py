"""Detector for unused variables in script code."""

from typing import Any, List, Set, Dict
from ...script.shared import ScriptDetector, Violation
from ...common import ASTLineUtils


class UnusedVariableDetector(ScriptDetector):
    """Detects unused variables in script code with scope awareness."""

    def __init__(self, file_path: str = "", line_offset: int = 1, is_global_scope: bool = False, global_functions: Set[str] = None):
        """Initialize detector with file context and scope information."""
        super().__init__(file_path, line_offset)
        self.is_global_scope = is_global_scope
        self.global_functions = global_functions or set()

    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """
        Analyze AST and return list of unused variable violations.
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Analyze the script with scope awareness
        scope_analysis = self._analyze_script_scope(ast, self.is_global_scope, self.global_functions)
        
        # Check for unused variables in each scope
        for scope_info in scope_analysis['scopes']:
            scope_type = scope_info['type']
            scope_name = scope_info['name']
            declared_vars = scope_info['declared_vars']
            used_vars = scope_info['used_vars']
            
            # Check for unused variables in this scope
            for var_name, var_info in declared_vars.items():
                if var_name not in used_vars:
                    # Skip function declarations - they're handled by ScriptUnusedFunctionRule
                    if var_info.get('is_function', False):
                        continue
                    
                    # Skip variables that are used in other scopes (global scope variables)
                    if scope_type == 'global' and var_name in scope_analysis['global_used_vars']:
                        continue
                    
                    # Create violation with function name context
                    if scope_type == 'function':
                        message = f"Unused variable '{var_name}' in function '{scope_name}'"
                    else:
                        message = f"Unused variable '{var_name}' in {scope_type} scope"
                    
                    violations.append(Violation(
                        message=message,
                        line=self.get_line_from_tree_node(var_info['node']),
                        metadata={
                            'variable_name': var_name,
                            'scope_type': scope_type,
                            'scope_name': scope_name
                        }
                    ))
        
        return violations

    def _analyze_script_scope(self, ast: Any, is_global_scope: bool, global_functions: Set[str]) -> Dict:
        """Analyze script scope and variable usage."""
        scope_analysis = {
            'scopes': [],
            'global_used_vars': set()
        }
        
        # Find all scopes in the script
        scopes = self._find_scopes(ast, is_global_scope, global_functions)
        scope_analysis['scopes'] = scopes
        
        # Collect all variables used across all scopes
        for scope in scopes:
            scope_analysis['global_used_vars'].update(scope['used_vars'])
        
        return scope_analysis

    def _find_scopes(self, ast: Any, is_global_scope: bool, global_functions: Set[str]) -> List[Dict]:
        """Find all scopes in the script."""
        scopes = []
        
        # Global scope
        if is_global_scope:
            global_scope = self._analyze_scope(ast, 'global', 'global', global_functions)
            scopes.append(global_scope)
        
        # Function scopes - look for variable statements that contain function expressions
        for node in ast.find_data('variable_statement'):
            # Check if this variable statement contains a function expression
            function_expr = None
            function_name = None
            
            for child in node.children:
                if hasattr(child, 'data') and child.data == 'variable_declaration':
                    # Get the variable name (function name)
                    if len(child.children) > 0:
                        var_name_token = child.children[0]
                        if hasattr(var_name_token, 'value'):
                            function_name = var_name_token.value
                    
                    # Check if this variable declaration contains a function expression
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'function_expression':
                            function_expr = grandchild
                            break
            
            if function_expr and function_name:
                function_scope = self._analyze_scope(function_expr, 'function', function_name, global_functions)
                scopes.append(function_scope)
        
        return scopes

    def _analyze_scope(self, ast: Any, scope_type: str, scope_name: str, global_functions: Set[str]) -> Dict:
        """Analyze a specific scope for variable declarations and usage."""
        declared_vars = {}
        used_vars = set()
        
        if scope_type == 'global':
            # For global scope, only look for top-level variable statements
            # that are not inside function expressions
            for node in ast.find_data('variable_statement'):
                # Check if this variable statement is at the top level
                # (not inside a function_expression)
                if self._is_top_level_variable_statement(node, ast):
                    var_name = self._get_variable_name_from_statement(node)
                    if var_name:
                        # Check if this variable statement contains a function expression
                        is_function = self._contains_function_expression(node)
                        declared_vars[var_name] = {
                            'node': node,
                            'is_function': is_function
                        }
        else:
            # For function scope, look for variable statements within the function
            for node in ast.find_data('variable_statement'):
                var_name = self._get_variable_name_from_statement(node)
                if var_name:
                    declared_vars[var_name] = {
                        'node': node,
                        'is_function': False
                    }
        
        # Find function declarations within this scope
        for node in ast.find_data('function_expression'):
            func_name = self._get_function_name(node)
            if func_name:
                declared_vars[func_name] = {
                    'node': node,
                    'is_function': True
                }
        
        # Find variable usage
        for node in ast.find_data('identifier_expression'):
            var_name = self._get_identifier_name(node)
            if var_name:
                used_vars.add(var_name)
        
        # Add global functions to used vars (they're available in all scopes)
        used_vars.update(global_functions)
        
        return {
            'type': scope_type,
            'name': scope_name,
            'declared_vars': declared_vars,
            'used_vars': used_vars
        }

    def _contains_function_expression(self, node: Any) -> bool:
        """Check if a variable statement contains a function expression."""
        for child in node.children:
            if hasattr(child, 'data') and child.data == 'variable_declaration':
                for grandchild in child.children:
                    if hasattr(grandchild, 'data') and grandchild.data == 'function_expression':
                        return True
        return False

    def _is_top_level_variable_statement(self, node: Any, root_ast: Any) -> bool:
        """Check if a variable statement is at the top level (not inside a function)."""
        # For our simple test case, if the root is a variable_statement,
        # then this node is the root itself, so it's top-level
        if node == root_ast:
            return True
        
        # Check if this node is a direct child of the root
        for child in root_ast.children:
            if child == node:
                return True
        
        return False

    def _get_variable_name_from_statement(self, node: Any) -> str:
        """Extract variable name from a variable statement node."""
        if hasattr(node, 'children') and len(node.children) > 1:
            # The second child should be the variable_declaration
            var_decl_node = node.children[1]
            if hasattr(var_decl_node, 'children') and len(var_decl_node.children) > 0:
                var_name_token = var_decl_node.children[0]
                if hasattr(var_name_token, 'value'):
                    return var_name_token.value
        return ""

    def _get_variable_name(self, node: Any) -> str:
        """Extract variable name from a variable declaration node."""
        if hasattr(node, 'children') and node.children:
            var_node = node.children[0]
            if hasattr(var_node, 'children') and var_node.children:
                identifier = var_node.children[0]
                if hasattr(identifier, 'value'):
                    return identifier.value
        return ""

    def _get_function_name(self, node: Any) -> str:
        """Extract function name from a function expression node."""
        # The function name is not in the function_expression node itself,
        # but in the parent variable_declaration node. We need to traverse up
        # to find the variable declaration that contains this function.
        # For now, return empty string - function names will be handled differently
        return ""

    def _get_identifier_name(self, node: Any) -> str:
        """Extract identifier name from an identifier expression node."""
        if hasattr(node, 'children') and node.children:
            identifier = node.children[0]
            if hasattr(identifier, 'value'):
                return identifier.value
        return ""
