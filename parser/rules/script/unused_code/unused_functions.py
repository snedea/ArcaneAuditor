from typing import Set, Dict
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, PodModel


class ScriptUnusedFunctionRule(Rule):
    """Validates that functions are not declared but never used."""
    
    DESCRIPTION = "Ensures functions are not declared but never used"
    SEVERITY = "WARNING"

    def analyze(self, context: ProjectContext):
        """Main entry point - analyze all PMD models, POD models, and standalone script files in the context."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model, context)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model, context)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)

    def visit_pmd(self, pmd_model: PMDModel, context=None):
        """Analyzes script fields in a PMD model for unused functions."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model, context)
        
        # Build a registry of all functions declared across all script fields
        all_declared_functions = self._build_function_registry(pmd_model)
        
        # Build a registry of all function calls across all script fields
        all_function_calls = self._build_function_call_registry(pmd_model)
        
        # Analyze each script field for unused functions
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_unused_functions_in_field(
                    field_value, field_name, pmd_model, line_offset,
                    all_declared_functions, all_function_calls, context
                )

    def visit_pod(self, pod_model: PodModel, context=None):
        """Analyzes script fields in a POD model for unused functions."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        # Build a registry of all functions declared across all POD script fields
        all_declared_functions = self._build_pod_function_registry(pod_model)
        
        # Build a registry of all function calls across all POD script fields
        all_function_calls = self._build_pod_function_call_registry(pod_model)
        
        # Analyze each script field for unused functions
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_unused_functions_in_field(
                    field_value, field_name, pod_model, line_offset,
                    all_declared_functions, all_function_calls, context
                )

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for unused functions."""
        try:
            # For standalone scripts, build registries from the single file
            script_fields = [("script", script_model.source, "script", 1)]
            
            all_declared_functions = {}
            all_function_calls = set()
            
            # Build registries from the script content
            ast = self._parse_script_content(script_model.source, None)
            if ast:
                field_functions = self._extract_function_declarations(ast, "script", 1)
                all_declared_functions.update(field_functions)
                
                field_calls = self._extract_function_calls(ast)
                all_function_calls.update(field_calls)
            
            # Check for unused functions
            yield from self._check_unused_functions_in_field(
                script_model.source, "script", script_model, 1,
                all_declared_functions, all_function_calls, None
            )
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _build_function_registry(self, pmd_model: PMDModel) -> Dict[str, Dict]:
        """Build a registry of all functions declared in the PMD model."""
        function_registry = {}
        script_fields = self.find_script_fields(pmd_model, None)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                ast = self._parse_script_content(field_value)
                if ast:
                    field_functions = self._extract_function_declarations(ast, field_name, line_offset)
                    function_registry.update(field_functions)
        
        return function_registry

    def _build_function_call_registry(self, pmd_model: PMDModel) -> Set[str]:
        """Build a registry of all function calls across the PMD model."""
        function_calls = set()
        script_fields = self.find_script_fields(pmd_model, None)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                ast = self._parse_script_content(field_value)
                if ast:
                    field_calls = self._extract_function_calls(ast)
                    function_calls.update(field_calls)
        
        return function_calls

    def _check_unused_functions_in_field(self, script_content, field_name, pmd_model, line_offset, 
                                       all_declared_functions, all_function_calls, context=None):
        """Check for unused functions in a specific script field."""
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Get functions declared in this specific field
        field_functions = self._extract_function_declarations(ast, field_name, line_offset)
        
        # Check each function declared in this field
        for func_name, func_info in field_functions.items():
            if func_name not in all_function_calls:
                # Function is declared but never called anywhere
                yield Finding(
                    rule=self,
                    message=f"Function '{func_name}' is declared but never used. Consider removing it.",
                    line=func_info['line'],
                    column=1,
                    file_path=pmd_model.file_path
                )

    def _extract_function_declarations(self, ast, field_name, line_offset) -> Dict[str, Dict]:
        """Extract function declarations from AST."""
        functions = {}
        
        def _search_functions(node, current_line_offset=0):
            if hasattr(node, 'data'):
                # Skip function_expression nodes - they are handled by variable_declaration
                # The function_expression node contains parameters, not the function name
                if node.data == 'function_expression':
                    pass
                
                elif node.data == 'variable_declaration':
                    # Check if this is a function assignment (let func = function() { ... } or let func = () => { ... })
                    if len(node.children) >= 2:
                        var_name_node = node.children[0]
                        func_expr = node.children[1]
                        
                        if (hasattr(var_name_node, 'value') and 
                            hasattr(func_expr, 'data') and 
                            func_expr.data in ['function_expression', 'arrow_function', 'arrow_function_expression']):
                            
                            func_name = var_name_node.value
                            # Get line number from var_name_node
                            base_line = 1
                            if hasattr(var_name_node, 'meta') and hasattr(var_name_node.meta, 'line'):
                                base_line = var_name_node.meta.line
                            elif hasattr(var_name_node, 'line'):
                                base_line = var_name_node.line
                            line_number = base_line + line_offset - 1
                            
                            functions[func_name] = {
                                'line': line_number,
                                'field': field_name,
                                'type': 'function'
                            }
            
            # Recursively search children
            if hasattr(node, 'children'):
                for child in node.children:
                    _search_functions(child, current_line_offset)
        
        _search_functions(ast, line_offset)
        return functions

    def _extract_function_calls(self, ast) -> Set[str]:
        """Extract function calls from AST."""
        function_calls = set()
        
        def _search_function_calls(node):
            if hasattr(node, 'data'):
                if node.data == 'arguments_expression':
                    # Handle function calls with arguments (func(arg1, arg2))
                    if len(node.children) > 0:
                        func_name_node = node.children[0]
                        if hasattr(func_name_node, 'data') and func_name_node.data == 'identifier_expression':
                            if len(func_name_node.children) > 0:
                                func_name = func_name_node.children[0].value
                                function_calls.add(func_name)
                
                elif node.data == 'call_expression':
                    # Extract function name from call expression
                    if len(node.children) > 0:
                        func_name_node = node.children[0]
                        if hasattr(func_name_node, 'data') and func_name_node.data == 'identifier_expression':
                            if len(func_name_node.children) > 0:
                                func_name = func_name_node.children[0].value
                                function_calls.add(func_name)
                
                elif node.data == 'statement_list':
                    # Handle function calls within statement lists
                    # Look for identifier_expression followed by parenthesized_expression
                    children = node.children if hasattr(node, 'children') else []
                    for i in range(len(children) - 1):
                        current = children[i]
                        next_node = children[i + 1]
                        
                        if (hasattr(current, 'data') and current.data == 'identifier_expression' and
                            hasattr(next_node, 'data') and next_node.data == 'parenthesized_expression'):
                            # This looks like a function call
                            if len(current.children) > 0:
                                func_name = current.children[0].value
                                function_calls.add(func_name)
                
                elif node.data == 'member_dot_expression':
                    # Handle method calls like obj.method()
                    if len(node.children) >= 2:
                        # Check if this is followed by a call expression
                        # This is a bit tricky - we need to check the parent context
                        pass
                
                elif node.data == 'curly_literal_expression':
                    # Handle object literal exports like { "funcName": funcName }
                    self._extract_object_literal_exports(node, function_calls)
                
                elif node.data == 'curly_literal':
                    # Handle object literal exports like { "funcName": funcName }
                    self._extract_object_literal_exports(node, function_calls)
            
            # Recursively search children
            if hasattr(node, 'children'):
                for child in node.children:
                    _search_function_calls(child)
        
        _search_function_calls(ast)
        return function_calls

    def _extract_object_literal_exports(self, node, function_calls):
        """Extract function references from object literal exports."""
        if not hasattr(node, 'children'):
            return
        
        # Handle curly_literal structure: literal_expression, identifier_expression, property_expression_assignment, ...
        children = node.children
        i = 0
        while i < len(children):
            child = children[i]
            
            # Look for identifier_expression (function references)
            if hasattr(child, 'data') and child.data == 'identifier_expression':
                if len(child.children) > 0:
                    func_name = child.children[0].value
                    function_calls.add(func_name)
            
            # Look for property_expression_assignment
            elif hasattr(child, 'data') and child.data == 'property_expression_assignment':
                if len(child.children) >= 2:
                    value_node = child.children[1]
                    if hasattr(value_node, 'data') and value_node.data == 'identifier_expression':
                        if len(value_node.children) > 0:
                            func_name = value_node.children[0].value
                            function_calls.add(func_name)
            
            # Recursively search children for nested structures
            if hasattr(child, 'children'):
                for grandchild in child.children:
                    if hasattr(grandchild, 'data') and grandchild.data == 'identifier_expression':
                        if len(grandchild.children) > 0:
                            func_name = grandchild.children[0].value
                            function_calls.add(func_name)
            
            i += 1

    def _build_pod_function_registry(self, pod_model: PodModel) -> Dict[str, Dict]:
        """Build a registry of all functions declared in the POD model."""
        function_registry = {}
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                ast = self._parse_script_content(field_value, None)
                if ast:
                    field_functions = self._extract_function_declarations(ast, field_name, line_offset)
                    function_registry.update(field_functions)
        
        return function_registry

    def _build_pod_function_call_registry(self, pod_model: PodModel) -> Set[str]:
        """Build a registry of all function calls in the POD model."""
        all_function_calls = set()
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                ast = self._parse_script_content(field_value)
                if ast:
                    field_calls = self._extract_function_calls(ast)
                    all_function_calls.update(field_calls)
        
        return all_function_calls
