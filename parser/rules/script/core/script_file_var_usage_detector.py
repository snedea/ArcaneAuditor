"""Script file variable usage detection logic for ScriptFileVarUsageRule."""

from typing import Generator, Set, Dict, Any
from lark import Tree
from ...script.shared import ScriptDetector
from ...common import Violation


class ScriptFileVarUsageDetector(ScriptDetector):
    """Detects variable usage patterns in standalone script files."""

    def __init__(self, file_path: str = "", line_offset: int = 1, config: Dict[str, Any] = None):
        super().__init__(file_path, line_offset)
        self.config = config or {}

    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect variable usage issues in standalone script files."""
        if ast is None:
            return
        
        # Extract declared variables and exported variables
        declared_vars = self._extract_declared_variables(ast)
        exported_vars = self._extract_exported_variables(ast)
        
        # Check for issues
        yield from self._check_var_usage_issues(declared_vars, exported_vars, ast)

    def _extract_declared_variables(self, ast) -> Dict[str, dict]:
        """Extract all variable declarations from the AST, marking their scope."""
        declared_vars = {}
        
        # Get top-level variable statements
        top_level_vars = self._get_top_level_variables(ast)
        declared_vars.update(top_level_vars)
        
        # Get function-scoped variable statements  
        function_vars = self._get_function_variables(ast)
        declared_vars.update(function_vars)
        
        return declared_vars

    def _get_top_level_variables(self, ast) -> Dict[str, dict]:
        """Get variables declared at the top level of the script."""
        top_level_vars = {}
        
        if hasattr(ast, 'children'):
            for stmt in ast.children:
                if hasattr(stmt, 'data') and stmt.data == 'variable_statement':
                    var_info = self._extract_var_info_from_statement(stmt, 'top-level')
                    if var_info:
                        top_level_vars[var_info['name']] = var_info['info']
        
        return top_level_vars

    def _get_function_variables(self, ast) -> Dict[str, dict]:
        """Get variables declared inside functions."""
        function_vars = {}
        
        # Find all variable statements that are NOT top-level
        all_var_statements = list(ast.find_data('variable_statement'))
        top_level_statements = ast.children if hasattr(ast, 'children') else []
        
        for var_stmt in all_var_statements:
            if var_stmt not in top_level_statements:
                var_info = self._extract_var_info_from_statement(var_stmt, 'function')
                if var_info:
                    function_vars[var_info['name']] = var_info['info']
        
        return function_vars

    def _extract_var_info_from_statement(self, var_stmt, scope) -> dict:
        """Extract variable information from a variable statement."""
        if len(var_stmt.children) >= 2:
            var_type = var_stmt.children[0].type if hasattr(var_stmt.children[0], 'type') else 'unknown'
            var_declaration = var_stmt.children[1]
            
            if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                if len(var_declaration.children) > 0:
                    var_name = var_declaration.children[0].value
                    line_number = self.get_line_number(var_stmt)
                    
                    return {
                        'name': var_name,
                        'info': {
                            'type': var_type,
                            'line': line_number,
                            'has_initializer': len(var_declaration.children) > 1,
                            'scope': scope
                        }
                    }
        return None

    def _extract_exported_variables(self, ast) -> Set[str]:
        """Extract variables that are exported in the final object literal."""
        exported_vars = set()
        
        # Look for object literal expressions (the export map)
        # In our grammar, object literals can be curly_literal_expression or curly_literal
        for node in ast.iter_subtrees():
            if hasattr(node, 'data') and node.data in ['object_literal', 'curly_literal_expression', 'curly_literal']:
                exported_vars.update(self._extract_object_literal_references(node))
        
        return exported_vars

    def _extract_object_literal_references(self, obj_literal) -> Set[str]:
        """Extract variable references from object literal values."""
        references = set()
        
        try:
            # Find property expression assignments in the object literal
            for node in obj_literal.iter_subtrees():
                if hasattr(node, 'data') and node.data == 'property_expression_assignment':
                    if len(node.children) >= 2:
                        # Get the value (second child) 
                        value_expr = node.children[1]
                        
                        # If the value is an identifier, it's a variable reference
                        if hasattr(value_expr, 'data') and value_expr.data == 'identifier_expression':
                            if len(value_expr.children) > 0:
                                var_name = value_expr.children[0].value
                                references.add(var_name)
            
            # Also handle direct identifier_expression nodes in curly_literal structure
            if hasattr(obj_literal, 'children'):
                for child in obj_literal.children:
                    if hasattr(child, 'data') and child.data == 'identifier_expression':
                        if len(child.children) > 0:
                            var_name = child.children[0].value
                            references.add(var_name)
                    
                    # Recursively search children for nested structures
                    if hasattr(child, 'children'):
                        for grandchild in child.children:
                            if hasattr(grandchild, 'data') and grandchild.data == 'identifier_expression':
                                if len(grandchild.children) > 0:
                                    var_name = grandchild.children[0].value
                                    references.add(var_name)
        except Exception as e:
            pass  # Silently handle parsing errors
        
        return references

    def _extract_internal_function_calls(self, ast) -> Set[str]:
        """Extract function calls that reference internally declared functions."""
        internal_calls = set()
        
        try:
            # Find all function call expressions (arguments_expression nodes)
            for call_expr in ast.find_data('arguments_expression'):
                if len(call_expr.children) > 0:
                    function_node = call_expr.children[0]
                    
                    # Check if it's a simple identifier (not a member access)
                    if hasattr(function_node, 'data') and function_node.data == 'identifier_expression':
                        if len(function_node.children) > 0:
                            function_name = function_node.children[0].value
                            internal_calls.add(function_name)
        except Exception:
            pass
        
        return internal_calls

    def _check_var_usage_issues(self, declared_vars: Dict[str, dict], exported_vars: Set[str], 
                               ast: Tree) -> Generator[Violation, None, None]:
        """Check for variable usage issues based on configuration."""
        
        # Separate top-level and function-scoped variables
        top_level_vars = {k: v for k, v in declared_vars.items() if v.get('scope') == 'top-level'}
        function_vars = {k: v for k, v in declared_vars.items() if v.get('scope') == 'function'}
        
        # Get internal function calls to identify helper functions
        internal_calls = self._extract_internal_function_calls(ast)
        
        # Issue 1: Top-level variables declared but not exported AND not used internally
        unexported_vars = set(top_level_vars.keys()) - exported_vars
        truly_unused_vars = unexported_vars - internal_calls
        
        for var_name in truly_unused_vars:
            var_info = top_level_vars[var_name]
            yield Violation(
                message=f"Top-level variable '{var_name}' is declared but neither exported nor used internally. Consider removing if unused.",
                line=var_info['line']
            )
