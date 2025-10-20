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
        # Find all functions and analyze each one independently
        functions = self._find_all_functions(ast)
        
        for func_name, func_info in functions.items():
            # Analyze nesting levels within this specific function
            nesting_info = self._analyze_function_nesting(func_info['body'], 0)
            max_nesting_found = nesting_info['max_nesting']
            
            if max_nesting_found > self.max_nesting:
                # Get line number from the function declaration
                line_number = func_info['line']
                
                yield Violation(
                    message=f"Function '{func_name}' has {max_nesting_found} nesting levels (max recommended: {self.max_nesting}). Consider refactoring.",
                    line=line_number
                )
        
        # Also check procedural code (code not inside any function)
        procedural_nesting = self._analyze_procedural_nesting(ast)
        if procedural_nesting['max_nesting'] > self.max_nesting:
            line_number = procedural_nesting.get('line', 1)
            yield Violation(
                message=f"File section '{field_name}' has {procedural_nesting['max_nesting']} nesting levels (max recommended: {self.max_nesting}). Consider refactoring.",
                line=line_number
            )
    
    def _find_all_functions(self, ast: Tree) -> Dict[str, Dict[str, Any]]:
        """Find all function declarations in the AST."""
        functions = {}
        
        def traverse(node):
            if hasattr(node, 'data'):
                if node.data == 'variable_statement':
                    func_info = self._extract_function_info(node)
                    if func_info:
                        functions[func_info['name']] = func_info
            
            if hasattr(node, 'children'):
                for child in node.children:
                    traverse(child)
        
        traverse(ast)
        return functions
    
    def _analyze_function_nesting(self, function_body: Tree, current_depth: int) -> Dict[str, Any]:
        """Analyze nesting levels within a specific function body."""
        return self._analyze_nesting_recursive(function_body, current_depth)
    
    def _analyze_procedural_nesting(self, ast: Tree) -> Dict[str, Any]:
        """Analyze nesting levels in procedural code (not inside functions)."""
        max_nesting = 0
        max_nesting_line = None
        
        def traverse(node, depth=0):
            nonlocal max_nesting, max_nesting_line
            
            if hasattr(node, 'data'):
                # Skip function declarations - we handle those separately
                if node.data == 'variable_statement':
                    func_info = self._extract_function_info(node)
                    if func_info:
                        return  # Skip this node and its children
                
                # Count control flow structures
                elif node.data in ['if_statement', 'while_statement', 'for_statement', 'for_var_statement', 'do_statement']:
                    depth += 1
                    if depth > max_nesting:
                        max_nesting = depth
                        max_nesting_line = self.get_line_from_tree_node(node)
            
            if hasattr(node, 'children'):
                for child in node.children:
                    traverse(child, depth)
        
        traverse(ast)
        return {
            'max_nesting': max_nesting,
            'line': max_nesting_line
        }
    
    def _analyze_nesting_recursive(self, node, current_depth: int) -> Dict[str, Any]:
        """Analyze nesting levels in AST nodes recursively."""
        max_nesting = current_depth
        max_nesting_line = None
        
        # Get line number from the current node
        current_line = self.get_line_from_tree_node(node)
        
        # Check if this is a control flow structure
        if hasattr(node, 'data'):
            if node.data in ['if_statement', 'while_statement', 'for_statement', 'for_var_statement', 'do_statement']:
                # Control flow structures add nesting
                current_depth += 1
                if current_depth > max_nesting:
                    max_nesting = current_depth
                    max_nesting_line = current_line
        
        # Recursively analyze children
        if hasattr(node, 'children'):
            for child in node.children:
                child_result = self._analyze_nesting_recursive(child, current_depth)
                if child_result['max_nesting'] > max_nesting:
                    max_nesting = child_result['max_nesting']
                    max_nesting_line = child_result['line']
        
        return {
            'max_nesting': max_nesting,
            'line': max_nesting_line
        }
    
    def _extract_function_info(self, var_stmt: Tree) -> Dict[str, Any]:
        """Extract function name, line, and body from a variable statement."""
        try:
            # Find variable declaration
            var_decl = None
            for child in var_stmt.children:
                if hasattr(child, 'data') and child.data == 'variable_declaration':
                    var_decl = child
                    break
            
            if not var_decl or not var_decl.children:
                return None
            
            # Extract function name
            func_name_token = var_decl.children[0]
            if not hasattr(func_name_token, 'value'):
                return None
            func_name = func_name_token.value
            
            # Find function expression
            func_body = None
            line = None
            for child in var_decl.children:
                if hasattr(child, 'data') and child.data == 'function_expression':
                    func_body = child
                    # Extract line number from function token
                    line = self.get_line_from_tree_node(child)
                    break
            
            # Only return function info if we actually found a function expression
            if func_body is None:
                return None
            
            return {
                'name': func_name,
                'line': line,
                'body': func_body
            }
        except (AttributeError, IndexError) as e:
            return None