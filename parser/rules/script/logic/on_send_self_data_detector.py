"""Detector for anti-pattern 'self.data = {:}' in onSend scripts."""

from typing import Generator
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class OnSendSelfDataDetector(ScriptDetector):
    """Detects the anti-pattern 'self.data = {:}' in onSend scripts."""

    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """
        Detect anti-pattern in the AST.
        
        Looks for assignment expressions where:
        - Left side is member expression: self.data
        - Right side is empty object literal: {:}
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            Generator of Violation objects
        """
        # Find all assignment expressions in the AST
        for assignment_expr in ast.find_data('assignment_expression'):
            if self._is_self_data_empty_object_assignment(assignment_expr):
                line_number = self.get_line_from_tree_node(assignment_expr)
                
                yield Violation(
                    message=f"onSend script uses anti-pattern 'self.data = {{:}}'. This pattern should be avoided.",
                    line=line_number
                )
    
    def _is_self_data_empty_object_assignment(self, assignment_node: Tree) -> bool:
        """
        Check if this is an assignment of the form: self.data = {:}
        
        Args:
            assignment_node: AST node for assignment_expression
            
        Returns:
            True if this matches the anti-pattern
        """
        if not hasattr(assignment_node, 'children') or len(assignment_node.children) < 2:
            return False
        
        left_side = assignment_node.children[0]
        right_side = assignment_node.children[1]
        
        # Check if left side is "self.data"
        if not self._is_self_data_member_expression(left_side):
            return False
        
        # Check if right side is {:} (empty object literal)
        if not self._is_empty_object_literal(right_side):
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
    
    def _is_empty_object_literal(self, node: Tree) -> bool:
        """
        Check if node represents {:} (empty object literal).
        
        Args:
            node: AST node to check
            
        Returns:
            True if this is an empty object literal
        """
        if not hasattr(node, 'data'):
            return False
        
        # Check for various object literal node types
        if node.data in ['object_literal', 'curly_literal', 'curly_literal_expression']:
            # Check if it has no properties (empty object)
            if not hasattr(node, 'children') or len(node.children) == 0:
                return True
            
            # Check if all children are just structural tokens (like { and })
            # Empty object should have no property assignments
            for child in node.children:
                if hasattr(child, 'data') and 'property' in child.data:
                    return False
            
            return True
        
        return False

