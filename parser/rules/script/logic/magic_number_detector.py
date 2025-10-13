"""Magic number detection logic for ScriptMagicNumberRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class MagicNumberDetector(ScriptDetector):
    """Detects magic numbers in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        # Define allowed numbers and contexts
        self.allowed_numbers = {0, 1, -1}  # Common legitimate numbers
    
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
                            # Skip if this number is in a variable declaration (it's being named!)
                            if self._is_in_variable_declaration(node, parent, ast):
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
    
    def _is_in_variable_declaration(self, literal_node: Tree, parent: Tree, ast: Tree) -> bool:
        """
        Check if this numeric literal is the DIRECT value in a variable declaration (named constant).
        
        Allows: const maxLength = 10;  (10 is being named)
        Flags: const result = value * 42;  (42 is magic number in expression)
        """
        # Find all variable declarations in the AST
        for var_decl in ast.find_data('variable_declaration'):
            # Check if this literal is a DIRECT child (not in a nested expression)
            if self._is_direct_initializer(var_decl, literal_node):
                return True
        
        # Also check variable_statement nodes
        for var_stmt in ast.find_data('variable_statement'):
            if self._is_direct_initializer(var_stmt, literal_node):
                return True
        
        return False
    
    def _is_direct_initializer(self, var_decl: Tree, literal_node: Tree) -> bool:
        """
        Check if literal is the ONLY value being assigned (not part of an expression).
        
        Returns True for:  const maxLength = 10;
        Returns False for: const result = value * 42;
        Returns False for: for(let i = 0; i < 10; ...)  (10 in condition, not declaration)
        """
        # Variable declaration structure: [identifier, initializer]
        if not hasattr(var_decl, 'children') or len(var_decl.children) < 2:
            return False
        
        initializer = var_decl.children[1]
        
        # Use object identity (is) not equality (==) to ensure it's the exact same node
        # The literal_node itself is the direct initializer
        if initializer is literal_node:
            return True
        
        # The initializer should be a simple literal_expression (not an operator expression)
        # If it's multiplicative_expression, additive_expression, etc., the number is magic
        if hasattr(initializer, 'data'):
            # Only allow literal_expression as direct initializer
            if initializer.data == 'literal_expression':
                # Check if this literal_expression IS our literal_node (object identity)
                return initializer is literal_node
            else:
                # It's some kind of expression (multiplicative, additive, etc.)
                # The number is being used in a calculation, so it's magic
                return False
        
        return False
    
    def _is_descendant(self, ancestor: Tree, target: Tree) -> bool:
        """Check if target node is a descendant of ancestor node."""
        if ancestor == target:
            return True
        
        if hasattr(ancestor, 'children'):
            for child in ancestor.children:
                if isinstance(child, Tree):
                    if self._is_descendant(child, target):
                        return True
        
        return False
