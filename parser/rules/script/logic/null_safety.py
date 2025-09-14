from typing import Generator, List, Optional, Dict, Set, Tuple
from lark import Tree
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel
from ...line_number_utils import LineNumberUtils


class ScriptNullSafetyRule(Rule):
    """Validates that property access chains are properly null-safe."""

    ID = "SCRIPT010"
    DESCRIPTION = "Ensures property access chains are protected against null reference exceptions"
    SEVERITY = "WARNING"

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze scripts for unsafe property access patterns, considering conditional execution contexts."""
        for pmd_model in context.pmds.values():
            # Analyze page-level scripts
            yield from self._analyze_pmd_script(pmd_model)
            
            # Analyze endpoint scripts with conditional execution context
            yield from self._analyze_endpoints(pmd_model)
            
            # Analyze widget scripts with conditional execution context  
            yield from self._analyze_widgets(pmd_model)
            
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_standalone_script(script_model)

    def _analyze_pmd_script(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze page-level scripts in PMD files."""
        for script_field in ['script', 'onLoad', 'onSubmit']:
            script_content = getattr(pmd_model, script_field, None)
            if not script_content:
                continue
                
            try:
                ast = self._parse_script_content(script_content)
                if not ast:
                    continue
                
                # Find unsafe accesses without conditional context
                unsafe_accesses = self._find_unsafe_property_accesses(ast)
                
                for access_info in unsafe_accesses:
                    line_number = self._get_line_number(pmd_model, access_info['line'])
                    
                    yield Finding(
                        rule=self,
                        message=f"Potentially unsafe property access: {access_info['chain']} - consider using null coalescing (??) or empty checks",
                        line=line_number,
                        column=1,
                        file_path=pmd_model.file_path
                    )
                    
            except Exception as e:
                print(f"Error analyzing {script_field} in {pmd_model.file_path}: {e}")
                continue

    def _analyze_endpoints(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze endpoint scripts considering exclude conditions."""
        # Analyze inbound endpoints
        for i, endpoint in enumerate(pmd_model.inboundEndpoints or []):
            yield from self._analyze_endpoint_script(pmd_model, endpoint, f"endPoints[{i}]")
        
        # Analyze outbound endpoints  
        if hasattr(pmd_model, 'outboundData') and pmd_model.outboundData:
            outbound_endpoints = getattr(pmd_model.outboundData, 'outboundEndPoints', []) or []
            for i, endpoint in enumerate(outbound_endpoints):
                yield from self._analyze_endpoint_script(pmd_model, endpoint, f"outboundData.outboundEndPoints[{i}]")

    def _analyze_endpoint_script(self, pmd_model: PMDModel, endpoint: dict, endpoint_path: str) -> Generator[Finding, None, None]:
        """Analyze a single endpoint's scripts considering its exclude condition."""
        exclude_condition = endpoint.get('exclude')
        on_send_script = endpoint.get('onSend')
        url_script = endpoint.get('url')
        
        # Extract variables that are checked in exclude condition
        exclude_variables = set()
        if exclude_condition:
            exclude_variables = self._extract_checked_variables(exclude_condition)
        
        # Analyze onSend script
        if on_send_script:
            yield from self._analyze_conditional_script(
                pmd_model, on_send_script, exclude_variables, 
                f"{endpoint_path}.onSend", 
                f"Variables checked in exclude condition: {', '.join(exclude_variables) if exclude_variables else 'none'}"
            )
        
        # Analyze url script
        if url_script:
            yield from self._analyze_conditional_script(
                pmd_model, url_script, exclude_variables,
                f"{endpoint_path}.url",
                f"Variables checked in exclude condition: {', '.join(exclude_variables) if exclude_variables else 'none'}"
            )

    def _analyze_widgets(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze widget scripts considering render conditions."""
        if not pmd_model.presentation:
            return
            
        # Recursively analyze all widgets in the presentation
        yield from self._analyze_widget_recursive(pmd_model, pmd_model.presentation.body, "presentation.body")

    def _analyze_widget_recursive(self, pmd_model: PMDModel, widget: dict, widget_path: str) -> Generator[Finding, None, None]:
        """Recursively analyze widgets and their scripts."""
        if not isinstance(widget, dict):
            return
            
        # Check for render condition
        render_condition = widget.get('render')
        render_variables = set()
        if render_condition:
            render_variables = self._extract_checked_variables(render_condition)
        
        # Analyze widget scripts that are conditionally executed
        for script_field in ['value', 'onChange', 'onClick', 'enabled']:
            script_content = widget.get(script_field)
            if script_content and isinstance(script_content, str) and script_content.strip().startswith('<%'):
                yield from self._analyze_conditional_script(
                    pmd_model, script_content, render_variables,
                    f"{widget_path}.{script_field}",
                    f"Variables checked in render condition: {', '.join(render_variables) if render_variables else 'none'}"
                )
        
        # Recursively analyze children
        children = widget.get('children', [])
        if isinstance(children, list):
            for i, child in enumerate(children):
                yield from self._analyze_widget_recursive(pmd_model, child, f"{widget_path}.children[{i}]")

    def _analyze_conditional_script(self, pmd_model: PMDModel, script_content: str, safe_variables: Set[str], 
                                  script_path: str, context_message: str) -> Generator[Finding, None, None]:
        """Analyze a script that runs in a conditional execution context."""
        try:
            ast = self._parse_script_content(script_content)
            if not ast:
                return
            
            # Find unsafe accesses, but exclude variables that are known to be safe due to conditional execution
            unsafe_accesses = self._find_unsafe_property_accesses_with_context(ast, safe_variables)
            
            for access_info in unsafe_accesses:
                line_number = self._get_line_number(pmd_model, access_info['line'])
                
                yield Finding(
                    rule=self,
                    message=f"Potentially unsafe property access: {access_info['chain']} - {context_message}",
                    line=line_number,
                    column=1,
                    file_path=pmd_model.file_path
                )
                
        except Exception as e:
            print(f"Error analyzing conditional script {script_path} in {pmd_model.file_path}: {e}")

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
            print(f"Error analyzing standalone script {script_model.file_path}: {e}")

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
        
        # If the root object is known to be safe due to conditional execution, skip this chain
        if root_object in safe_variables:
            return False
        
        # Apply the same safety checks as the original method
        if self._is_global_object(root_object):
            return False
            
        if self._is_protected_chain(ast, chain):
            return False
            
        # Check if any parent chain is protected
        for i in range(len(parts) - 1):
            partial_chain = '.'.join(parts[:i+1])
            if self._is_protected_chain(ast, partial_chain):
                return False
        
        return True

    def _parse_script_content(self, script_content: str) -> Optional[Tree]:
        """Parse script content using the PMD script parser."""
        if not script_content or not script_content.strip():
            return None
        
        # Remove script tags if present
        clean_content = script_content.strip()
        if clean_content.startswith('<%') and clean_content.endswith('%>'):
            clean_content = clean_content[2:-2].strip()
        
        try:
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception:
            return None

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
        global_objects = {'console', 'pageVariables', 'sessionVariables', 'queryParams', }
        
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
