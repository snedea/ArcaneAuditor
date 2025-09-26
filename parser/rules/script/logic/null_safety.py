from typing import Generator, List, Optional, Set
from lark import Tree
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel
from ...line_number_utils import LineNumberUtils


class ScriptNullSafetyRule(Rule):
    """Validates that property access chains are properly null-safe."""

    DESCRIPTION = "Ensures property access chains are protected against null reference exceptions"
    SEVERITY = "WARNING"

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze scripts for unsafe property access patterns, considering conditional execution contexts."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            # Use the generic script field finder to detect all fields containing <% %> patterns
            script_fields = self.find_script_fields(pmd_model, context)
            
            for field_path, field_value, field_name, line_offset in script_fields:
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_null_safety(field_value, field_name, pmd_model.file_path, line_offset, pmd_model, context)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            script_fields = self.find_pod_script_fields(pod_model)
            
            for field_path, field_value, field_name, line_offset in script_fields:
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_null_safety(field_name, pod_model.file_path, line_offset, None, context)
                
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_standalone_script(script_model)

    def _check_null_safety(self, script_content: str, field_name: str, file_path: str, line_offset: int, pmd_model: PMDModel, context=None) -> Generator[Finding, None, None]:
        """Check null safety for a script field, considering conditional execution contexts."""
        try:
            ast = self._parse_script_content(script_content, context)
            if not ast:
                return
            
            # Determine safe variables based on field context
            safe_variables = self._get_safe_variables_for_field(field_name, pmd_model)
            
            # Find unsafe accesses with context awareness
            unsafe_accesses = self._find_unsafe_property_accesses_with_context(ast, safe_variables)
            
            for access_info in unsafe_accesses:
                line_number = line_offset + access_info['line'] - 1
                
                yield Finding(
                    rule=self,
                    message=f"Potentially unsafe property access: {access_info['chain']} - consider using null coalescing (??) or empty checks",
                    line=line_number,
                    column=1,
                    file_path=file_path
                )
                
        except Exception as e:
            print(f"Warning: Failed to analyze {field_name} in {file_path}: {e}")
            return
    
    def _get_safe_variables_for_field(self, field_name: str, pmd_model: PMDModel) -> Set[str]:
        """Determine which variables are safe based on the field context (exclude/render conditions)."""
        safe_variables = set()
        
        # Check if this field is within an endpoint context
        if self._is_endpoint_field(field_name, pmd_model):
            safe_variables.update(self._get_endpoint_safe_variables(field_name, pmd_model))
        
        # Check if this field is within a widget context  
        elif self._is_widget_field(field_name, pmd_model):
            safe_variables.update(self._get_widget_safe_variables(field_name, pmd_model))
        
        return safe_variables
    
    def _is_endpoint_field(self, field_name: str, pmd_model: PMDModel) -> bool:
        """Check if a field is within an endpoint context."""
        return 'inboundEndpoints' in field_name or 'outboundEndpoints' in field_name
    
    def _is_widget_field(self, field_name: str, pmd_model: PMDModel) -> bool:
        """Check if a field is within a widget context."""
        return 'presentation' in field_name and ('widgets' in field_name or 'value' in field_name or 'onChange' in field_name)
    
    def _get_endpoint_safe_variables(self, field_name: str, pmd_model: PMDModel) -> Set[str]:
        """Get safe variables from endpoint exclude conditions and adjacent fields."""
        safe_variables = set()
        
        # Find the endpoint that contains this field
        endpoint = self._find_endpoint_for_field(field_name, pmd_model)
        if endpoint:
            # Check exclude condition (endpoints only have exclude, not render)
            if 'exclude' in endpoint:
                exclude_condition = endpoint['exclude']
                safe_variables.update(self._extract_checked_variables(exclude_condition))
            
            # If this field is within an endpoint that has an exclude condition,
            # ALL script fields in that endpoint are safe (not just url/onSend)
            # because if exclude returns true, the entire endpoint doesn't execute
            if 'exclude' in endpoint:
                # Extract variables from ALL script fields in this endpoint
                for field_key, field_value in endpoint.items():
                    if isinstance(field_value, str) and field_value.strip().startswith('<%'):
                        safe_variables.update(self._extract_checked_variables(field_value))
        
        return safe_variables
    
    def _find_endpoint_for_field(self, field_name: str, pmd_model: PMDModel) -> dict:
        """Find the endpoint that contains the given field."""
        # Parse field name like "inboundEndpoints.0.onSend" or "outboundEndpoints.1.url"
        if 'inboundEndpoints' in field_name:
            parts = field_name.split('.')
            if len(parts) >= 2 and parts[0] == 'inboundEndpoints':
                try:
                    index = int(parts[1])
                    if 0 <= index < len(pmd_model.inboundEndpoints):
                        return pmd_model.inboundEndpoints[index]
                except (ValueError, IndexError):
                    pass
        elif 'outboundEndpoints' in field_name:
            parts = field_name.split('.')
            if len(parts) >= 2 and parts[0] == 'outboundEndpoints':
                try:
                    index = int(parts[1])
                    if 0 <= index < len(pmd_model.outboundEndpoints):
                        return pmd_model.outboundEndpoints[index]
                except (ValueError, IndexError):
                    pass
        return None
    
    def _get_widget_safe_variables(self, field_name: str, pmd_model: PMDModel) -> Set[str]:
        """Get safe variables from widget render conditions and adjacent fields."""
        safe_variables = set()
        
        # Find the widget that contains this field
        widget = self._find_widget_for_field(field_name, pmd_model)
        if widget:
            # Check render condition
            if 'render' in widget:
                render_condition = widget['render']
                safe_variables.update(self._extract_checked_variables(render_condition))
            
            # If this field is within a widget that has a render condition,
            # ALL script fields in that widget are safe (not just value/onChange)
            # because if render returns false, the entire widget doesn't execute
            if 'render' in widget:
                # Extract variables from ALL script fields in this widget
                for field_key, field_value in widget.items():
                    if isinstance(field_value, str) and field_value.strip().startswith('<%'):
                        safe_variables.update(self._extract_checked_variables(field_value))
        
        return safe_variables
    
    def _find_widget_for_field(self, field_name: str, pmd_model: PMDModel) -> dict:
        """Find the widget that contains the given field."""
        # Parse field name like "presentation.body.children.0.value"
        if 'presentation' in field_name and 'children' in field_name:
            parts = field_name.split('.')
            if len(parts) >= 4 and parts[0] == 'presentation' and parts[2] == 'children':
                try:
                    index = int(parts[3])
                    # Navigate to presentation.body.children[index]
                    if hasattr(pmd_model, 'presentation') and pmd_model.presentation:
                        presentation = pmd_model.presentation
                        if hasattr(presentation, 'body') and presentation.body:
                            body = presentation.body
                            if hasattr(body, 'children') and body.children and 0 <= index < len(body.children):
                                return body.children[index]
                except (ValueError, IndexError, AttributeError):
                    pass
        return None
    


    def _analyze_standalone_script(self, script_model) -> Generator[Finding, None, None]:
        """Analyze standalone script files."""
        try:
            ast = self._parse_script_content(script_model.source)
            if not ast:
                return
            
            unsafe_accesses = self._find_unsafe_property_accesses(ast)
            
            for access_info in unsafe_accesses:
                yield Finding(
                    rule=self,
                    message=f"Potentially unsafe property access: {access_info['chain']} - consider using null coalescing (??) or empty checks",
                    line=access_info['line'],
                    column=1,
                    file_path=script_model.file_path
                )
                
        except Exception as e:
            print(f"Warning: Failed to analyze standalone script {script_model.file_path}: {e}")

    def _extract_checked_variables(self, condition: str) -> Set[str]:
        """Extract variable names that are checked in a condition (like exclude or render)."""
        if not condition or not isinstance(condition, str):
            return set()
        
        # Remove script tags if present
        clean_condition = condition.strip()
        if clean_condition.startswith('<%') and clean_condition.endswith('%>'):
            clean_condition = clean_condition[2:-2].strip()
        
        try:
            ast = self._parse_script_content(clean_condition)
            if not ast:
                return set()
            
            variables = set()
            self._extract_variables_from_ast(ast, variables)
            return variables
        except Exception:
            return set()

    def _extract_variables_from_ast(self, ast: Tree, variables: Set[str]):
        """Recursively extract variable names and property chains that are checked in conditions."""
        if not hasattr(ast, 'data') or not hasattr(ast, 'children'):
            return
        
        # Check for empty/not_empty expressions - these indicate null safety checks
        if ast.data in ['empty_expression', 'not_empty_expression', 'empty_function_expression']:
            # Extract the variable/chain being checked
            if len(ast.children) > 1:
                checked_expr = ast.children[1]
                if checked_expr.data == 'identifier_expression' and len(checked_expr.children) > 0:
                    identifier = checked_expr.children[0].value if hasattr(checked_expr.children[0], 'value') else str(checked_expr.children[0])
                    variables.add(identifier)
                elif checked_expr.data == 'member_dot_expression':
                    # Extract the full property chain being checked
                    chain = self._extract_property_chain(checked_expr)
                    if chain:
                        # Add the root variable and the full chain
                        root_var = chain.split('.')[0]
                        variables.add(root_var)
                        variables.add(chain)
        
        # Check for identifier expressions
        elif ast.data == 'identifier_expression' and len(ast.children) > 0:
            identifier = ast.children[0].value if hasattr(ast.children[0], 'value') else str(ast.children[0])
            variables.add(identifier)
        
        # Check for member dot expressions
        elif ast.data == 'member_dot_expression':
            # Extract the root variable from property access
            if len(ast.children) > 0:
                root_obj = ast.children[0]
                if root_obj.data == 'identifier_expression' and len(root_obj.children) > 0:
                    identifier = root_obj.children[0].value if hasattr(root_obj.children[0], 'value') else str(root_obj.children[0])
                    variables.add(identifier)
                # Also extract the full chain
                chain = self._extract_property_chain(ast)
                if chain:
                    variables.add(chain)
        
        # Recursively check children
        for child in ast.children:
            if hasattr(child, 'data'):  # It's a Tree node
                self._extract_variables_from_ast(child, variables)

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
                'line': chain_info['line']
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
                'line': chain_info['line']
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
    

    def _get_line_number(self, pmd_model: PMDModel, relative_line: int) -> int:
        """Get the absolute line number for a relative line in the script."""
        if not pmd_model.script:
            return 1
            
        # Calculate the script line offset using the utility
        line_offset = LineNumberUtils.calculate_script_line_offset(pmd_model, pmd_model.script)
        return line_offset + relative_line - 1
