from typing import Generator, List, Optional, Dict, Set, Tuple
from lark import Tree
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, PODModel
from ...line_number_utils import LineNumberUtils


class ScriptNullSafetyRule(Rule):
    """Validates that property access chains are properly null-safe."""

    DESCRIPTION = "Ensures property access chains are protected against null reference exceptions"
    SEVERITY = "SEVERE"

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze scripts for unsafe property access patterns, considering conditional execution contexts."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            # Use the generic script field finder to detect all fields containing <% %> patterns
            script_fields = self.find_script_fields(pmd_model)
            
            for field_path, field_value, field_name, line_offset in script_fields:
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_null_safety(field_value, field_name, pmd_model.file_path, line_offset, pmd_model)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            script_fields = self.find_pod_script_fields(pod_model)
            
            for field_path, field_value, field_name, line_offset in script_fields:
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_null_safety(field_value, field_name, pod_model.file_path, line_offset, None)
                
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_standalone_script(script_model)

    def _check_null_safety(self, script_content: str, field_name: str, file_path: str, line_offset: int, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Check null safety for a script field, considering conditional execution contexts."""
        try:
            ast = self._parse_script_content(script_content)
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
        """Get safe variables from endpoint exclude conditions."""
        safe_variables = set()
        
        # Find the endpoint that contains this field
        endpoint = self._find_endpoint_for_field(field_name, pmd_model)
        if endpoint and 'exclude' in endpoint:
            exclude_condition = endpoint['exclude']
            safe_variables.update(self._extract_checked_variables(exclude_condition))
        
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
        """Get safe variables from widget render conditions."""
        safe_variables = set()
        
        # Find the widget that contains this field
        widget = self._find_widget_for_field(field_name, pmd_model)
        if widget and 'render' in widget:
            render_condition = widget['render']
            safe_variables.update(self._extract_checked_variables(render_condition))
        
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
        """Recursively extract variable names from an AST."""
        if not hasattr(ast, 'data') or not hasattr(ast, 'children'):
            return
        
        # Check for identifier expressions
        if ast.data == 'identifier_expression' and len(ast.children) > 0:
            identifier = ast.children[0].value if hasattr(ast.children[0], 'value') else str(ast.children[0])
            variables.add(identifier)
        elif ast.data == 'member_dot_expression':
            # Extract the root variable from property access
            if len(ast.children) > 0:
                root_obj = ast.children[0]
                if root_obj.data == 'identifier_expression' and len(root_obj.children) > 0:
                    identifier = root_obj.children[0].value if hasattr(root_obj.children[0], 'value') else str(root_obj.children[0])
                    variables.add(identifier)
        
        # Recursively check children
        for child in ast.children:
            if hasattr(child, 'data'):  # It's a Tree node
                self._extract_variables_from_ast(child, variables)

    def _find_unsafe_property_accesses_with_context(self, ast: Tree, safe_variables: Set[str]) -> List[dict]:
        """Find unsafe property accesses, excluding variables known to be safe due to conditional execution."""
        unsafe_accesses = []
        
        for node in ast.iter_subtrees():
            if node.data == 'member_dot_expression':
                chain = self._extract_property_chain(node)
                if chain and self._is_unsafe_chain_with_context(ast, chain, safe_variables):
                    unsafe_accesses.append({
                        'chain': chain,
                        'line': getattr(node.meta, 'line', 1)
                    })
        
        return unsafe_accesses

    def _is_unsafe_chain_with_context(self, ast: Tree, chain: str, safe_variables: Set[str]) -> bool:
        """Check if a property access chain is unsafe, considering conditional execution context."""
        parts = chain.split('.')
        
        if len(parts) < 2:
            return False
        
        root_object = parts[0]
        
        # If the root object is known to be safe due to conditional execution,
        # only consider direct property access on that variable as safe
        if root_object in safe_variables:
            # For chains like "getUser.data.something", if "getUser.data" is safe,
            # then "getUser.data.something" is only safe if it's a direct property access
            if len(parts) == 2:
                # Direct property access on safe variable is safe
                return False
            else:
                # Nested property access on safe variable needs further checking
                # Check if the remaining chain (after the safe variable) is protected
                remaining_chain = '.'.join(parts[1:])
                if self._is_protected_chain(ast, remaining_chain):
                    return False
                # Also check if any partial chain from the safe variable onwards is protected
                for i in range(1, len(parts)):
                    partial_chain = '.'.join(parts[:i+1])
                    if self._is_protected_chain(ast, partial_chain):
                        return False
                # If no protection found, this nested access is unsafe
                return True
        
        # Global objects are guaranteed to exist, but their properties are not
        # So we need to check if the chain is protected or if it's just a direct property access
        if self._is_global_object(root_object):
            # For global objects, only direct property access (like "self.data") is safe
            # Nested access (like "self.data.name") needs protection
            if len(parts) == 2:
                # Direct property access on global object is safe
                return False
            else:
                # Nested property access on global object needs protection
                # Check if the chain is protected
                if self._is_protected_chain(ast, chain):
                    return False
                # Check if any partial chain is protected
                for i in range(1, len(parts)):
                    partial_chain = '.'.join(parts[:i+1])
                    if self._is_protected_chain(ast, partial_chain):
                        return False
                # If no protection found, this nested access is unsafe
                return True
            
        if self._is_protected_chain(ast, chain):
            return False
            
        # Check if any parent chain is protected
        for i in range(len(parts) - 1):
            partial_chain = '.'.join(parts[:i+1])
            if self._is_protected_chain(ast, partial_chain):
                return False
                
        return True


    def _find_unsafe_property_accesses(self, ast: Tree) -> List[dict]:
        """Find property access chains that lack null safety."""
        unsafe_accesses = []       

        # Find all member access expressions
        for node in ast.iter_subtrees():
            if node.data == 'member_dot_expression':
                chain = self._extract_property_chain(node)
                if chain and self._is_unsafe_chain(ast, chain):
                    unsafe_accesses.append({
                        'chain': chain,
                        'line': getattr(node.meta, 'line', 1)
                    })

        return unsafe_accesses
    
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
        """Check if a property access chain is unsafe (lacks null safety)."""
        # Split the chain to get individual parts
        parts = chain.split('.')

        if len(parts) < 2:
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
