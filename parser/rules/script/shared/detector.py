"""Base detector class for script analysis."""

from abc import ABC, abstractmethod
from typing import Any, List
from lark import Tree
from .violation import Violation


class ScriptDetector(ABC):
    """Base class for script analysis detectors."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        """Initialize detector with file context."""
        self.file_path = file_path
        self.line_offset = line_offset
        # Cache for function context maps to avoid rebuilding for each violation
        self._function_context_cache = {}
    
    @abstractmethod
    def detect(self, ast: Any) -> List[Violation]:
        """
        Analyze AST and return list of violations.
        
        Args:
            ast: Parsed AST node
            
        Returns:
            List of Violation objects
        """
        pass
    
    def get_line_number(self, node: Any) -> int:
        """Get line number from AST node with offset."""
        from ...common import ASTLineUtils
        return ASTLineUtils.get_line_number(node, self.line_offset)
    
    def get_line_number_from_token(self, token: Any) -> int:
        """Get line number from token with offset - more reliable than get_line_number()."""
        # First try direct token access (most reliable for Lark tokens)
        if hasattr(token, 'line') and token.line is not None:
            # For PMD script content, add 1 to account for the <% line
            # The line_offset is where the script field starts, but the actual content starts on the next line
            return token.line + self.line_offset
        elif hasattr(token, 'children'):
            # If token doesn't have line info, search children for line numbers
            for child in token.children:
                if hasattr(child, 'line') and child.line is not None:
                    # For PMD script content, add 1 to account for the <% line
                    # The line_offset is where the script field starts, but the actual content starts on the next line
                    return child.line + self.line_offset
                # Recursively search deeper if needed
                if hasattr(child, 'children'):
                    for grandchild in child.children:
                        if hasattr(grandchild, 'line') and grandchild.line is not None:
                            # For PMD script content, add 1 to account for the <% line
                            # The line_offset is where the script field starts, but the actual content starts on the next line
                            return grandchild.line + self.line_offset
        
        # Default to line 1 if no line info found
        return self.line_offset
    
    def get_line_from_tree_node(self, node: Any) -> int:
        """Get line number from a Tree node by finding the first token with line info."""
        if hasattr(node, 'children') and len(node.children) > 0:
            for child in node.children:
                # Check if child has line info directly
                if hasattr(child, 'line') and child.line is not None:
                    return child.line + self.line_offset
                # If child is a Tree, recurse into it
                elif hasattr(child, 'children') and len(child.children) > 0:
                    for grandchild in child.children:
                        if hasattr(grandchild, 'line') and grandchild.line is not None:
                            return grandchild.line + self.line_offset
        return self.line_offset
    
    def get_function_context_for_node(self, node: Any, ast: Any) -> str:
        """Get the function name that contains the given node, or None if not in a function."""
        # Use AST object id as cache key to avoid rebuilding the same map
        ast_id = id(ast)
        
        # Check if we already have the function context map for this AST
        if ast_id not in self._function_context_cache:
            # Build function context map and cache it
            function_contexts = self._build_function_context_map(ast)
            self._function_context_cache[ast_id] = function_contexts
        else:
            # Use cached function context map
            function_contexts = self._function_context_cache[ast_id]
        
        # Find the enclosing function name
        return self._get_enclosing_function_name(node, function_contexts)
    
    def _build_function_context_map(self, ast: Any) -> dict:
        """Build a map of AST nodes to their enclosing function names."""
        function_contexts = {}
        
        # Recursively find all function expressions in the AST
        self._find_and_map_functions(ast, function_contexts)
        
        return function_contexts
    
    def _find_and_map_functions(self, node: Any, function_contexts: dict):
        """Recursively find function expressions and map their nodes."""
        if hasattr(node, 'data'):
            # Check if this is a variable statement that contains a function
            if node.data == 'variable_statement' and len(node.children) > 1:
                var_declaration = node.children[1]
                if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                    # Check if this variable declaration contains a function expression
                    for child in var_declaration.children:
                        if hasattr(child, 'data') and child.data in ['function_expression', 'arrow_function_expression']:
                            # Found a function! Get the variable name (function name)
                            if len(var_declaration.children) > 0:
                                var_name_token = var_declaration.children[0]
                                if hasattr(var_name_token, 'value'):
                                    function_name = var_name_token.value
                                    # Map all nodes within this function to the function name
                                    self._map_function_nodes(child, function_name, function_contexts)
        
        # Recursively process children
        if hasattr(node, 'children'):
            for child in node.children:
                self._find_and_map_functions(child, function_contexts)
    
    def _map_function_nodes(self, function_node: Any, function_name: str, function_contexts: dict):
        """Recursively map all nodes within a function to the function name."""
        function_contexts[function_node] = function_name
        
        if hasattr(function_node, 'children'):
            for child in function_node.children:
                if hasattr(child, 'data'):  # Only map Tree nodes, not Tokens
                    self._map_function_nodes(child, function_name, function_contexts)
    
    def _get_enclosing_function_name(self, node: Any, function_contexts: dict) -> str:
        """Find the name of the function that contains the given node."""
        # Check if this node is directly mapped to a function
        if node in function_contexts:
            return function_contexts[node]
        
        # Check if any parent node is mapped to a function
        # Since we don't have parent references, we'll use a different approach
        # We'll check if the node is a descendant of any function node
        # Find the closest (most specific) function by checking depth
        closest_function = None
        closest_depth = float('inf')
        
        for func_node, func_name in function_contexts.items():
            if self._is_descendant(node, func_node):
                # Calculate depth to find the closest function
                depth = self._calculate_descendant_depth(node, func_node)
                if depth < closest_depth:
                    closest_depth = depth
                    closest_function = func_name
        
        return closest_function
    
    def _calculate_descendant_depth(self, node: Any, ancestor: Any) -> int:
        """Calculate the depth of a node within an ancestor (0 = direct child)."""
        if node == ancestor:
            return 0
        
        if hasattr(ancestor, 'children'):
            for child in ancestor.children:
                if hasattr(child, 'data'):  # Only check Tree nodes
                    if self._is_descendant(node, child):
                        return 1 + self._calculate_descendant_depth(node, child)
        
        return float('inf')
    
    def _is_descendant(self, node: Any, ancestor: Any) -> bool:
        """Check if node is a descendant of ancestor."""
        if node == ancestor:
            return True
        
        if hasattr(ancestor, 'children'):
            for child in ancestor.children:
                if hasattr(child, 'data'):  # Only check Tree nodes
                    if self._is_descendant(node, child):
                        return True
        
        return False
    
    def clear_function_context_cache(self):
        """Clear the function context cache. Useful for testing or processing multiple files."""
        self._function_context_cache.clear()
    
    def extract_variable_from_empty_expression(self, node) -> str:
        """
        Extract variable name from empty expression nodes.
        Handles both empty keyword and empty() function cases.
        
        Args:
            node: AST node (empty_expression, not_empty_expression, or empty_function_expression)
            
        Returns:
            Variable name string, or empty string if not found
        """
        if not hasattr(node, 'data') or not hasattr(node, 'children'):
            return ""
        
        # Handle different AST structures for empty keyword vs empty() function
        if node.data == 'empty_function_expression':
            # empty_function_expression: ['empty', '(', 'expression', ')']
            if len(node.children) > 2:
                return self._extract_variable_from_node(node.children[2])
        else:
            # empty_expression: ['empty', 'expression'] 
            if len(node.children) > 1:
                child = node.children[1]
                # Check if it's a parenthesized expression (empty(variable) case)
                if child.data == 'parenthesized_expression' and len(child.children) > 0:
                    # Look inside the parentheses
                    inner_expr = child.children[0]
                    return self._extract_variable_from_node(inner_expr)
                else:
                    return self._extract_variable_from_node(child)
        
        return ""
    
    def extract_variable_from_not_empty_expression(self, node) -> str:
        """
        Extract variable name from not_expression containing empty expressions.
        Handles both !empty variable and !empty(variable) cases.
        
        Args:
            node: AST node (not_expression)
            
        Returns:
            Variable name string, or empty string if not found
        """
        if not hasattr(node, 'data') or not hasattr(node, 'children'):
            return ""
        
        if node.data == 'not_expression':
            if len(node.children) > 0 and isinstance(node.children[0], Tree) and node.children[0].data == 'empty_function_expression':
                # not_expression -> empty_function_expression: ['empty', '(', 'expression', ')']
                empty_func = node.children[0]
                if len(empty_func.children) > 2:
                    return self._extract_variable_from_node(empty_func.children[2])
            elif len(node.children) > 0 and isinstance(node.children[0], Tree) and node.children[0].data == 'empty_expression':
                # not_expression -> empty_expression -> parenthesized_expression (!empty(variable) case)
                empty_expr = node.children[0]
                if len(empty_expr.children) > 1:
                    child = empty_expr.children[1]
                    if child.data == 'parenthesized_expression' and len(child.children) > 0:
                        inner_expr = child.children[0]
                        return self._extract_variable_from_node(inner_expr)
                    else:
                        # not_expression -> empty_expression -> identifier_expression (!empty variable case)
                        return self._extract_variable_from_node(child)
        
        return ""
    
    def _extract_variable_from_node(self, node) -> str:
        """Extract variable name from a node."""
        if not hasattr(node, 'data'):
            return ""
            
        if node.data == 'identifier_expression' and len(node.children) > 0:
            return node.children[0].value if hasattr(node.children[0], 'value') else str(node.children[0])
        elif node.data == 'member_dot_expression':
            # Extract property chain
            return self._extract_property_chain(node) or ""
        
        return ""