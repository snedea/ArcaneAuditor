from ...base import Rule, Finding
from ....models import PMDModel, PodModel


class ScriptUnusedVariableRule(Rule):
    """Validates that all declared variables are used with proper scoping."""
    
    DESCRIPTION = "Ensures all declared variables are used (prevents dead code) with proper scoping awareness"
    SEVERITY = "WARNING"

    def analyze(self, context):
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
        """Analyzes script fields in a PMD model with scope awareness."""
        script_fields = self.find_script_fields(pmd_model, context)
        
        # Build a global function registry from the main script section
        global_functions = self._build_global_function_registry(pmd_model, context)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                is_global_scope = (field_name == 'script')
                yield from self._check_unused_variables_with_scope(
                    field_value, field_name, pmd_model.file_path, 
                    is_global_scope, global_functions, line_offset, context
                )

    def visit_pod(self, pod_model: PodModel, context=None):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        # PODs don't have a global script section like PMDs, so no global functions
        global_functions = set()
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                # POD scripts are typically local scope (widget handlers, endpoint handlers)
                is_global_scope = False
                yield from self._check_unused_variables_with_scope(
                    field_value, field_name, pod_model.file_path, 
                    is_global_scope, global_functions, line_offset, context
                )

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for unused variables."""
        try:
            # Standalone scripts don't have global functions from other sections
            global_functions = set()
            is_global_scope = True  # The entire script file is global scope
            yield from self._check_unused_variables_with_scope(
                script_model.source, "script", script_model.file_path, 
                is_global_scope, global_functions, 1, None
            )
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _build_global_function_registry(self, pmd_model: PMDModel, context=None):
        """Build a registry of functions declared in the global script section."""
        global_functions = set()
        
        if pmd_model.script:
            ast = self._parse_script_content(pmd_model.script, context)
            if ast:
                global_functions = self._find_function_declarations(ast)
        
        return global_functions

    def _check_unused_variables_with_scope(self, script_content, field_name, file_path, is_global_scope, global_functions, line_offset=1, context=None):
        """Check for unused variables with proper scoping awareness."""
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Analyze the script with scope awareness
        scope_analysis = self._analyze_script_scope(ast, is_global_scope, global_functions)
        
        # Check for unused variables in each scope
        for scope_info in scope_analysis['scopes']:
            scope_type = scope_info['type']
            scope_name = scope_info['name']
            declared_vars = scope_info['declared_vars']
            used_vars = scope_info['used_vars']
            
            # Check for unused variables in this scope
            for var_name, var_info in declared_vars.items():
                if var_name not in used_vars:
                    # Skip function declarations - they're handled by ScriptUnusedFunctionRule
                    if var_info.get('is_function', False):
                        continue
                    
                    # Regular unused variable handling
                    scope_context = f" in {scope_type} '{scope_name}'" if scope_name != 'global' else ""
                    
                    # Use line_offset as base, add relative line if available
                    relative_line = var_info.get('line', 1) or 1
                    line_number = line_offset + relative_line - 1
                    
                    yield Finding(
                        rule=self,
                        message=f"File section '{field_name}' declares unused variable '{var_name}'{scope_context}. Consider removing it.",
                        line=line_number,
                        column=1,
                        file_path=file_path
                    )

    def _analyze_script_scope(self, ast, is_global_scope, global_functions):
        """Analyze script with proper scoping."""
        analysis = {
            'scopes': [],
            'global_functions': global_functions
        }
        
        # Create global scope
        global_scope = {
            'type': 'global',
            'name': 'global',
            'declared_vars': {},
            'used_vars': set(),
            'functions': {}
        }
        
        # Analyze the AST
        self._analyze_ast_scope(ast, global_scope, is_global_scope, global_functions)
        analysis['scopes'].append(global_scope)
        
        # Add function scopes
        for func_name, func_expr in global_scope['functions'].items():
            func_scope = {
                'type': 'function',
                'name': func_name,
                'declared_vars': {},
                'used_vars': set(),
                'functions': {}
            }
            
            # Analyze function body
            self._analyze_function_body(func_expr, func_scope)
            
            # Only add function scope if it has variables to check
            if func_scope['declared_vars'] or func_scope['used_vars']:
                analysis['scopes'].append(func_scope)
        
        return analysis

    def _analyze_ast_scope(self, node, current_scope, is_global_scope, global_functions):
        """Recursively analyze AST with scope awareness."""
        if hasattr(node, 'data'):
            if node.data == 'variable_declaration':
                # Handle variable declarations
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    var_name = node.children[0].value
                    # Get line number from the first token in the node
                    line_number = None
                    if hasattr(node, 'children') and len(node.children) > 0:
                        for child in node.children:
                            if hasattr(child, 'meta') and hasattr(child.meta, 'line'):
                                line_number = child.meta.line
                                break
                            elif hasattr(child, 'line') and child.line is not None:
                                line_number = child.line
                                break
                    
                    # Check if this is a function declaration
                    is_function = False
                    if len(node.children) >= 2:
                        func_expr = node.children[1]
                        if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                            current_scope['functions'][var_name] = func_expr
                            is_function = True
                    
                    current_scope['declared_vars'][var_name] = {
                        'line': line_number,
                        'type': 'function' if is_function else 'variable',
                        'is_function': is_function
                    }
                            
            elif node.data == 'identifier_expression':
                # Handle variable usage
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    var_name = node.children[0].value
                    current_scope['used_vars'].add(var_name)
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                self._analyze_ast_scope(child, current_scope, is_global_scope, global_functions)

    def _analyze_function_body(self, func_expr, func_scope):
        """Analyze function body for local variables and parameters."""
        # First, extract function parameters
        self._extract_function_parameters(func_expr, func_scope)
        
        # Then analyze function body (source_elements)
        for child in func_expr.children:
            if hasattr(child, 'data') and child.data == 'source_elements':
                self._analyze_ast_scope(child, func_scope, False, set())
                break

    def _extract_function_parameters(self, func_expr, func_scope):
        """Extract function parameters and add them to the scope."""
        # Look for formal_parameter_list in function expression
        for child in func_expr.children:
            if hasattr(child, 'data') and child.data == 'formal_parameter_list':
                # Extract parameter names
                for param_child in child.children:
                    if hasattr(param_child, 'value'):
                        param_name = param_child.value
                        # Get line number from param_child
                        line_number = None
                        if hasattr(param_child, 'meta') and hasattr(param_child.meta, 'line'):
                            line_number = param_child.meta.line
                        elif hasattr(param_child, 'line'):
                            line_number = param_child.line
                        
                        func_scope['declared_vars'][param_name] = {
                            'line': line_number,
                            'type': 'parameter'
                        }
                break

    def _find_function_declarations(self, ast):
        """Find all function declarations in the AST."""
        functions = set()
        
        def _search_functions(node):
            if hasattr(node, 'data'):
                if node.data == 'variable_declaration':
                    if len(node.children) >= 2:
                        var_name = node.children[0].value if hasattr(node.children[0], 'value') else None
                        func_expr = node.children[1]
                        if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                            if var_name:
                                functions.add(var_name)
            
            if hasattr(node, 'children'):
                for child in node.children:
                    _search_functions(child)
        
        _search_functions(ast)
        return functions
