from typing import Generator, List, Optional
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
        """Analyze scripts for unsafe property access patterns."""
        for pmd_model in context.pmds.values():
            if not pmd_model.script:
                continue

            try:
                ast = self._parse_script_content(pmd_model.script)
                if not ast:
                    continue
          
                # Find all property access chains that might be unsafe
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
                print(f"Error analyzing null safety in {pmd_model.file_path}: {e}")
                continue


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
        global_objects = {
            # Browser/DOM APIs
            'window', 'document', 'navigator', 'location', 'history', 'screen',
            
            # Console and logging
            'console',
            
            # JavaScript built-ins
            'Math', 'Date', 'JSON', 'Array', 'Object', 'String', 'Number', 'Boolean',
            'RegExp', 'Error', 'Promise', 'Symbol', 'Map', 'Set', 'WeakMap', 'WeakSet',
            
            # Common libraries that are typically available globally
            'jQuery', '$', 'lodash', '_', 'moment', 'axios', 'fetch',
            
            # Workday-specific globals (if any)
            'workday', 'wd'
        }
        
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
