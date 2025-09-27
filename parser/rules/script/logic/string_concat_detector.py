"""String concatenation detection logic for ScriptStringConcatRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class StringConcatDetector(ScriptDetector):
    """Detects string concatenation using + operator in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect string concatenation using + operator in the AST."""
        # Find all addition expressions in the AST
        addition_expressions = ast.find_data('additive_expression')
        
        for add_expr in addition_expressions:
            if self._is_string_concatenation(add_expr):
                line_number = self.get_line_number(add_expr)
                
                # Extract the concatenation expression for better error message
                concat_text = self._extract_expression_text(add_expr)
                
                yield Violation(
                    message=f"File section '{field_name}' uses string concatenation with + operator: '{concat_text}'. Consider using PMD template strings with backticks and {{{{ }}}} syntax instead (e.g., `Hello {{{{name}}}}!`).",
                    line=line_number,
                    column=1
                )
    
    def _is_string_concatenation(self, add_expr: Tree) -> bool:
        """Check if an addition expression is actually string concatenation."""
        if not isinstance(add_expr, Tree) or add_expr.data != 'additive_expression':
            return False
        
        # Check if any operand involves strings
        # The AST structure shows that additive expressions can have multiple operands
        # when there are chained + operations like "a" + b + "c"
        for operand in add_expr.children:
            if self._involves_string(operand):
                return True
            # Recursively check if any operand is itself a string concatenation
            if isinstance(operand, Tree) and self._is_string_concatenation(operand):
                return True
        
        return False
    
    def _involves_string(self, node) -> bool:
        """Check if a node involves string operations."""
        if not isinstance(node, Tree):
            return False
        
        # Check if it's a string literal
        if node.data == 'literal_expression':
            if len(node.children) > 0:
                child = node.children[0]
                if hasattr(child, 'value') and isinstance(child.value, str) and child.value.startswith(('"', "'")):
                    return True
        
        # Check if it's a template literal (backticks)
        if node.data == 'literal_expression':
            if len(node.children) > 0:
                child = node.children[0]
                if hasattr(child, 'value') and isinstance(child.value, str) and child.value.startswith('`'):
                    return True
        
        # Check if it's a POD parameter (valid in POD context)
        if node.data == 'pod_parameter_expression':
            return True
        
        # Recursively check child nodes for string operations
        for child in node.children:
            if isinstance(child, Tree) and self._involves_string(child):
                return True
        
        return False
    
    def _extract_expression_text(self, node: Tree) -> str:
        """Extract readable text representation of an expression."""
        if not isinstance(node, Tree):
            return str(node)
        
        if node.data == 'additive_expression':
            if len(node.children) >= 3:
                left = self._extract_expression_text(node.children[0])
                operator = node.children[1].value if hasattr(node.children[1], 'value') else '+'
                right = self._extract_expression_text(node.children[2])
                return f"{left} {operator} {right}"
        
        elif node.data == 'literal_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        elif node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        elif node.data == 'pod_parameter_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        # For other node types, try to extract meaningful text
        text_parts = []
        for child in node.children:
            if hasattr(child, 'value'):
                text_parts.append(child.value)
            elif isinstance(child, Tree):
                text_parts.append(self._extract_expression_text(child))
        
        return ' '.join(text_parts) if text_parts else str(node.data)
