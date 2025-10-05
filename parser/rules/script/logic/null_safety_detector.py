"""Detector for null safety violations in script code."""

from typing import Any, List, Optional, Set
from lark import Tree
from ...script.shared import ScriptDetector, Violation
from ...common import ASTLineUtils


class NullSafetyDetector(ScriptDetector):
    """Detects unsafe property access patterns that lack null safety."""

    def __init__(self, file_path: str = "", line_offset: int = 1, safe_variables: Set[str] = None, endpoint_names: Set[str] = None):
        """Initialize detector with file context, safe variables, and endpoint names."""
        super().__init__(file_path, line_offset)
        self.safe_variables = safe_variables or set()
        self.endpoint_names = endpoint_names or set()

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
            # Check if this unsafe access is inside a function
            function_name = self.get_function_context_for_node(access_info['node'], ast)
            
            if function_name:
                message = f"Potentially unsafe property access in function '{function_name}': {access_info['chain']} - consider using null coalescing (??) or empty checks"
            else:
                message = f"Potentially unsafe property access: {access_info['chain']} - consider using null coalescing (??) or empty checks"
            
            violations.append(Violation(
                message=message,
                line=self.get_line_number_from_token(access_info['node'])
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
        
        # Check if the chain is safe due to local variable declaration
        if self._is_chain_safe_due_to_local_declaration(ast, chain):
            return False
        
        # Check if the chain is safe due to known safe patterns
        if self._is_chain_safe_due_to_known_patterns(chain):
            return False
        
        # Check if the chain is safe due to safe property patterns (widget, childrenMap, etc.)
        if self._is_safe_property_pattern(chain):
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
        # Widget property access - if compiler allows widget.property, it's safe
        if chain.startswith('widget.'):
            return True
        
        # Grid structure patterns - these are guaranteed by the grid definition
        # childrenMap access is always safe in Workday Extend
        if '.childrenMap.' in chain:
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
            # Check if the left side of the null coalescing contains our chain
            if len(node.children) > 0 and self._expression_contains_chain(node.children[0], chain):
                return True
                
        # Check for ternary operators (condition ? safe_expression : fallback)
        if node.data == 'ternary_expression':
            # For ternary: condition ? true_expr : false_expr
            # If the condition checks the same object, then the true_expr is safe
            if len(node.children) >= 3:
                condition = node.children[0]
                true_expr = node.children[1]
                false_expr = node.children[2]
                
                # Check if the condition tests the same object as our chain
                if self._condition_tests_object(condition, chain):
                    # If the true expression contains our chain, it's safe
                    if self._expression_contains_chain(true_expr, chain):
                        return True
                
        # Check for Elvis operators (obj ?: fallback) - equivalent to obj ? obj : fallback
        if node.data == 'elvis_expression':
            # For Elvis: left_expr ?: right_expr
            # The Elvis operator is inherently safe because it only uses left_expr if it's truthy
            if len(node.children) >= 2:
                left_expr = node.children[0]
                right_expr = node.children[1]
                
                # If the left expression contains our chain, it's safe
                if self._expression_contains_chain(left_expr, chain):
                    return True
                
        return False

    def _condition_tests_object(self, condition_node: Tree, chain: str) -> bool:
        """Check if a condition tests the same object as the given chain."""
        if not hasattr(condition_node, 'data'):
            return False
            
        # Direct object test: obj or !obj
        if condition_node.data == 'identifier_expression':
            if self._chain_matches_node(condition_node, chain):
                return True
                
        # Negated object test: !obj
        if condition_node.data == 'not_expression':
            if len(condition_node.children) > 0:
                child = condition_node.children[0]
                if self._chain_matches_node(child, chain):
                    return True
                    
        # Empty check: empty obj
        if condition_node.data in ['empty_expression', 'not_empty_expression']:
            if len(condition_node.children) > 1:
                child = condition_node.children[1]
                if self._chain_matches_node(child, chain):
                    return True
                    
        # Recursively check child nodes for complex conditions
        if hasattr(condition_node, 'children'):
            for child in condition_node.children:
                if self._condition_tests_object(child, chain):
                    return True
                    
        return False

    def _expression_contains_chain(self, node: Tree, chain: str) -> bool:
        """Check if an expression contains the given property chain."""
        if not hasattr(node, 'data'):
            return False
            
        # Check if this node itself matches the chain
        if self._chain_matches_node(node, chain):
            return True
            
        # Recursively check child nodes
        if hasattr(node, 'children'):
            for child in node.children:
                if self._expression_contains_chain(child, chain):
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

    def _is_chain_safe_due_to_local_declaration(self, ast: Tree, chain: str) -> bool:
        """Check if a property access chain is safe due to local variable declaration and initialization."""
        parts = chain.split('.')
        if len(parts) < 2:
            return False
            
        root_object = parts[0]
        
        # Look for variable declarations in the AST
        for node in ast.iter_subtrees():
            if node.data == 'variable_declaration':
                # Check if this declares our root object
                if self._declares_variable(node, root_object):
                    # Check if the variable is initialized with an object that has the first property
                    # If the first property exists, we consider the entire chain safe
                    if self._is_variable_initialized_with_properties(node, [parts[1]]):
                        return True
                        
        return False

    def _declares_variable(self, declaration_node: Tree, variable_name: str) -> bool:
        """Check if a variable declaration node declares the given variable."""
        if not hasattr(declaration_node, 'children') or len(declaration_node.children) < 2:
            return False
            
        # Variable declaration has structure: ['variable_name', 'initialization_value']
        declared_var = declaration_node.children[0]
        if hasattr(declared_var, 'value'):
            return declared_var.value == variable_name
        elif hasattr(declared_var, 'children') and len(declared_var.children) > 0:
            return str(declared_var.children[0]) == variable_name
        else:
            return str(declared_var) == variable_name
                
        return False

    def _is_variable_initialized_with_properties(self, declaration_node: Tree, required_properties: List[str]) -> bool:
        """Check if a variable is initialized with an object that has the required properties."""
        if not hasattr(declaration_node, 'children') or len(declaration_node.children) < 2:
            return False
            
        # Variable declaration has structure: ['variable_name', 'initialization_value']
        init_value = declaration_node.children[1]
        
        if not init_value:
            return False
            
        # Check if it's an object literal with the required properties
        if init_value.data == 'curly_literal_expression':
            # This is an object literal expression, check its contents
            return self._object_has_properties(init_value, required_properties)
        elif init_value.data == 'identifier_expression':
            # Variable is initialized with another variable - this is harder to track
            # For now, we'll be conservative and return False
            return False
            
        return False

    def _object_has_properties(self, object_node: Tree, required_properties: List[str]) -> bool:
        """Check if an object literal has the required properties."""
        if not hasattr(object_node, 'children'):
            return False
            
        # Look for property assignments in the object
        declared_properties = set()
        
        # Handle curly_literal_expression -> curly_literal structure
        if object_node.data == 'curly_literal_expression' and len(object_node.children) > 0:
            curly_literal = object_node.children[0]
            if curly_literal.data == 'curly_literal':
                # Process the curly_literal children
                for i in range(0, len(curly_literal.children), 2):  # Skip every other child (values)
                    if i < len(curly_literal.children):
                        prop_node = curly_literal.children[i]
                        if prop_node.data == 'literal_expression' and len(prop_node.children) > 0:
                            prop_token = prop_node.children[0]
                            if hasattr(prop_token, 'value'):
                                # Remove quotes from string literal
                                prop_name = prop_token.value.strip('"\'')
                                declared_properties.add(prop_name)
        
        # Check if all required properties are declared
        return all(prop in declared_properties for prop in required_properties)

    def _is_chain_safe_due_to_known_patterns(self, chain: str) -> bool:
        """Check if a property access chain is safe due to known safe patterns."""
        parts = chain.split('.')
        if len(parts) < 2:
            return False
        
        # Pattern 1: Endpoint data patterns - use actual endpoint names
        # Examples: getExpenses.data.filter, getTools.data.find, etc.
        if len(parts) >= 3 and parts[-2] == 'data':
            endpoint_name = parts[0]
            if endpoint_name in self.endpoint_names:
                # Check if the last part is an array method
                last_part = parts[-1]
                if last_part in ['filter', 'find', 'map', 'reduce', 'forEach', 'for']:
                    return True
        
        # Pattern 2: Grid rows patterns - rows is always a list (empty or populated)
        # Examples: homeExpensesGrid.rows.forEach, vehicleGrid.rows.filter, etc.
        if len(parts) >= 3 and parts[-2] == 'rows':
            # Check if this looks like a grid rows access
            grid_name = parts[0]
            if 'grid' in grid_name.lower():
                # Check if the last part is an array method
                last_part = parts[-1]
                if last_part in ['filter', 'find', 'map', 'reduce', 'forEach', 'for']:
                    return True
        
        # Pattern 3: Generic array method patterns - if compiler allows it, it's safe
        # Examples: anyObject.filter, anyList.forEach, etc.
        if len(parts) >= 2:
            last_part = parts[-1]
            if last_part in ['filter', 'find', 'map', 'reduce', 'forEach', 'for']:
                # If the compiler allows an array method call, the object is guaranteed to be an array
                return True
        
        return False

