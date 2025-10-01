"""Script unused functions rule using unified architecture."""

from typing import Generator, Set, List, Tuple
from ...script.shared import ScriptRuleBase
from ...base import Finding
from .unused_functions_detector import UnusedFunctionsDetector


class ScriptUnusedFunctionRule(ScriptRuleBase):
    """Validates that functions are not declared but never used."""

    DESCRIPTION = "Ensures functions are not declared but never used"
    SEVERITY = "WARNING"
    DETECTOR = UnusedFunctionsDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _analyze_fields(self, model, script_fields: List[Tuple[str, str, str, int]], context=None) -> Generator[Finding, None, None]:
        """Analyze script fields with proper global/local scoping."""
        # Separate global and local script fields
        global_fields = []
        local_fields = []
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                if self._is_global_script_field(field_name):
                    global_fields.append((field_path, field_value, field_name, line_offset))
                else:
                    local_fields.append((field_path, field_value, field_name, line_offset))
        
        # Analyze global functions (can be called from anywhere)
        if global_fields:
            yield from self._analyze_global_functions(model, global_fields, local_fields, context)
        
        # Analyze local functions (only checked within their own scope)
        yield from self._analyze_local_functions(model, local_fields, context)

    def _is_global_script_field(self, field_name: str) -> bool:
        """Check if a script field is in global scope (script section)."""
        return 'script' in field_name.lower()

    def _analyze_global_functions(self, model, global_fields: List[Tuple[str, str, str, int]], 
                                 local_fields: List[Tuple[str, str, str, int]], context=None) -> Generator[Finding, None, None]:
        """Analyze global functions - can be called from anywhere on the page."""
        # Collect all function declarations from global fields
        all_declared_functions = set()
        all_function_calls = set()
        global_field_asts = {}
        
        # First pass: collect declarations from global fields
        for field_path, field_value, field_name, line_offset in global_fields:
            ast = self._parse_script_content(field_value, context)
            if ast:
                global_field_asts[(field_path, field_name, line_offset)] = ast
                all_declared_functions.update(self._collect_function_declarations(ast))
        
        # Second pass: collect calls from ALL fields (global + local)
        all_fields = global_fields + local_fields
        for field_path, field_value, field_name, line_offset in all_fields:
            ast = self._parse_script_content(field_value, context)
            if ast:
                all_function_calls.update(self._collect_function_calls(ast))
        
        # Third pass: check for unused global functions
        for (field_path, field_name, line_offset), ast in global_field_asts.items():
            detector = self.DETECTOR(model.file_path, line_offset, all_declared_functions, all_function_calls)
            violations = detector.detect(ast, field_name)
            
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=model.file_path
                )

    def _analyze_local_functions(self, model, local_fields: List[Tuple[str, str, str, int]], 
                                context=None) -> Generator[Finding, None, None]:
        """Analyze local functions - only checked within their own scope."""
        for field_path, field_value, field_name, line_offset in local_fields:
            ast = self._parse_script_content(field_value, context)
            if ast:
                # For local functions, only check within the same field
                local_declared_functions = self._collect_function_declarations(ast)
                local_function_calls = self._collect_function_calls(ast)
                
                detector = self.DETECTOR(model.file_path, line_offset, local_declared_functions, local_function_calls)
                violations = detector.detect(ast, field_name)
                
                for violation in violations:
                    yield Finding(
                        rule=self,
                        message=violation.message,
                        line=violation.line,
                        file_path=model.file_path
                    )

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector - not used in file-level analysis."""
        # This method is not used when _analyze_fields is overridden
        # Return empty generator to avoid NoneType iteration errors
        yield from []
    
    def _collect_function_declarations(self, ast) -> Set[str]:
        """
        Collect all function declarations from the AST.
        
        In PMD Script, all functions are anonymous and assigned to variables.
        We track the variable names, not function names.
        
        Patterns to detect:
        - var funcName = function() { ... }
        - let funcName = function() { ... }
        - const funcName = function() { ... }
        - var funcName = () => { ... }  (arrow functions)
        """
        declared_functions = set()
        
        try:
            # Find all variable declarations
            for var_decl_node in ast.find_data('variable_statement'):
                # Look for variables that are assigned to functions
                variable_names = self._extract_function_variable_names(var_decl_node)
                declared_functions.update(variable_names)
        except Exception:
            pass  # If AST traversal fails, return empty set
        
        return declared_functions
    
    def _collect_function_calls(self, ast) -> Set[str]:
        """
        Collect all references to identifiers that could be function calls.
        
        This includes:
        - Direct calls: myFunc()
        - Function references passed as arguments: array.map(myFunc)
        - Function references in expressions: var x = myFunc
        """
        function_calls = set()
        
        try:
            # Collect all identifiers that are referenced (not declarations)
            # We'll filter by collecting identifiers used in various contexts
            
            # 1. Direct function calls
            for call_node in ast.find_data('call_expression'):
                func_name = self._extract_identifier_from_expression(call_node.children[0] if call_node.children else None)
                if func_name:
                    function_calls.add(func_name)
            
            # 2. Identifiers used in member expressions (e.g., obj.method())
            # These are already handled by call_expression above if they're called
            
            # 3. Identifiers used as arguments or in expressions
            # Parse through all expression nodes and collect standalone identifiers
            for tree in ast.iter_subtrees():
                # Look for identifiers that aren't part of variable declarations
                if tree.data not in ('variable_declaration', 'variable_statement'):
                    for child in tree.children:
                        if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                            function_calls.add(child.value)
                            
        except Exception:
            pass  # If AST traversal fails, return empty set
        
        return function_calls
    
    def _extract_identifier_from_expression(self, node) -> str:
        """Extract identifier name from an expression node."""
        if node is None:
            return ""
        if hasattr(node, 'value'):
            return node.value
        if hasattr(node, 'children') and node.children:
            # For member expressions, get the last identifier (method name)
            for child in node.children:
                if hasattr(child, 'value'):
                    return child.value
        return ""
    
    def _extract_function_variable_names(self, var_statement_node) -> Set[str]:
        """
        Extract variable names that are assigned to functions.
        
        For example, from: var myFunc = function() { ... }
        We extract: "myFunc"
        """
        function_vars = set()
        
        try:
            # Traverse the variable statement to find variable declarations
            for child in var_statement_node.iter_subtrees():
                if child.data == 'variable_declaration':
                    # Get the variable name (first child is IDENTIFIER)
                    if len(child.children) >= 1:
                        identifier = child.children[0]
                        if hasattr(identifier, 'value'):
                            var_name = identifier.value
                            
                            # Check if it's assigned to a function
                            # Look for initializer -> function_expression or arrow_function_expression
                            if len(child.children) >= 2:
                                initializer = child.children[1]
                                if self._is_function_assignment(initializer):
                                    function_vars.add(var_name)
        except Exception:
            pass
        
        return function_vars
    
    def _is_function_assignment(self, initializer_node) -> bool:
        """Check if an initializer node assigns a function."""
        try:
            # Check if the initializer contains a function expression or arrow function
            for subtree in initializer_node.iter_subtrees():
                if subtree.data in ('function_expression', 'arrow_function_expression'):
                    return True
        except Exception:
            pass
        return False