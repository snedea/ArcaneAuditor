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
            # Get line number using standardized method
            line_number = self.get_line_from_tree_node(func_info.get('node', ast))
            
            # Check if this long function is inside another function
            function_node = func_info.get('node')
            parent_function_name = None
            if function_node:
                parent_function_name = self.get_function_context_for_node(function_node, ast)
            
            if parent_function_name:
                message = f"File section '{field_name}' contains function '{func_info['name']}' in function '{parent_function_name}' with {func_info['lines']} lines (max recommended: {self.max_lines}). Consider breaking it into smaller functions."
            else:
                message = f"File section '{field_name}' contains function '{func_info['name']}' with {func_info['lines']} lines (max recommended: {self.max_lines}). Consider breaking it into smaller functions."
            
            yield Violation(
                message=message,
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
                                    'line': line_number,
                                    'node': node
                                })
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                child_functions = self._find_long_functions(child, max_lines)
                long_functions.extend(child_functions)
        
        return long_functions
    
    def _count_function_lines(self, func_body) -> int:
        """Count the number of code lines in a function body, excluding nested function bodies."""
        if not hasattr(func_body, 'children'):
            return 1
        
        counted_lines = set()
        
        def collect_lines(node, inside_nested_function=False):
            # Check if this node is a nested function definition
            is_nested_function = False
            if hasattr(node, 'data'):
                if node.data in ['function_expression', 'arrow_function', 'function_declaration']:
                    is_nested_function = True
                    # Don't traverse into nested functions at all
                    return
                
                # Also check for variable statements that contain function expressions
                if node.data == 'variable_statement':
                    # Check if this variable statement contains a function expression
                    if hasattr(node, 'children'):
                        for child in node.children:
                            if hasattr(child, 'data') and child.data == 'variable_declaration':
                                if hasattr(child, 'children') and len(child.children) >= 2:
                                    func_expr = child.children[1]
                                    if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                                        is_nested_function = True
                                        # Don't traverse into this variable statement at all
                                        return
            
            # Only count lines if we're not inside a nested function
            if not inside_nested_function:
                if hasattr(node, 'line') and node.line is not None:
                    # Skip newline tokens that might be associated with function declarations
                    if hasattr(node, 'type') and node.type == 'NEWLINE':
                        # Don't count newline tokens
                        pass
                    elif self._is_code_line(node):
                        counted_lines.add(node.line)
            
            # Recursively check children
            if hasattr(node, 'children'):
                for child in node.children:
                    collect_lines(child, inside_nested_function or is_nested_function)
        
        collect_lines(func_body)
        
        if counted_lines:
            return len(counted_lines)
        
        return len(func_body.children) if func_body.children else 1
    
    def _is_code_line(self, node: Tree) -> bool:
        """Check if a node represents actual code (not empty lines, comments, or template markers)."""
        # Check if node has type attribute (Lark tokens)
        if hasattr(node, 'type'):
            # Skip whitespace and comments (exclusion list approach)
            if node.type in ['WHITESPACE', 'COMMENT']:
                return False
            
            # Don't skip NEWLINE tokens - they represent actual line breaks that should be counted
            # The goal is to count procedural code lines, and NEWLINE tokens are part of that
            
            # Count actual code tokens (exclusion list approach)
            # Only exclude specific non-code types, everything else is code
            return True
        
        # Check if node has data attribute (Lark Tree nodes)
        if hasattr(node, 'data'):
            # Skip template markers
            if node.data in ['template_start', 'template_end']:
                return False
            
            # Skip comments
            if node.data in ['line_comment', 'block_comment']:
                return False
            
            # Skip empty statements
            if node.data == 'empty_statement':
                return False
            
            # Don't skip EOS tokens - they represent actual line breaks that should be counted
            # The goal is to count procedural code lines, and EOS tokens are part of that
            
            # Everything else is considered code
            return True
        
        return False
