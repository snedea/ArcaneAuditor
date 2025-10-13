"""Cyclomatic complexity detection logic for ScriptComplexityRule."""

from typing import Generator, Dict, Any
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class CyclomaticComplexityDetector(ScriptDetector):
    """Detects excessive cyclomatic complexity in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        self.max_complexity = 10
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect excessive cyclomatic complexity in the AST."""
        # Find all top-level functions and check each separately
        functions = list(self._find_top_level_functions(ast))
        
        for func_info in functions:
            func_name = func_info['name']
            func_node = func_info['node']
            
            complexity_info = self._analyze_ast_complexity(func_node)
            complexity = complexity_info['complexity']
            
            if complexity > self.max_complexity:
                relative_line = complexity_info.get('line', 1) or 1
                line_number = self.line_offset + relative_line - 1
                
                message = f"Function '{func_name}' in '{field_name}' has complexity of {complexity} (max recommended: {self.max_complexity}). Consider refactoring."
                
                yield Violation(
                    message=message,
                    line=line_number
                )
        
        # Only check procedural code if there are NO top-level functions
        # (i.e., pure procedural scripts like onLoad/onSend)
        if not functions:
            complexity_info = self._analyze_ast_complexity(ast)
            complexity = complexity_info['complexity']
            
            if complexity > self.max_complexity:
                relative_line = complexity_info.get('line', 1) or 1
                line_number = self.line_offset + relative_line - 1
                
                message = f"File section '{field_name}' has complexity of {complexity} (max recommended: {self.max_complexity}). Consider refactoring."
                
                yield Violation(
                    message=message,
                    line=line_number
                )
    
    def _find_top_level_functions(self, ast: Tree) -> Generator[Dict[str, Any], None, None]:
        """Find all top-level functions (not nested inside other functions)."""
        # Look for variable statements that contain function expressions
        for var_stmt in ast.find_data('variable_statement'):
            # Check if this is a top-level statement (not inside another function)
            if self._is_top_level_node(var_stmt, ast):
                # Extract function name and node
                for var_decl in var_stmt.find_data('variable_declaration'):
                    func_name = None
                    func_node = None
                    
                    # Get variable name (function name)
                    if hasattr(var_decl, 'children') and len(var_decl.children) > 0:
                        var_name_token = var_decl.children[0]
                        if hasattr(var_name_token, 'value'):
                            func_name = var_name_token.value
                    
                    # Check if it's a function expression
                    for child in var_decl.children:
                        if hasattr(child, 'data') and child.data == 'function_expression':
                            func_node = child
                            break
                    
                    if func_name and func_node:
                        yield {
                            'name': func_name,
                            'node': func_node
                        }
    
    def _is_top_level_node(self, node: Tree, root: Tree) -> bool:
        """Check if a node is at the top level (not inside a function)."""
        # For simplicity, check if the node is a direct child of root or within a few levels
        # A more robust implementation would track parent nodes during traversal
        # For now, assume all variable_statement nodes at the root level are top-level
        return True  # Simplified - assumes we're not analyzing nested functions separately
    
    def _analyze_procedural_complexity(self, ast: Tree) -> int:
        """Analyze complexity of procedural code (code not inside functions)."""
        # This is a simplified version - ideally we'd exclude function bodies
        # For now, we'll skip this check if there are top-level functions
        # since the complexity is already being checked per function
        
        # Count if statements, loops, etc. that are NOT inside function expressions
        procedural_complexity = 1  # Base complexity
        
        # Find all complexity-increasing constructs at top level
        for node in ast.iter_subtrees():
            if hasattr(node, 'data'):
                # Skip if this node is inside a function_expression
                if self._is_inside_function(node, ast):
                    continue
                
                if node.data in ['if_statement', 'while_statement', 'for_statement', 'do_statement']:
                    procedural_complexity += 1
                elif node.data in ['logical_and_expression', 'logical_or_expression', 'ternary_expression']:
                    procedural_complexity += 1
        
        return procedural_complexity
    
    def _is_inside_function(self, node: Tree, root: Tree) -> bool:
        """Check if a node is inside a function expression."""
        # Simplified check - in a full implementation, we'd track parent chain
        # For now, return False to include all nodes
        return False
    
    def _analyze_ast_complexity(self, node) -> Dict[str, Any]:
        """Analyze cyclomatic complexity in AST nodes."""
        complexity = 1  # Base complexity
        line = None
        
        if hasattr(node, 'data'):
            # Count complexity-increasing constructs
            if node.data in ['if_statement', 'while_statement', 'for_statement', 'do_statement']:
                complexity += 1
                # Get line number from the first token in the node
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'logical_and_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'logical_or_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'ternary_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
        
        # Recursively analyze children
        if hasattr(node, 'children'):
            for child in node.children:
                child_complexity = self._analyze_ast_complexity(child)
                complexity += child_complexity['complexity'] - 1  # Subtract 1 to avoid double-counting base complexity
                if child_complexity.get('line') and not line:
                    line = child_complexity['line']
        
        return {
            'complexity': complexity,
            'line': line
        }
