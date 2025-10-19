"""Long function detection logic for ScriptLongFunctionRule."""

from typing import Generator, Dict, Any, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class LongFunctionDetector(ScriptDetector):
    """Detects functions that exceed maximum line count."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1, skip_comments: bool = False, skip_blank_lines: bool = False, source_text: str = ""):
        super().__init__(file_path, line_offset, source_text)
        self.max_lines = 50
        self.skip_comments = skip_comments
        self.skip_blank_lines = skip_blank_lines
        
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect functions that exceed maximum line count in the AST."""
        # Only analyze functions in locations where they can be globally accessible:
        # 1. PMD 'script' section (functions are available throughout the PMD file)
        # 2. Standalone .script files (functions are exported and reusable)
        # Skip embedded blocks (onLoad, onChange, onSend, etc.) where functions are local only
        if field_name and field_name != 'script':
            return
        
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
                            # Count lines from the ENTIRE variable declaration node, not just the function expression
                            # The function_expression node is incomplete - it doesn't include the return statement
                            # and closing brace. We need to count from the variable declaration node instead.
                            line_count = self._count_function_lines(node, var_name)
                            
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
    
    def _count_function_lines(self, func_expr, var_name="unknown") -> int:
        """
        Count lines using source text (ESLint approach).
        
        Gets the start and end line numbers from the AST, then counts
        the actual physical lines in the source text between them.
        """
        if not hasattr(func_expr, 'children'):
            return 1
        
        # Collect all line numbers from the AST to find min and max
        counted_lines = set()
        
        def collect_lines(node):
            """Recursively collect all line numbers from the AST."""
            if hasattr(node, 'line') and node.line is not None:
                if self._should_count_line(node):
                    counted_lines.add(node.line)
            
            if hasattr(node, 'children'):
                for child in node.children:
                    collect_lines(child)
        
        collect_lines(func_expr)
        
        if not counted_lines:
            return 1
        
        # Get the range of lines from the AST
        min_line = min(counted_lines)
        max_line = max(counted_lines)
        
        # Find closing brace, but limit search to actual source text length
        actual_end_line = self._find_closing_brace_from_start(min_line, max_line, var_name)
        
        # Ensure we don't go beyond the actual source text length
        max_source_line = len(self.source_text.split('\n'))
        if actual_end_line > max_source_line:
            actual_end_line = max_source_line

        # Use the shared helper to count physical lines from source text
        result = self.count_physical_lines(min_line, actual_end_line)
        
        return result
    
    def _find_closing_brace_from_start(self, func_start_line: int, last_ast_line: int, function_name: str = "") -> int:
        """Find the closing brace by counting from the function start."""
        if not self.source_text:
            return last_ast_line + 1
        
        source_lines = self.source_text.split('\n')
        
        # Start counting braces from the function declaration line
        brace_depth = 0
        start_idx = func_start_line - 1
        has_seen_opening_brace = False
        
        for line_idx in range(start_idx, len(source_lines)):
            line = source_lines[line_idx]
            
            # Count braces on this line
            open_braces = line.count('{')
            close_braces = line.count('}')
            
            # Track if we've seen an opening brace
            if open_braces > 0:
                has_seen_opening_brace = True
            
            # Update brace depth
            brace_depth += open_braces
            brace_depth -= close_braces
            
            # Once we close all braces AND we've seen an opening brace, we found the end
            if brace_depth == 0 and has_seen_opening_brace:
                return line_idx + 1
        
        return last_ast_line + 1
    
    def _should_count_line(self, node) -> bool:
        """
        Determine if a node's line should be counted based on skip flags.
        
        Args:
            node: AST node to check
            
        Returns:
            True if the line should be counted, False otherwise
        """
        # Check if node has type attribute (Lark tokens)
        if hasattr(node, 'type'):
            # Always skip whitespace tokens
            if node.type == 'WHITESPACE':
                return False
            
            # Skip comment tokens if flag is set
            if self.skip_comments and node.type == 'COMMENT':
                return False
            
            # Skip newline/blank line tokens if flag is set
            if self.skip_blank_lines and node.type in ['NEWLINE', 'NL']:
                return False
            
            return True
        
        # Check if node has data attribute (Lark Tree nodes)
        if hasattr(node, 'data'):
            # Skip comment nodes if flag is set
            if self.skip_comments and node.data in ['line_comment', 'block_comment', 'comment']:
                return False
            
            # Skip template markers (always)
            if node.data in ['template_start', 'template_end']:
                return False
            
            # Skip empty statements (always)
            if node.data == 'empty_statement':
                return False
            
            return True
        
        return True
