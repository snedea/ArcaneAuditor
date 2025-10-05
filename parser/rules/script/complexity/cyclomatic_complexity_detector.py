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
        # Analyze complexity using AST
        complexity_info = self._analyze_ast_complexity(ast)
        complexity = complexity_info['complexity']
        line = complexity_info.get('line', 1)
        
        if complexity > self.max_complexity:
            # Get line number from complexity info and apply offset
            relative_line = complexity_info.get('line', 1) or 1
            line_number = self.line_offset + relative_line - 1
            
            yield Violation(
                message=f"File section '{field_name}' has complexity of {complexity} (max recommended: {self.max_complexity}). Consider refactoring.",
                line=line_number
            )
    
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
