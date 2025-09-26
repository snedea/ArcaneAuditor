"""Common AST utilities for script analysis."""

from typing import Any, List, Optional, Set, Tuple
from lark import Tree


# Control flow node types for efficient membership checking
CONTROL_FLOW_NODES: Set[str] = {
    "if_statement", 
    "while_statement", 
    "for_statement", 
    "switch_statement"
}


def get_line_number(node: Any, line_offset: int = 1) -> int:
    """Get line number from AST node with offset."""
    if hasattr(node, 'meta') and hasattr(node.meta, 'line'):
        return node.meta.line + line_offset - 1
    return 1


def extract_expression_text(node: Any) -> str:
    """Extract text content from an expression node."""
    if hasattr(node, 'children') and node.children:
        # For simple expressions, return the first child's text
        first_child = node.children[0]
        if hasattr(first_child, 'value'):
            return first_child.value
        elif hasattr(first_child, 'children') and first_child.children:
            return extract_expression_text(first_child)
    return ""


def find_member_access_chains(node: Any) -> List[List[str]]:
    """Find all member access chains in an AST (e.g., obj.prop.subprop)."""
    chains = []
    
    def traverse(n: Any, current_chain: List[str]):
        if hasattr(n, 'data'):
            if n.data == 'member_expression':
                # Extract the property name
                if hasattr(n, 'children') and len(n.children) >= 2:
                    prop_node = n.children[1]
                    if hasattr(prop_node, 'value'):
                        current_chain.append(prop_node.value)
                    elif hasattr(prop_node, 'children') and prop_node.children:
                        # Handle computed property access
                        current_chain.append(f"[{extract_expression_text(prop_node)}]")
                
                # Continue traversing the object part
                if hasattr(n, 'children') and n.children:
                    traverse(n.children[0], current_chain)
            else:
                # Continue traversing children
                if hasattr(n, 'children'):
                    for child in n.children:
                        traverse(child, current_chain)
    
    traverse(node, [])
    return chains


def find_data_nodes(ast: Any, node_type: str) -> List[Any]:
    """Find all nodes of a specific type in the AST."""
    nodes = []
    
    def traverse(n: Any):
        if hasattr(n, 'data') and n.data == node_type:
            nodes.append(n)
        
        if hasattr(n, 'children'):
            for child in n.children:
                traverse(child)
    
    traverse(ast)
    return nodes


def has_control_flow_structures(node: Any) -> bool:
    """Check if a node contains control flow structures."""
    if not hasattr(node, 'data'):
        return False
    
    # Check for control flow structures using constant for efficiency
    if node.data in CONTROL_FLOW_NODES:
        return True
    
    # Recursively check children
    if hasattr(node, 'children'):
        for child in node.children:
            if has_control_flow_structures(child):
                return True
    
    return False


def is_script_expression_with_returns(node: Any) -> bool:
    """
    Check if a function node is a script expression (fake function) vs actual function definition.
    
    Script expressions typically have:
    - Simple return statements without complex logic
    - No control flow structures
    - Minimal setup code
    """
    if not hasattr(node, 'children') or len(node.children) < 3:
        return False
    
    function_body = node.children[2]
    
    # Check if the body contains only simple return statements
    return _is_script_expression_with_returns_helper(function_body)


def _is_script_expression_with_returns_helper(node: Any) -> bool:
    """Helper function to check if a node represents a script expression."""
    if not hasattr(node, 'data'):
        return True
    
    # If we find control flow structures, it's not a simple script expression
    if node.data in CONTROL_FLOW_NODES:
        return False
    
    # If we find complex statements, it's not a simple script expression
    if node.data in ['variable_declaration', 'assignment', 'function_call']:
        return False
    
    # For return statements, check if they're simple
    if node.data == 'return_statement':
        if hasattr(node, 'children') and node.children:
            # Check if the return value is simple (literal, variable, or simple expression)
            return_value = node.children[0]
            return _is_simple_expression(return_value)
        return True
    
    # For block statements, check all children
    if node.data == 'block_statement':
        if hasattr(node, 'children'):
            for child in node.children:
                if not _is_script_expression_with_returns_helper(child):
                    return False
        return True
    
    # For other nodes, continue checking
    if hasattr(node, 'children'):
        for child in node.children:
            if not _is_script_expression_with_returns_helper(child):
                return False
    
    return True


def _is_simple_expression(node: Any) -> bool:
    """Check if an expression is simple (literal, variable, or basic operation)."""
    if not hasattr(node, 'data'):
        return True
    
    # Simple expressions
    if node.data in ['literal', 'identifier', 'member_expression']:
        return True
    
    # Basic arithmetic operations
    if node.data in ['add', 'subtract', 'multiply', 'divide']:
        if hasattr(node, 'children'):
            for child in node.children:
                if not _is_simple_expression(child):
                    return False
        return True
    
    # Function calls are not considered simple
    if node.data == 'call_expression':
        return False
    
    # For other expressions, check children
    if hasattr(node, 'children'):
        for child in node.children:
            if not _is_simple_expression(child):
                return False
    
    return True


def get_function_body(node: Any) -> Optional[Any]:
    """Get the function body from a function expression node."""
    if not hasattr(node, 'children') or len(node.children) < 3:
        return None
    return node.children[2]


def get_function_parameters(node: Any) -> List[str]:
    """Get parameter names from a function expression node."""
    parameters = []
    if hasattr(node, 'children') and len(node.children) >= 2:
        params_node = node.children[1]
        if hasattr(params_node, 'children'):
            for param in params_node.children:
                if hasattr(param, 'children') and param.children:
                    param_name = param.children[0]
                    if hasattr(param_name, 'value'):
                        parameters.append(param_name.value)
    return parameters
