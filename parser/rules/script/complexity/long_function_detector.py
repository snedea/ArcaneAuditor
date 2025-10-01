"""Long function detection logic for ScriptLongFunctionRule."""

from typing import Generator, Dict, Any, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class LongFunctionDetector(ScriptDetector):
    """Detects functions that exceed maximum line count."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        self.max_lines = 50
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect functions that exceed maximum line count in the AST."""
        long_functions = self._find_long_functions(ast, self.max_lines)
        
        for func_info in long_functions:
            # Use line_offset as base, add relative line if available
            relative_line = func_info.get('line', 1) or 1
            line_number = self.line_offset + relative_line - 1
            
            yield Violation(
                message=f"File section '{field_name}' contains function '{func_info['name']}' with {func_info['lines']} lines (max recommended: {self.max_lines}). Consider breaking it into smaller functions.",
                line=line_number
            )
    
    def _find_long_functions(self, node, max_lines: int) -> List[Dict[str, Any]]:
        """Find functions that exceed the maximum line count."""
        long_functions = []
        
        if hasattr(node, 'data'):
            if node.data == 'variable_declaration':
                # Check if this variable declaration contains a function expression
                if len(node.children) >= 2:
                    var_name = node.children[0].value if hasattr(node.children[0], 'value') else "unknown"
                    func_expr = node.children[1]
                    
                    if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                        # Find function body
                        func_body = None
                        for child in func_expr.children:
                            if hasattr(child, 'data') and child.data == 'source_elements':
                                func_body = child
                                break
                        
                        if func_body:
                            line_count = self._count_function_lines(func_body)
                            if line_count > max_lines:
                                # Get line number from the first token in the node
                                line_number = None
                                if hasattr(node, 'children') and len(node.children) > 0:
                                    for child in node.children:
                                        if hasattr(child, 'line') and child.line is not None:
                                            line_number = child.line
                                            break
                                
                                long_functions.append({
                                    'name': var_name,
                                    'lines': line_count,
                                    'line': line_number
                                })
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                child_functions = self._find_long_functions(child, max_lines)
                long_functions.extend(child_functions)
        
        return long_functions
    
    def _count_function_lines(self, func_body) -> int:
        """Count the number of lines in a function body."""
        # Count the number of statements in the function body
        if hasattr(func_body, 'children'):
            return len(func_body.children)
        return 1
