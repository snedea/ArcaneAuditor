"""Detector for anti-pattern 'self.data = {...}' in onSend scripts."""

from typing import Generator
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class OnSendSelfDataDetector(ScriptDetector):
    """Detects the anti-pattern of overwriting self.data with a new object in onSend scripts."""

    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """
        Detect anti-pattern in the AST.
        
        Looks for assignment expressions where:
        - Left side is member expression: self.data (not self.data.property)
        - Right side is any object literal: {:} or {foo: 'bar'}
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            Generator of Violation objects
        """
        # Find all assignment expressions in the AST
        for assignment_expr in ast.find_data('assignment_expression'):
            if self._is_self_data_object_assignment(assignment_expr):
                line_number = self.get_line_from_tree_node(assignment_expr)
                
                yield Violation(
                    message=f"onSend script uses 'self.data' as temporary storage by creating a new object. Use a local variable instead (let postData = {{...}}) for better code clarity.",
                    line=line_number
                )
    
    def _is_self_data_object_assignment(self, assignment_node: Tree) -> bool:
        """
        Check if this is an assignment of the form: self.data = <object>
        
        This includes both empty and populated objects:
        - self.data = {:}
        - self.data = {foo: 'bar'}
        
        But NOT property assignments:
        - self.data.foo = 'bar'  (this is OK in situations where Extend populated self.data, not the developer!)
        
        Args:
            assignment_node: AST node for assignment_expression
            
        Returns:
            True if this matches the anti-pattern
        """
        if not hasattr(assignment_node, 'children') or len(assignment_node.children) < 2:
            return False
        
        left_side = assignment_node.children[0]
        right_side = assignment_node.children[1]
        
        # Check if left side is "self.data" (NOT self.data.property)
        if not self._is_self_data_member_expression(left_side):
            return False
        
        # Check if right side is any object literal (empty or populated)
        if not self._is_object_literal(right_side):
            return False
        
        return True
    
    def _is_self_data_member_expression(self, node: Tree) -> bool:
        """
        Check if node represents 'self.data' member expression.
        
        Args:
            node: AST node to check
            
        Returns:
            True if this is self.data
        """
        if not hasattr(node, 'data') or node.data != 'member_dot_expression':
            return False
        
        if not hasattr(node, 'children') or len(node.children) < 2:
            return False
        
        # Get the object (should be 'self')
        obj_node = node.children[0]
        if not self._is_identifier_with_value(obj_node, 'self'):
            return False
        
        # Get the property (should be 'data')
        prop_node = node.children[1]
        if hasattr(prop_node, 'value'):
            return prop_node.value == 'data'
        elif hasattr(prop_node, 'data') and prop_node.data == 'identifier_expression':
            if len(prop_node.children) > 0 and hasattr(prop_node.children[0], 'value'):
                return prop_node.children[0].value == 'data'
        
        return False
    
    def _is_identifier_with_value(self, node: Tree, expected_value: str) -> bool:
        """
        Check if node is an identifier with a specific value.
        
        Args:
            node: AST node to check
            expected_value: The expected identifier value
            
        Returns:
            True if node is identifier with expected value
        """
        if not hasattr(node, 'data'):
            return False
        
        if node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value == expected_value
        
        return False
    
    def _is_object_literal(self, node: Tree) -> bool:
        """
        Check if node represents any object literal: {:} or {foo: 'bar'}.
        
        Args:
            node: AST node to check
            
        Returns:
            True if this is an object literal (empty or populated)
        """
        if not hasattr(node, 'data'):
            return False
        
        # Check for various object literal node types
        # This matches any object literal, regardless of whether it has properties
        if node.data in ['object_literal', 'curly_literal', 'curly_literal_expression']:
            return True
        
        return False

