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
