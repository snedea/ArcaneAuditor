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
            'if_statement', 'while_statement', 'for_statement', 'do_statement',
            'logical_and_expression', 'logical_or_expression', 'ternary_expression'
        }
    
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
                line_number = self.line_offset + complexity_info.get('line', 1) - 1
                message = f"Function '{func_name}' in '{field_name}' has complexity of {complexity} (max recommended: {self.max_complexity}). Consider refactoring."
                
                yield Violation(
                    message=message,
                    line=line_number
                )
        
        # Generate violation for procedural code if no functions found
        if not analysis_results['functions'] and analysis_results['procedural_complexity'] > self.max_complexity:
            line_number = self.line_offset + analysis_results.get('procedural_line', 1) - 1
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
        stack = [(ast, False, None)]  # (node, is_inside_function, function_name)
        visited = set()
        
        while stack:
            node, is_inside_function, function_name = stack.pop()
            
            # Skip if already visited (circular reference protection)
            node_id = id(node)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            if hasattr(node, 'data'):
                # Check if this is a function declaration
                if node.data == 'variable_statement' and not is_inside_function:
                    func_info = self._extract_function_info(node)
                    if func_info:
                        functions[func_info['name']] = {
                            'complexity': 1,  # Base complexity
                            'line': func_info['line']
                        }
                        # Add function body to stack
                        if func_info['body']:
                            stack.append((func_info['body'], True, func_info['name']))
                        continue
                
                # Count complexity-increasing constructs
                if node.data in self.complexity_nodes:
                    if is_inside_function and function_name:
                        # Add to function complexity
                        functions[function_name]['complexity'] += 1
                    else:
                        # Add to procedural complexity
                        procedural_complexity += 1
                        if not procedural_line:
                            procedural_line = self._extract_line_number(node)
            
            # Add children to stack
            if hasattr(node, 'children'):
                # Add children in reverse order for forward processing
                for child in reversed(node.children):
                    if hasattr(child, 'data') or hasattr(child, 'children'):
                        stack.append((child, is_inside_function, function_name))
        
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
            
            return {
                'name': func_name,
                'line': line,
                'body': func_body
            }
        except (AttributeError, IndexError):
            return None
    
    def _extract_line_number(self, node: Tree) -> int:
        """Extract line number from a node efficiently."""
        if hasattr(node, 'line') and node.line is not None:
            return node.line
        
        # Search children for line number
        if hasattr(node, 'children'):
            for child in node.children:
                if hasattr(child, 'line') and child.line is not None:
                    return child.line
        
        return 1  # Default line number
