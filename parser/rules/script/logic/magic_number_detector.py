"""Magic number detection logic for ScriptMagicNumberRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class MagicNumberDetector(ScriptDetector):
    """Detects magic numbers in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
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
                                function_name = self.get_function_context_for_node(node, ast)
                                
                                if function_name:
                                    message = f"File section '{field_name}' contains magic number '{number}' in function '{function_name}'. Consider using a named constant instead."
                                else:
                                    message = f"File section '{field_name}' contains magic number '{number}'. Consider using a named constant instead."
                                
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
        """
        if not hasattr(initializer, 'data'):
            return False
        
        # If this IS our literal node, it's definitely simple
        if initializer is literal_node:
            return True
        
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