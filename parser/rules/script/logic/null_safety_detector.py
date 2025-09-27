"""Detector for null safety violations in script code."""

from typing import Any, List, Optional, Set
from lark import Tree
from ...script.shared import ScriptDetector, Violation
from ...script.shared.ast_utils import get_line_number


class NullSafetyDetector(ScriptDetector):
    """Detects unsafe property access patterns that lack null safety."""

    def __init__(self, file_path: str = "", line_offset: int = 1, safe_variables: Set[str] = None):
        """Initialize detector with file context and safe variables."""
        super().__init__(file_path, line_offset)
        self.safe_variables = safe_variables or set()

    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """
        Analyze AST and return list of null safety violations.
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed (for context)
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Find unsafe property accesses
        unsafe_accesses = self._find_unsafe_property_accesses_with_context(ast, self.safe_variables)
        
        for access_info in unsafe_accesses:
            violations.append(Violation(
                message=f"Potentially unsafe property access: {access_info['chain']} - consider using null coalescing (??) or empty checks",
                line=self.get_line_number(access_info['node']),
                column=1
            ))
        
        return violations

    def _find_unsafe_property_accesses_with_context(self, ast: Tree, safe_variables: Set[str]) -> List[dict]:
        """Find unsafe property accesses, excluding variables known to be safe due to conditional execution."""
        unsafe_accesses = []       
        all_chains = []
        seen_chains = set()  # Track seen chains to avoid duplicates

        # First, collect all member access expressions and their chains
        for node in ast.iter_subtrees():
            if node.data == 'member_dot_expression':
                chain = self._extract_property_chain(node)
                if chain and self._is_unsafe_chain_with_context(ast, chain, safe_variables):
                    line = getattr(node.meta, 'line', 1)
                    chain_key = (chain, line)  # Use chain and line as key
                    
                    # Only add if we haven't seen this exact chain on this line before
                    if chain_key not in seen_chains:
                        seen_chains.add(chain_key)
                        all_chains.append({
                            'chain': chain,
                            'line': line,
                            'node': node
                        })

        # Filter out redundant chains - only keep the longest/most specific ones
        filtered_chains = self._filter_redundant_chains(all_chains)
        
        for chain_info in filtered_chains:
            unsafe_accesses.append({
                'chain': chain_info['chain'],
                'line': chain_info['line'],
                'node': chain_info['node']
            })
        
        return unsafe_accesses

    def _is_unsafe_chain_with_context(self, ast: Tree, chain: str, safe_variables: Set[str]) -> bool:
        """Check if a property access chain is unsafe, considering conditional execution context."""
        parts = chain.split('.')
        
        if len(parts) < 2:
            return False
        
        root_object = parts[0]
        
        # Check if the entire chain is safe (e.g., from render/exclude conditions)
        if chain in safe_variables:
            return False
        
        # Check if the root object is safe
        if root_object in safe_variables:
            # If the root is safe, check if any parent chain is also safe
            for i in range(1, len(parts)):
                partial_chain = '.'.join(parts[:i+1])
                if partial_chain in safe_variables:
                    return False
        
        # Check if any parent chain is safe
        for i in range(len(parts) - 1):
            partial_chain = '.'.join(parts[:i+1])
            if partial_chain in safe_variables:
                return False
        
        # If no safe variables found, use the standard unsafe chain logic
        return self._is_unsafe_chain(ast, chain)

    def _find_unsafe_property_accesses(self, ast: Tree) -> List[dict]:
        """Find property access chains that lack null safety."""
        unsafe_accesses = []       
        all_chains = []
        seen_chains = set()  # Track seen chains to avoid duplicates

        # First, collect all member access expressions and their chains
        for node in ast.iter_subtrees():
            if node.data == 'member_dot_expression':
                chain = self._extract_property_chain(node)
                if chain and self._is_unsafe_chain(ast, chain):
                    line = getattr(node.meta, 'line', 1)
                    chain_key = (chain, line)  # Use chain and line as key
                    
                    # Only add if we haven't seen this exact chain on this line before
                    if chain_key not in seen_chains:
                        seen_chains.add(chain_key)
                        all_chains.append({
                            'chain': chain,
                            'line': line,
                            'node': node
                        })

        # Filter out redundant chains - only keep the longest/most specific ones
        filtered_chains = self._filter_redundant_chains(all_chains)
        
        for chain_info in filtered_chains:
            unsafe_accesses.append({
                'chain': chain_info['chain'],
                'line': chain_info['line'],
                'node': chain_info['node']
            })

        return unsafe_accesses

    def _filter_redundant_chains(self, all_chains: List[dict]) -> List[dict]:
        """Filter out redundant property access chains, keeping only the longest/most specific ones."""
        if not all_chains:
            return []
        
        # Group chains by line number first
        line_groups = {}
        for chain_info in all_chains:
            line = chain_info['line']
            if line not in line_groups:
                line_groups[line] = []
            line_groups[line].append(chain_info)
        
        filtered_chains = []
        
        # Process each line separately
        for line, chains_on_line in line_groups.items():
            # Sort chains on this line by length (longest first)
            sorted_chains = sorted(chains_on_line, key=lambda x: len(x['chain'].split('.')), reverse=True)
            
            # Keep only chains that are not prefixes of longer chains on the same line
            for chain_info in sorted_chains:
                chain = chain_info['chain']
                is_redundant = False
                
                # Check if this chain is a prefix of any already filtered chain on this line
                for filtered_chain_info in filtered_chains:
                    if filtered_chain_info['line'] == line:  # Only check chains on the same line
                        filtered_chain = filtered_chain_info['chain']
                        if filtered_chain.startswith(chain + '.'):
                            # The filtered chain is longer and starts with this chain, so this one is redundant
                            is_redundant = True
                            break
                
                if not is_redundant:
                    filtered_chains.append(chain_info)
        
        return filtered_chains
    
    def _extract_property_chain(self, node: Tree) -> Optional[str]:
        """Extract the full property access chain from a member_dot_expression."""
        if node.data != 'member_dot_expression' or len(node.children) < 2:
            return None
            
        # Get the object being accessed
        obj_node = node.children[0]
        property_name = node.children[1].value if hasattr(node.children[1], 'value') else str(node.children[1])
        
        # If the object is also a member access, recurse
        if obj_node.data == 'member_dot_expression':
            parent_chain = self._extract_property_chain(obj_node)
            if parent_chain:
                return f"{parent_chain}.{property_name}"
            else:
                return f"<expression>.{property_name}"
        elif obj_node.data == 'identifier_expression' and len(obj_node.children) > 0:
            identifier = obj_node.children[0].value if hasattr(obj_node.children[0], 'value') else str(obj_node.children[0])
            return f"{identifier}.{property_name}"
        else:
            return f"<expression>.{property_name}"

    def _is_unsafe_chain(self, ast: Tree, chain: str) -> bool:
        """Check if a property access chain is unsafe (lacks null safety) based on depth and specific patterns."""
        # Split the chain to get individual parts
        parts = chain.split('.')

        if len(parts) < 2:
            return False
        
        # Only flag chains that are deep enough to be potentially unsafe
        # Target patterns: getData.data[0], getData.invoke().foo, myVal.worker.firstName
        # Don't flag: getData.data, myVal.worker, widget.value
        
        # Check if this is a high-risk pattern that should always be flagged
        if self._is_high_risk_pattern(chain):
            return not self._is_protected_chain(ast, chain)
        
        # For other patterns, only flag if they meet specific criteria:
        # 1. Must be at least 3 levels deep (obj.prop.subprop)
        # 2. Must not be a safe pattern
        # 3. Must not be a global object
        if len(parts) < 3:
            return False  # Don't flag shallow access like "obj.property"
        
        # Check if this is a safe property pattern (widget properties, etc.)
        if self._is_safe_property_pattern(chain):
            return False
        
        # Check if the root object is a known global/library object
        root_object = parts[0]
        if self._is_global_object(root_object):
            return False
            
        # Check if the full chain is protected
        if self._is_protected_chain(ast, chain):
            return False
            
        # Also check if any parent chain is protected (which would make this safe)
        for i in range(len(parts) - 1):
            partial_chain = '.'.join(parts[:i+1])
            if self._is_protected_chain(ast, partial_chain):
                return False
            
        return True

    def _is_high_risk_pattern(self, chain: str) -> bool:
        """Check if a property access chain represents a high-risk pattern that should always be flagged."""
        # Array access patterns - these are always risky
        if '[' in chain and ']' in chain:
            return True
        
        # Method chaining patterns - calling a method and then accessing properties
        # Pattern: obj.method().property
        if '.invoke().' in chain or '.get().' in chain or '.find().' in chain:
            return True
        
        # Deep property chains that are commonly unsafe (3+ levels)
        # Pattern: obj.data.property or obj.response.property
        parts = chain.split('.')
        if len(parts) >= 3:
            if any(pattern in chain for pattern in [
                '.data.', '.response.', '.result.', '.payload.', '.content.'
            ]):
                return True
        
        # API response patterns that are commonly unsafe
        # Pattern: apiCall.data[0].property or apiCall.response.items[0]
        if any(pattern in chain for pattern in [
            '.data[', '.response[', '.result[', '.items[', '.list['
        ]):
            return True
        
        return False

    def _is_safe_property_pattern(self, chain: str) -> bool:
        """Check if a property access chain represents a safe pattern that doesn't need null safety checks."""
        # Widget method calls and properties - these are safe in PMD context
        if any(pattern in chain for pattern in [
            'widget.setError', 'widget.clearError', 'widget.setValue',
            'widget.value', 'widget.selectedEntries', 'widget.children', 'widget.childrenMap', 
            'widget.label', 'widget.data', 'widget.getChildren', 'widget.setEnabled'
        ]):
            return True
        
        # Array method calls - these are safe
        if any(pattern in chain for pattern in [
            '.filter', '.map', '.sort', '.distinct', '.find', '.forEach', '.reduce', '.add', '.size'
        ]):
            return True
        
        # Global object properties that are safe
        if any(pattern in chain for pattern in [
            'site.applicationId', 'pageVariables.', 'sessionVariables.', 'queryParams.', 'self.data'
        ]):
            return True
        
        # Collection method calls that are safe
        if any(pattern in chain for pattern in [
            '.add', '.find', '.size', '.length'
        ]):
            return True
        
        return False

    def _is_global_object(self, object_name: str) -> bool:
        """Check if an object name refers to a known global/library object."""
        # List of known global objects that are guaranteed to exist and don't need null safety checks
        global_objects = {'console', 'pageVariables', 'sessionVariables', 'queryParams', 'self'}
        
        return object_name in global_objects

    def _is_protected_chain(self, ast: Tree, chain: str) -> bool:
        """Check if a property chain is protected by null safety mechanisms."""
        # Look for empty checks, null coalescing, or optional chaining
        for node in ast.iter_subtrees():
            if self._has_null_safety_protection(node, chain):
                return True

        return False

    def _has_null_safety_protection(self, node: Tree, chain: str) -> bool:
        """Check if a node contains null safety protection for the given chain."""
        if not hasattr(node, 'data') or not hasattr(node, 'children'):
            return False

        # Check for empty expressions
        if node.data in ['empty_expression', 'not_empty_expression', 'empty_function_expression']:
            # For empty expressions, check the child expression being tested
            # empty_expression has ['empty', 'expression'] structure
            if len(node.children) > 1 and self._chain_matches_node(node.children[1], chain):
                return True
                
        # Check for null coalescing
        if node.data == 'null_coalescing_expression':
            if self._chain_matches_node(node.children[0], chain):
                return True
                

        # Check for optional chaining
        if node.data == 'optional_member_dot_expression':
            if self._chain_matches_node(node, chain):
                return True
                

        return False

    def _chain_matches_node(self, node: Tree, chain: str) -> bool:
        """Check if a node represents the given property chain."""
        if not hasattr(node, 'data'):
            return False
            
        if node.data == 'identifier_expression' and len(node.children) > 0:
            identifier = node.children[0].value if hasattr(node.children[0], 'value') else str(node.children[0])
            return chain == identifier
        elif node.data == 'member_dot_expression':
            extracted_chain = self._extract_property_chain(node)
            return extracted_chain == chain
        return False

