"""Highly optimized cyclomatic complexity detection logic for ScriptComplexityRule."""

from typing import Generator, Dict, Any, List, Tuple
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class CyclomaticComplexityDetector(ScriptDetector):
    """Highly optimized detector for excessive cyclomatic complexity in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        self.max_complexity = 10
        
        # Pre-compile complexity-increasing node types for faster lookup
        self.complexity_nodes = {
            'if_statement', 'else_if_statement', 'while_statement', 'for_statement', 'do_statement',
            'logical_and_expression', 'logical_or_expression', 'ternary_expression'
        }
    
    def apply_settings(self, custom_settings: dict):
        """Apply custom settings from configuration."""
        if 'max_complexity' in custom_settings:
            max_complexity = custom_settings['max_complexity']
            # Ensure it's a valid integer within reasonable bounds
            if isinstance(max_complexity, (int, float)):
                max_complexity = int(max_complexity)
                if 1 <= max_complexity <= 50:
                    self.max_complexity = max_complexity
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect excessive cyclomatic complexity in the AST using optimized single-pass analysis."""
        if not ast:
            return
            
        # Single-pass analysis: find functions and analyze complexity in one traversal
        analysis_results = self._analyze_complexity_single_pass(ast)
        
        # Generate violations for functions
        for func_name, complexity_info in analysis_results['functions'].items():
            complexity = complexity_info['complexity']
            if complexity > self.max_complexity:
                # Get line number from the stored line in complexity_info
                line_number = complexity_info.get('line', 1)
                
                # Create appropriate message based on whether it's nested
                if complexity_info.get('is_nested', False):
                    parent_name = complexity_info.get('parent', 'unknown')
                    message = f"Inline function '{func_name.split('.')[-1]}' inside '{parent_name}' in '{field_name}' has complexity of {complexity} (max recommended: {self.max_complexity}). Consider refactoring."
                else:
                    message = f"Function '{func_name}' in '{field_name}' has complexity of {complexity} (max recommended: {self.max_complexity}). Consider refactoring."
                
                yield Violation(
                    message=message,
                    line=line_number
                )
        
        # Generate violation for procedural code if no functions found
        if not analysis_results['functions'] and analysis_results['procedural_complexity'] > self.max_complexity:
            # Get line number from the stored procedural line
            line_number = analysis_results.get('procedural_line', 1)
            message = f"File section '{field_name}' has complexity of {analysis_results['procedural_complexity']} (max recommended: {self.max_complexity}). Consider refactoring."
            
            yield Violation(
                message=message,
                line=line_number
            )
    
    def _analyze_complexity_single_pass(self, ast: Tree) -> Dict[str, Any]:
        """Analyze complexity in a single pass through the AST."""
        functions = {}
        procedural_complexity = 1  # Base complexity
        procedural_line = None
        
        
        # Use iterative traversal with a stack for better performance
        # Stack format: (node, function_stack) where function_stack is a list of function names
        stack = [(ast, [])]  # Start with empty function stack
        visited = set()
        
        while stack:
            node, function_stack = stack.pop()
            
            # Skip if already visited (circular reference protection)
            node_id = id(node)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            if hasattr(node, 'data'):
                # Check if this is a function declaration (variable_statement with function)
                if node.data == 'variable_statement':
                    func_info = self._extract_function_info(node)
                    if func_info:
                        # Create unique identifier for nested function
                        if len(function_stack) == 0:
                            func_name = func_info['name']
                            is_nested = False
                            parent_name = None
                        else:
                            parent_name = function_stack[-1]
                            func_name = f"{parent_name}.{func_info['name']}"
                            is_nested = True
                        
                        
                        functions[func_name] = {
                            'complexity': 1,  # Base complexity
                            'line': func_info['line'],
                            'is_nested': is_nested,
                            'parent': parent_name
                        }
                        # Add function body to stack with this function added to the stack
                        if func_info['body']:
                            new_stack = function_stack + [func_info['name']]
                            stack.append((func_info['body'], new_stack))
                        continue
                
                # Count complexity-increasing constructs
                if node.data in self.complexity_nodes:
                    line_num = self._extract_line_number(node)
                    current_func = function_stack[-1] if len(function_stack) > 0 else 'procedural'
                    
                    # Calculate complexity contribution based on node type
                    complexity_contribution = self._calculate_complexity_contribution(node)
                    
                    if len(function_stack) > 0:
                        # Add to the current function's complexity (the last one in the stack)
                        # Build the full function name from the stack
                        func_name = '.'.join(function_stack)
                        
                        # Ensure the function exists in our tracking
                        if func_name not in functions:
                            # This is a deeply nested function we haven't seen yet
                            functions[func_name] = {
                                'complexity': 1,  # Base complexity
                                'line': self._extract_line_number(node),
                                'is_nested': len(function_stack) > 1,
                                'parent': function_stack[-2] if len(function_stack) > 1 else None
                            }
                        
                        functions[func_name]['complexity'] += complexity_contribution
                    else:
                        # Add to procedural complexity
                        procedural_complexity += complexity_contribution
                        if not procedural_line:
                            procedural_line = self._extract_line_number(node)
            
            # Add children to stack
            if hasattr(node, 'children'):
                # Add children in reverse order for forward processing
                for child in reversed(node.children):
                    if hasattr(child, 'data') or hasattr(child, 'children'):
                        stack.append((child, function_stack))
        
        return {
            'functions': functions,
            'procedural_complexity': procedural_complexity,
            'procedural_line': procedural_line
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
                    line = self._extract_line_number(child)
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
    
    def _calculate_complexity_contribution(self, node: Tree) -> int:
        """Calculate the complexity contribution of a node based on its type and structure."""
        if node.data in ('logical_and_expression', 'logical_or_expression'):
            # For logical operators, count the actual number of operators
            # Number of operators = Number of children - 1
            if hasattr(node, 'children') and len(node.children) > 1:
                return len(node.children) - 1
            else:
                return 1  # Fallback if no children
        else:
            # For other complexity-increasing constructs (if, while, for, etc.), count as 1
            return 1
    
    def _extract_line_number(self, node: Tree) -> int:
        """Extract line number from a node using standardized calculation."""
        return self.get_line_from_tree_node(node)
