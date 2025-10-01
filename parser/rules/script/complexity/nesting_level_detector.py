"""Nesting level detection logic for ScriptNestingLevelRule."""

from typing import Generator, Dict, Any
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class NestingLevelDetector(ScriptDetector):
    """Detects excessive nesting levels in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        self.max_nesting = 4
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect excessive nesting levels in the AST."""
        # Analyze nesting levels using AST
        nesting_info = self._analyze_ast_nesting(ast, 0)
        max_nesting_found = nesting_info['max_nesting']
        function_context = nesting_info['function_context']
        
        if max_nesting_found > self.max_nesting:
            # Create a more descriptive message with function context
            if function_context:
                context_info = f" in function '{function_context}'"
            else:
                context_info = ""
            
            # Use line_offset as base, add relative line if available
            relative_line = nesting_info.get('line', 1) or 1
            line_number = self.line_offset + relative_line - 1
            
            yield Violation(
                message=f"File section '{field_name}' has {max_nesting_found} nesting levels{context_info} (max recommended: {self.max_nesting}). Consider refactoring.",
                line=line_number
            )
    
    def _analyze_ast_nesting(self, node, current_depth: int) -> Dict[str, Any]:
        """Analyze nesting levels in AST nodes."""
        max_nesting = current_depth
        function_context = None
        
        # Check if this is a function expression
        if hasattr(node, 'data'):
            if node.data == 'function_expression':
                # Extract function name if available
                if len(node.children) > 0 and hasattr(node.children[0], 'type') and node.children[0].type == 'FUNCTION':
                    if len(node.children) > 1 and hasattr(node.children[1], 'value'):
                        function_context = node.children[1].value
                # Function body adds one nesting level
                current_depth += 1
                max_nesting = max(max_nesting, current_depth)
            
            elif node.data in ['block', 'if_statement', 'while_statement', 'for_statement', 'for_var_statement', 'do_statement']:
                # Control flow structures add nesting
                current_depth += 1
                max_nesting = max(max_nesting, current_depth)
        
        # Recursively analyze children
        if hasattr(node, 'children'):
            for child in node.children:
                child_result = self._analyze_ast_nesting(child, current_depth)
                max_nesting = max(max_nesting, child_result['max_nesting'])
                if child_result['function_context'] and not function_context:
                    function_context = child_result['function_context']
        
        # Get line number from the first token in the node
        line_number = None
        if hasattr(node, 'children') and len(node.children) > 0:
            # Look for the first token with a line number
            for child in node.children:
                if hasattr(child, 'line') and child.line is not None:
                    line_number = child.line
                    break
        
        return {
            'max_nesting': max_nesting,
            'function_context': function_context,
            'line': line_number
        }
