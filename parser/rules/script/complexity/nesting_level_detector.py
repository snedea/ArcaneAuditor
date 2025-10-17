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
    
    def apply_settings(self, settings: dict):
        """
        Apply custom settings to the detector.
        
        Args:
            settings: Dictionary containing custom settings
        """
        if 'max_nesting_level' in settings:
            self.max_nesting = settings['max_nesting_level']
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect excessive nesting levels in the AST."""
        # Analyze nesting levels using AST
        nesting_info = self._analyze_ast_nesting(ast, 0)
        max_nesting_found = nesting_info['max_nesting']
        
        if max_nesting_found > self.max_nesting:
            # Get function context from the nesting analysis
            function_context = nesting_info.get('function_context')
            
            # Create a more descriptive message with function context
            if function_context:
                context_info = f" in function '{function_context}'"
            else:
                context_info = ""
            
            # Get line number from nesting info and apply offset
            relative_line = nesting_info.get('line', 1) or 1
            line_number = self.line_offset + relative_line - 1
            
            yield Violation(
                message=f"File section '{field_name}' has {max_nesting_found} nesting levels{context_info} (max recommended: {self.max_nesting}). Consider refactoring.",
                line=line_number
            )
    
    def _analyze_ast_nesting(self, node, current_depth: int) -> Dict[str, Any]:
        """Analyze nesting levels in AST nodes."""
        max_nesting = current_depth
        max_nesting_line = None
        function_context = None
        
        # Get line number from the current node
        current_line = None
        if hasattr(node, 'line') and node.line is not None:
            current_line = node.line
        elif hasattr(node, 'children') and len(node.children) > 0:
            # Look for the first token with a line number
            for child in node.children:
                if hasattr(child, 'line') and child.line is not None:
                    current_line = child.line
                    break
        
        # Check if this is a function expression
        if hasattr(node, 'data'):
            if node.data == 'function_expression':
                # Function expressions don't add nesting depth - only their bodies do
                # The nesting depth will be determined by control flow structures inside the function
                pass
            elif node.data == 'variable_declaration':
                # Extract function name from variable declaration (const myFunc = function() {...})
                if len(node.children) >= 2:
                    var_name = node.children[0]
                    if hasattr(var_name, 'value'):
                        function_context = var_name.value
            
            elif node.data in ['if_statement', 'while_statement', 'for_statement', 'for_var_statement', 'do_statement']:
                # Control flow structures add nesting
                current_depth += 1
                if current_depth > max_nesting:
                    max_nesting = current_depth
                    max_nesting_line = current_line
        
        # Recursively analyze children
        if hasattr(node, 'children'):
            for child in node.children:
                child_result = self._analyze_ast_nesting(child, current_depth)
                if child_result['max_nesting'] > max_nesting:
                    max_nesting = child_result['max_nesting']
                    max_nesting_line = child_result['line']
                if child_result['function_context'] and not function_context:
                    function_context = child_result['function_context']
        
        return {
            'max_nesting': max_nesting,
            'function_context': function_context,
            'line': max_nesting_line
        }
