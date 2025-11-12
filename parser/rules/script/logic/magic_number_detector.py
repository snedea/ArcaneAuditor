"""Magic number detection logic for ScriptMagicNumberRule."""

from typing import Generator, List, Optional
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class MagicNumberDetector(ScriptDetector):
    """Detects magic numbers in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1, source_text: str = ""):
        super().__init__(file_path, line_offset, source_text)
        # Define allowed numbers - ONLY the sentinel values
        self.allowed_numbers = {0, 1, -1}
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect magic numbers in the AST."""
        findings = []
        self._visit_node(ast, field_name, findings, ast)
        
        for finding in findings:
            yield Violation(
                message=finding['message'],
                line=finding['line']
            )

    
    def _visit_node(self, node, field_name: str, findings: List[dict], ast: Tree, parent=None):
        """Recursively visit AST nodes to find magic numbers."""
        # Check if the current node is a numeric literal
        if hasattr(node, 'data') and node.data == 'literal_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                try:
                    # Try to parse the value as a number
                    value = node.children[0].value
                    if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        number = int(value)
                        
                        # Check if this is a magic number
                        is_magic = number not in self.allowed_numbers
                        
                        if is_magic:
                            # Skip if this number is in a const variable declaration
                            if self._is_in_const_declaration(node, ast):
                                pass  # This is OK - number is being assigned to a named constant
                            else:
                                # Get line number from the token inside the literal_expression
                                line_number = self.get_line_number_from_token(node.children[0])
                                
                                # Check if this magic number is inside a function
                                function_name = self._get_function_name_for_node(node, ast)
                                
                                # Get code context for better error message
                                code_context = self._get_code_context(node, ast)
                                
                                if function_name:
                                    message = f"File section '{field_name}' contains magic number '{number}' in function '{function_name}': {code_context}. Consider using a named constant instead."
                                else:
                                    message = f"File section '{field_name}' contains magic number '{number}': {code_context}. Consider using a named constant instead."
                                
                                findings.append({
                                    'message': message,
                                    'line': line_number
                                })
                except (ValueError, AttributeError):
                    # Not a number, skip
                    pass
        
        # Recurse into children
        if hasattr(node, 'children'):
            for child in node.children:
                self._visit_node(child, field_name, findings, ast, parent=node)
    
    def _find_all_variable_statements(self, node: Tree) -> List[Tree]:
        """Manually find all variable_statement nodes in the tree."""
        results = []
        
        if hasattr(node, 'data') and node.data == 'variable_statement':
            results.append(node)
        
        if hasattr(node, 'children'):
            for child in node.children:
                if isinstance(child, Tree):
                    results.extend(self._find_all_variable_statements(child))
        
        return results

    def _is_in_const_declaration(self, literal_node: Tree, ast: Tree) -> bool:
        """Check if this numeric literal is being assigned to a const variable."""
        # Use manual traversal instead of find_data
        var_stmts = self._find_all_variable_statements(ast)
        
        for var_stmt in var_stmts:
            # Check if this is a const declaration
            if not self._is_const_statement(var_stmt):
                continue
            
            # Check if this literal is inside this statement
            if not self._is_descendant(var_stmt, literal_node):
                continue
            
            # It's in a const statement - check if it's a direct value
            if self._is_direct_value_in_const(var_stmt, literal_node):
                return True
        
        return False
    
    def _is_const_statement(self, var_stmt: Tree) -> bool:
        """Check if a variable_statement uses 'const'."""
        if not hasattr(var_stmt, 'children') or len(var_stmt.children) == 0:
            return False
        
        # First child should be the const/let/var token
        first_child = var_stmt.children[0]
        
        # Check type (case-insensitive to be safe)
        if hasattr(first_child, 'type') and first_child.type.upper() == 'CONST':
            return True
        
        # Fallback: check value (case-insensitive)
        if hasattr(first_child, 'value') and first_child.value.lower() == 'const':
            return True
        
        return False
    
    def _is_direct_value_in_const(self, var_stmt: Tree, literal_node: Tree) -> bool:
        """
        Check if the literal is a DIRECT assignment value (not in an expression).
        
        Returns True for:  const maxLength = 10;
        Returns False for: const result = value * 42;
        """
        # Find the variable_declaration inside this statement
        for child in var_stmt.children:
            if isinstance(child, Tree) and hasattr(child, 'data'):
                if child.data in ['variable_declaration', 'variable_declaration_list']:
                    if self._is_simple_literal_assignment(child, literal_node):
                        return True
        
        return False
    
    def _is_simple_literal_assignment(self, var_decl_node: Tree, literal_node: Tree) -> bool:
        """
        Check if the assignment is simply: identifier = literal (possibly wrapped)
        Not: identifier = expression_containing_literal
        """
        if not hasattr(var_decl_node, 'children'):
            return False
        
        # Handle variable_declaration_list (multiple declarations)
        if var_decl_node.data == 'variable_declaration_list':
            for child in var_decl_node.children:
                if isinstance(child, Tree):
                    if self._is_simple_literal_assignment(child, literal_node):
                        return True
            return False
        
        # For variable_declaration, structure is: [identifier, initializer]
        # Check if our literal is inside the initializer
        for child in var_decl_node.children:
            if isinstance(child, Tree) and self._is_descendant(child, literal_node):
                # Found it! But is it DIRECT or in an arithmetic expression?
                return self._is_simple_value(child, literal_node)
        
        return False
    
    def _is_simple_value(self, initializer: Tree, literal_node: Tree) -> bool:
        """
        Check if the literal is a simple value (not in an arithmetic expression).
        
        Allows: 
        - literal_expression: 70
        - arguments_expression: (70)  <- Grammar quirk workaround
        - parenthesized_expression: (70)
        
        Rejects: 
        - multiplicative_expression: 70 * 2
        - additive_expression: 70 + x
        - function_expression: function() { return 42; }  <- Literal inside function is NOT a direct const assignment
        - arrow_function_expression: () => { return 42; }
        """
        if not hasattr(initializer, 'data'):
            return False
        
        # If this IS our literal node, it's definitely simple
        if initializer is literal_node:
            return True
        
        # If we're inside a function, the literal is NOT a direct const assignment
        # Examples: const foo = function() { return 42; } - the 42 is magic, not a const value
        if initializer.data in ['function_expression', 'arrow_function_expression']:
            return False
        
        # These are "wrapper" nodes that don't change the value - recurse into them
        if initializer.data in ['literal_expression', 'arguments_expression', 'parenthesized_expression']:
            if hasattr(initializer, 'children'):
                for child in initializer.children:
                    if isinstance(child, Tree):
                        if self._is_simple_value(child, literal_node):
                            return True
            return False
        
        # These are arithmetic/logical expressions - the number is magic!
        if initializer.data in ['multiplicative_expression', 'additive_expression', 
                                'relational_expression', 'equality_expression',
                                'unary_expression', 'bitwise_expression']:
            return False
        
        # For unknown node types, recurse to be safe
        if hasattr(initializer, 'children'):
            for child in initializer.children:
                if isinstance(child, Tree):
                    if self._is_simple_value(child, literal_node):
                        return True
        
        return False
    
    def _is_descendant(self, ancestor: Tree, target: Tree) -> bool:
        """Check if target node is inside ancestor using object identity."""
        if ancestor is target:
            return True
        
        if hasattr(ancestor, 'children'):
            for child in ancestor.children:
                if isinstance(child, Tree):
                    if child is target:
                        return True
                    if self._is_descendant(child, target):
                        return True
        
        return False
    
    def _extract_code_context(self, literal_node: Tree, ast: Tree) -> str:
        """
        Extract readable code context around a magic number.
        
        For now, just return the magic number itself to avoid garbled output.
        This is much cleaner than the previous garbled text.
        """
        try:
            # Get the magic number value
            if hasattr(literal_node, 'children') and len(literal_node.children) > 0:
                child = literal_node.children[0]
                if hasattr(child, 'value'):
                    return str(child.value)
            
            return "magic number"
        except Exception:
            # If anything fails, return a safe fallback
            return "magic number"
    
    def _get_function_name_for_node(self, node: Tree, ast: Tree) -> Optional[str]:
        """Get the function name for a specific node using line-based matching."""
        # Get the line number of this node
        node_line = self.get_line_from_tree_node(node)
        
        # Find all variable statements and check which one contains this node
        for var_stmt in ast.find_data('variable_statement'):
            if len(var_stmt.children) > 1:
                var_declaration = var_stmt.children[1]
                if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                    # Check if this variable declaration contains a function expression
                    for child in var_declaration.children:
                        if hasattr(child, 'data') and child.data == 'function_expression':
                            # Check if this node is within this function by comparing line numbers
                            func_line = self.get_line_from_tree_node(child)
                            if node_line >= func_line:
                                # Check if the node is within the function's scope
                                if self._is_node_within_function(node, child, ast):
                                    # Found it! Get the variable name
                                    if len(var_declaration.children) > 0:
                                        var_name_token = var_declaration.children[0]
                                        if hasattr(var_name_token, 'value'):
                                            return var_name_token.value
        return None
    
    def _is_node_within_function(self, node: Tree, func_expr: Tree, ast: Tree) -> bool:
        """Check if a node is within the scope of a function expression."""
        # Simple heuristic: check if the node's line number is within the function's range
        node_line = self.get_line_from_tree_node(node)
        func_line = self.get_line_from_tree_node(func_expr)
        
        # Find the end of the function by looking for the next function or end of script
        func_end_line = self._find_function_end_line(func_expr, ast)
        
        return func_line <= node_line <= func_end_line
    
    def _find_function_end_line(self, func_expr: Tree, ast: Tree) -> int:
        """Find the approximate end line of a function expression."""
        # Get the function's starting line
        func_line = self.get_line_from_tree_node(func_expr)
        
        # Find all function expressions to determine boundaries
        all_functions = list(ast.find_data('function_expression'))
        func_index = all_functions.index(func_expr)
        
        # If this is the last function, use a large number
        if func_index == len(all_functions) - 1:
            return func_line + 100  # Arbitrary large number
        
        # Otherwise, use the next function's line as the boundary
        next_func = all_functions[func_index + 1]
        next_func_line = self.get_line_from_tree_node(next_func)
        return next_func_line - 1
    
    def _get_code_context(self, node: Tree, ast: Tree) -> str:
        """Get actual code context around a magic number using source text."""
        try:
            # Get the line number of the magic number WITHIN THE SCRIPT (1-based)
            # This is relative to the parsed script content, NOT the file
            magic_line_in_script = self.get_line_from_tree_node(node)
            
            # Convert from file line back to script-relative line
            # Formula: script_line = file_line - line_offset + 1
            script_line = magic_line_in_script - self.line_offset + 1
            
            # Use source text to get the actual line content
            if self.source_text:
                source_lines = self.source_text.split('\n')
                if 1 <= script_line <= len(source_lines):
                    actual_line = source_lines[script_line - 1].strip()
                    if actual_line:
                        return f"'{actual_line}'"
            
            # Fallback: try to reconstruct from AST
            return self._reconstruct_expression_from_ast(node)
        except Exception:
            return f"literal value"
    
    def _reconstruct_expression_from_ast(self, node: Tree) -> str:
        """Try to reconstruct a simple expression from the AST."""
        try:
            # Get the parent to understand the context
            parent = self._find_parent_node_in_tree(node)
            if parent and hasattr(parent, 'data'):
                if parent.data == 'additive_expression':
                    return f"arithmetic expression"
                elif parent.data == 'multiplicative_expression':
                    return f"arithmetic expression"
                elif parent.data == 'assignment_expression':
                    return f"assignment"
                elif parent.data == 'call_expression':
                    return f"function call"
                elif parent.data == 'member_expression':
                    return f"property access"
                elif parent.data == 'conditional_expression':
                    return f"conditional expression"
                elif parent.data == 'array_expression':
                    return f"array access"
                else:
                    return f"{parent.data}"
            
            return f"literal value"
        except Exception:
            return f"literal value"
    
    def _find_parent_node_in_tree(self, target_node: Tree) -> Optional[Tree]:
        """Find the immediate parent of a target node within its own tree."""
        # This is a simplified version that works within the current context
        # The full implementation would need access to the full AST
        return None
    
    def _find_parent_node(self, ast: Tree, target_node: Tree) -> Optional[Tree]:
        """Find the immediate parent of a target node."""
        def find_parent_recursive(node: Tree, target: Tree, parent: Optional[Tree] = None) -> Optional[Tree]:
            if node == target:
                return parent
            
            if isinstance(node, Tree):
                for child in node.children:
                    if isinstance(child, Tree):
                        result = find_parent_recursive(child, target, node)
                        if result is not None:
                            return result
            return None
        
        return find_parent_recursive(ast, target_node)