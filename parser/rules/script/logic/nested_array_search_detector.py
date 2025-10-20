"""Nested array search detection logic for ScriptNestedArraySearchRule."""

from typing import Generator, Optional, Set
from lark import Tree, Token
from ..shared import ScriptDetector
from ..shared.violation import Violation


class NestedArraySearchDetector(ScriptDetector):
    """Detects nested array search patterns that cause severe performance issues."""

    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        
        # Methods that search/filter through arrays (problematic when nested)
        self.SEARCH_METHODS = {'find', 'filter'}
        
        # Methods that iterate over arrays (outer loops)
        self.ITERATION_METHODS = {'map', 'forEach', 'filter'}

    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect nested array search patterns."""
        if ast is None:
            return
        
        yield from self._find_nested_searches(ast, field_name, owned_identifiers=set())

    def _find_nested_searches(self, node: Tree, field_name: str, owned_identifiers: Set[str]) -> Generator[Violation, None, None]:
        """Recursively find nested array searches, tracking owned identifiers."""
        if not isinstance(node, Tree):
            return
        
        # Check if this node is an iteration method call
        if node.data == 'arguments_expression':
            method_name = self._get_method_name(node)
            
            if method_name in self.ITERATION_METHODS:
                # Extract callback parameters
                callback_params = self._get_callback_parameters(node)
                
                # All identifiers that are "owned" in this callback's scope
                # (includes params from outer callbacks + this callback's params)
                callback_owned = owned_identifiers | callback_params
                
                # Get callback body
                callback_body = self._get_callback_body(node)
                
                if callback_body:
                    # Check for search methods in this callback
                    for search_violation in self._check_for_search_methods(callback_body, callback_owned, field_name, node):
                        yield search_violation
                    
                    # Recurse into callback body with updated owned identifiers
                    yield from self._find_nested_searches(callback_body, field_name, callback_owned)
                
                # Don't recurse into children again
                return
        
        # Recurse into all children
        if hasattr(node, 'children'):
            for child in node.children:
                if isinstance(child, Tree):
                    yield from self._find_nested_searches(child, field_name, owned_identifiers)

    def _check_for_search_methods(self, callback_body: Tree, owned_identifiers: Set[str], 
                              field_name: str, iteration_node: Tree) -> Generator[Violation, None, None]:
        """Check callback body for search methods on external arrays."""
        if not isinstance(callback_body, Tree):
            return
        
        # CRITICAL FIX: Check if the callback_body itself is a search call
        if callback_body.data == 'arguments_expression':
            method_name = self._get_method_name(callback_body)
            
            if method_name in self.SEARCH_METHODS:
                if self._is_external_array_search(callback_body, owned_identifiers):
                    line_number = self.get_line_from_tree_node(callback_body)
                    
                    outer_array = self._get_array_name(iteration_node) or 'outerArray'
                    inner_array = self._get_array_name(callback_body) or 'innerArray'
                    code_snippet = self._extract_code_snippet(iteration_node, callback_body)
                    
                    message = self._create_violation_message(code_snippet, outer_array, inner_array)
                    
                    yield Violation(
                        message=message,
                        line=line_number
                    )
            
            # Don't recurse into ITERATION methods - they'll be handled by _find_nested_searches
            # This prevents duplicate reporting for deeply nested structures
            if method_name in self.ITERATION_METHODS:
                return  # STOP HERE - don't recurse into children
            
            # For search methods and other calls, continue recursing
            if hasattr(callback_body, 'children'):
                for child in callback_body.children:
                    if isinstance(child, Tree):
                        yield from self._check_for_search_methods(child, owned_identifiers, field_name, iteration_node)
            return
        
        # For non-call nodes, recurse into children
        if not hasattr(callback_body, 'children'):
            return
        
        for child in callback_body.children:
            if isinstance(child, Tree):
                yield from self._check_for_search_methods(child, owned_identifiers, field_name, iteration_node)

    def _get_method_name(self, call_node: Tree) -> Optional[str]:
        """Extract method name from arguments_expression (e.g., 'map' from array.map())."""
        if not isinstance(call_node, Tree) or call_node.data != 'arguments_expression':
            return None
        
        if len(call_node.children) < 1:
            return None
        
        callee = call_node.children[0]
        
        # Check if it's a member expression (obj.method)
        if isinstance(callee, Tree) and callee.data == 'member_dot_expression':
            if len(callee.children) >= 2:
                method_token = callee.children[1]
                if isinstance(method_token, Token) and hasattr(method_token, 'value'):
                    return method_token.value
        
        return None

    def _get_callback_parameters(self, call_node: Tree) -> Set[str]:
        """Extract parameter names from callback function."""
        params = set()
        
        if not isinstance(call_node, Tree) or call_node.data != 'arguments_expression':
            return params
        
        if len(call_node.children) < 2:
            return params
        
        # Get arguments
        args_node = call_node.children[1]
        
        if not isinstance(args_node, Tree):
            return params
        
        # Find the callback (first argument for map/forEach/filter)
        callback = None
        if args_node.data == 'arguments':
            # arguments node contains the callback
            for child in args_node.children:
                if isinstance(child, Tree) and child.data in ['arrow_function_expression', 'function_expression']:
                    callback = child
                    break
        elif args_node.data in ['arrow_function_expression', 'function_expression']:
            callback = args_node
        
        if not callback:
            return params
        
        # Extract parameters based on function type
        if callback.data == 'arrow_function_expression':
            params = self._extract_arrow_function_params(callback)
        elif callback.data == 'function_expression':
            params = self._extract_function_expression_params(callback)
        
        return params

    def _extract_arrow_function_params(self, arrow_func: Tree) -> Set[str]:
        """Extract parameters from arrow function."""
        params = set()
        
        # Arrow function structure varies:
        # 1. Single param: identifier => body
        # 2. Multiple params: (param1, param2) => body
        
        for child in arrow_func.children:
            if isinstance(child, Token):
                # Single parameter (identifier token)
                if child.type == 'IDENTIFIER':
                    params.add(child.value)
            elif isinstance(child, Tree):
                # Check for formal_parameter_list or parameter_list
                if child.data in ['formal_parameter_list', 'parameter_list']:
                    params.update(self._extract_params_from_list(child))
                # Check for single identifier_expression
                elif child.data == 'identifier_expression':
                    if len(child.children) > 0 and isinstance(child.children[0], Token):
                        params.add(child.children[0].value)
        
        return params

    def _extract_function_expression_params(self, func_expr: Tree) -> Set[str]:
        """Extract parameters from function expression."""
        params = set()
        
        for child in func_expr.children:
            if isinstance(child, Tree) and child.data in ['formal_parameter_list', 'parameter_list']:
                params.update(self._extract_params_from_list(child))
        
        return params

    def _extract_params_from_list(self, param_list: Tree) -> Set[str]:
        """Extract parameter names from parameter list."""
        params = set()
        
        for child in param_list.children:
            if isinstance(child, Token) and child.type == 'IDENTIFIER':
                params.add(child.value)
            elif isinstance(child, Tree):
                if child.data == 'identifier_expression' and len(child.children) > 0:
                    if isinstance(child.children[0], Token):
                        params.add(child.children[0].value)
        
        return params

    def _get_callback_body(self, call_node: Tree) -> Optional[Tree]:
        """Extract the callback function body from a method call."""
        if not isinstance(call_node, Tree) or call_node.data != 'arguments_expression':
            return None
        
        if len(call_node.children) < 2:
            return None
        
        args_node = call_node.children[1]
        
        if not isinstance(args_node, Tree):
            return None
        
        # Find the callback
        callback = None
        if args_node.data == 'arguments':
            for child in args_node.children:
                if isinstance(child, Tree) and child.data in ['arrow_function_expression', 'function_expression']:
                    callback = child
                    break
        elif args_node.data in ['arrow_function_expression', 'function_expression']:
            callback = args_node
        
        if not callback:
            return None
        
        # Extract body based on function type
        return self._extract_function_body(callback)

    def _extract_function_body(self, callback: Tree) -> Optional[Tree]:
        """Extract the body from different function types."""
        if not isinstance(callback, Tree):
            return None
        
        if callback.data == 'arrow_function_expression':
            # Arrow function: last child that's a Tree is usually the body
            for child in reversed(callback.children):
                if isinstance(child, Tree) and child.data not in ['formal_parameter_list', 'parameter_list', 'identifier_expression']:
                    return child
        
        elif callback.data == 'function_expression':
            # Function expression: look for source_elements or block
            for child in callback.children:
                if isinstance(child, Tree) and child.data in ['source_elements', 'block']:
                    return child
        
        return None

    def _is_external_array_search(self, search_node: Tree, owned_identifiers: Set[str]) -> bool:
        """Check if search is on external array vs owned property/identifier."""
        if not isinstance(search_node, Tree) or search_node.data != 'arguments_expression':
            return False
        
        if len(search_node.children) < 1:
            return False
        
        callee = search_node.children[0]
        
        if not isinstance(callee, Tree) or callee.data != 'member_dot_expression':
            return False
        
        if len(callee.children) < 1:
            return False
        
        # Get the object being searched (the thing before .find or .filter)
        obj = callee.children[0]
        
        if not isinstance(obj, Tree):
            return False
        
        # If it's a simple identifier (e.g., orgData.find())
        if obj.data == 'identifier_expression':
            if len(obj.children) > 0 and isinstance(obj.children[0], Token):
                identifier = obj.children[0].value
                
                # If this identifier is a callback parameter (owned), don't flag
                if identifier in owned_identifiers:
                    return False  # e.g., item.find() where 'item' is callback param
                
                # Otherwise it's external
                return True  # e.g., orgData.find() where 'orgData' is external
        
        # If it's a property access (e.g., item.skills.find()), it's owned data
        # This includes member_dot_expression and other property accesses
        return False

    def _create_violation_message(self, code_snippet: str, outer_array: str, inner_array: str) -> str:
        """Create concise violation message with code context."""
        return (
            f"Nested array search: {code_snippet}\n"
            f"   → Searches the entire inner array for every outer item (potential for out-of-memory issues)\n"
            f"   → Fix: const {inner_array}Map = list:toMap({inner_array}, 'keyField'); "
            f"{outer_array}.map(item => {inner_array}Map[item.key])"
        )
    
    def _extract_code_snippet(self, outer_node: Tree, inner_node: Tree) -> str:
        """Extract readable code snippet showing the nested pattern."""
        # Get method names
        outer_method = self._get_method_name(outer_node) or 'method'
        inner_method = self._get_method_name(inner_node) or 'method'
        
        # Get array names
        outer_array = self._get_array_name(outer_node) or 'array'
        inner_array = self._get_array_name(inner_node) or 'array'
        
        return f"{outer_array}.{outer_method}(...) with {inner_array}.{inner_method}(...) inside"
    
    def _get_array_name(self, call_node: Tree) -> Optional[str]:
        """Extract the array name from a call expression."""
        if not isinstance(call_node, Tree) or call_node.data != 'arguments_expression':
            return None
        
        if len(call_node.children) < 1:
            return None
        
        callee = call_node.children[0]
        
        # Check if it's a member expression (array.method)
        if isinstance(callee, Tree) and callee.data == 'member_dot_expression':
            if len(callee.children) >= 1:
                obj = callee.children[0]
                
                # Extract array name from identifier_expression
                if isinstance(obj, Tree) and obj.data == 'identifier_expression':
                    if len(obj.children) > 0 and isinstance(obj.children[0], Token):
                        return obj.children[0].value
        
        return None