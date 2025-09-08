"""
Script validation rules - catches script quality violations that code reviewers should catch.

These are issues that compilers can't detect but violate code quality guidelines and best practices.
Examples: use of var vs let/const, nested block levels, code complexity metrics.

Note: Basic script validation (syntax errors, etc.) is handled by the compiler.
This tool focuses on script quality and best practices for code reviewers.
"""
from .base import Rule, Finding
from ..models import PMDModel, ProjectContext
import re
from typing import Set, List, Tuple, Optional, Generator
from lark import Tree


class ScriptVarUsageRule(Rule):
    """Validates that scripts use 'let' or 'const' instead of 'var'."""
    
    ID = "SCRIPT001"
    DESCRIPTION = "Ensures scripts use 'let' or 'const' instead of 'var' (best practice)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_var_usage(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_var_usage(self, script_content, field_name, file_path, line_offset=1):
        """Check for use of 'var' in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all variable_statement nodes in the AST
        var_statements = ast.find_data('variable_statement')
        for var_stmt in var_statements:
            # Check if the variable statement uses VAR keyword
            if len(var_stmt.children) > 0 and hasattr(var_stmt.children[0], 'type') and var_stmt.children[0].type == 'VAR':
                # Get the variable declaration (second child)
                var_declaration = var_stmt.children[1]
                if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                        var_name = var_declaration.children[0].value
                        # Get line number from the VAR token (first child)
                        relative_line = getattr(var_stmt.children[0], 'line', 1) or 1
                        line_number = line_offset + relative_line - 1
                        
                        yield Finding(
                            rule=self,
                            message=f"File section '{field_name}' uses 'var' declaration for variable '{var_name}'. Consider using 'let' or 'const' instead.",
                            line=line_number,
                            column=1,
                            file_path=file_path
                        )
    
    def _parse_script_content(self, script_content):
        """Parse script content using Lark grammar."""
        if not script_content or not script_content.strip():
            return None
        
        # Strip PMD script wrappers (<% ... %>)
        clean_content = self._strip_pmd_wrappers(script_content)
        if not clean_content:
            return None
        
        try:
            # Import the parser dynamically to avoid circular imports
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception as e:
            # If parsing fails, return None to fall back to regex
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        # Remove <% at the beginning and %> at the end
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            content = content[2:-2].strip()
        
        # Convert escaped newlines to actual newlines for proper line number tracking
        content = content.replace('\\n', '\n')
        return content
    

    def _get_line_number_from_content(self, content, position):
        """Get approximate line number from content position."""
        return content[:position].count('\n') + 1


class ScriptNestingLevelRule(Rule):
    """Validates that scripts don't have excessive nesting levels."""
    
    ID = "SCRIPT002"
    DESCRIPTION = "Ensures scripts don't have excessive nesting levels (max 4 levels)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_nesting_level(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_nesting_level(self, script_content, field_name, file_path, line_offset=1):
        """Check for excessive nesting levels in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        max_nesting = 4
        max_nesting_found = 0
        function_context = None
        
        # Analyze nesting levels using AST
        nesting_info = self._analyze_ast_nesting(ast, 0)
        max_nesting_found = nesting_info['max_nesting']
        function_context = nesting_info['function_context']
        
        if max_nesting_found > max_nesting:
            # Create a more descriptive message with function context
            if function_context:
                context_info = f" in function '{function_context}'"
            else:
                context_info = ""
            
            # Use line_offset as base, add relative line if available
            relative_line = nesting_info.get('line', 1) or 1
            line_number = line_offset + relative_line - 1
            
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' has {max_nesting_found} nesting levels{context_info} (max recommended: {max_nesting}). Consider refactoring.",
                line=line_number,
                column=1,
                file_path=file_path
            )
    
    def _parse_script_content(self, script_content):
        """Parse script content using Lark grammar."""
        if not script_content or not script_content.strip():
            return None
        
        # Strip PMD script wrappers (<% ... %>)
        clean_content = self._strip_pmd_wrappers(script_content)
        if not clean_content:
            return None
        
        try:
            # Import the parser dynamically to avoid circular imports
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception as e:
            # If parsing fails, return None to fall back to regex
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        # Remove <% at the beginning and %> at the end
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            content = content[2:-2].strip()
        
        # Convert escaped newlines to actual newlines for proper line number tracking
        content = content.replace('\\n', '\n')
        return content
    
    def _analyze_ast_nesting(self, node, current_depth):
        """Analyze nesting levels in AST nodes."""
        max_nesting = current_depth
        function_context = None
        
        # Check if this is a function expression
        if hasattr(node, 'data'):
            if node.data == 'function_expression':
                # Extract function name if available
                if len(node.children) > 0 and hasattr(node.children[0], 'type') and node.children[0].type == 'FUNCTION':
                    if len(node.children) > 1 and hasattr(node.children[1], 'value'):
                        function_context = node.children[1].value
                # Function body adds one nesting level
                current_depth += 1
                max_nesting = max(max_nesting, current_depth)
            
            elif node.data in ['block', 'if_statement', 'while_statement', 'for_statement', 'do_statement']:
                # Control flow structures add nesting
                current_depth += 1
                max_nesting = max(max_nesting, current_depth)
        
        # Recursively analyze children
        if hasattr(node, 'children'):
            for child in node.children:
                child_result = self._analyze_ast_nesting(child, current_depth)
                max_nesting = max(max_nesting, child_result['max_nesting'])
                if child_result['function_context'] and not function_context:
                    function_context = child_result['function_context']
        
        # Get line number from the first token in the node
        line_number = None
        if hasattr(node, 'children') and len(node.children) > 0:
            # Look for the first token with a line number
            for child in node.children:
                if hasattr(child, 'line') and child.line is not None:
                    line_number = child.line
                    break
        
        return {
            'max_nesting': max_nesting,
            'function_context': function_context,
            'line': line_number
        }


class ScriptComplexityRule(Rule):
    """Validates that scripts don't exceed complexity thresholds."""
    
    ID = "SCRIPT003"
    DESCRIPTION = "Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_complexity(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_complexity(self, script_content, field_name, file_path, line_offset=1):
        """Check for excessive complexity in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        max_complexity = 10
        
        # Analyze complexity using AST
        complexity_info = self._analyze_ast_complexity(ast)
        complexity = complexity_info['complexity']
        line = complexity_info.get('line', 1)
        
        if complexity > max_complexity:
            # Use line_offset as base, add relative line if available
            relative_line = complexity_info.get('line', 1) or 1
            line_number = line_offset + relative_line - 1
            
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' has complexity of {complexity} (max recommended: {max_complexity}). Consider refactoring.",
                line=line_number,
                column=1,
                file_path=file_path
            )
    
    def _parse_script_content(self, script_content):
        """Parse script content using Lark grammar."""
        if not script_content or not script_content.strip():
            return None
        
        # Strip PMD script wrappers (<% ... %>)
        clean_content = self._strip_pmd_wrappers(script_content)
        if not clean_content:
            return None
        
        try:
            # Import the parser dynamically to avoid circular imports
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception as e:
            # If parsing fails, return None to fall back to regex
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        # Remove <% at the beginning and %> at the end
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            content = content[2:-2].strip()
        
        # Convert escaped newlines to actual newlines for proper line number tracking
        content = content.replace('\\n', '\n')
        return content
    
    def _analyze_ast_complexity(self, node):
        """Analyze cyclomatic complexity in AST nodes."""
        complexity = 1  # Base complexity
        line = None
        
        if hasattr(node, 'data'):
            # Count complexity-increasing constructs
            if node.data in ['if_statement', 'while_statement', 'for_statement', 'do_statement']:
                complexity += 1
                # Get line number from the first token in the node
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'logical_and_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'logical_or_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'ternary_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
        
        # Recursively analyze children
        if hasattr(node, 'children'):
            for child in node.children:
                child_complexity = self._analyze_ast_complexity(child)
                complexity += child_complexity['complexity'] - 1  # Subtract 1 to avoid double-counting base complexity
                if child_complexity.get('line') and not line:
                    line = child_complexity['line']
        
        return {
            'complexity': complexity,
            'line': line
        }  


class ScriptUnusedVariableRule(Rule):
    """Validates that all declared variables are used with proper scoping."""
    
    ID = "SCRIPT004"
    DESCRIPTION = "Ensures all declared variables are used (prevents dead code) with proper scoping awareness"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model with scope awareness."""
        script_fields = self.find_script_fields(pmd_model)
        
        # Build a global function registry from the main script section
        global_functions = self._build_global_function_registry(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                is_global_scope = (field_name == 'script')
                yield from self._check_unused_variables_with_scope(
                    field_value, field_name, pmd_model.file_path, 
                    is_global_scope, global_functions, line_offset
                )

    def _build_global_function_registry(self, pmd_model: PMDModel):
        """Build a registry of functions declared in the global script section."""
        global_functions = set()
        
        if pmd_model.script:
            ast = self._parse_script_content(pmd_model.script)
            if ast:
                global_functions = self._find_function_declarations(ast)
        
        return global_functions

    def _check_unused_variables_with_scope(self, script_content, field_name, file_path, is_global_scope, global_functions, line_offset=1):
        """Check for unused variables with proper scoping awareness."""
        ast = self._parse_script_content(script_content)
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
                    # Special handling for global functions - they might be used by widgets/endpoints
                    if is_global_scope and scope_type == 'global' and var_name in global_functions:
                        # For now, we'll still flag them but with a different message
                        scope_context = " (global function - may be used by widgets/endpoints)"
                    else:
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
                            if hasattr(child, 'line') and child.line is not None:
                                line_number = child.line
                                break
                    
                    current_scope['declared_vars'][var_name] = {
                        'line': line_number,
                        'type': 'variable'
                    }
                    
                    # Check if this is a function declaration
                    if len(node.children) >= 2:
                        func_expr = node.children[1]
                        if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                            current_scope['functions'][var_name] = func_expr
                            
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
                        func_scope['declared_vars'][param_name] = {
                            'line': getattr(param_child, 'line', None),
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
    
    def _parse_script_content(self, script_content):
        """Parse script content using Lark grammar."""
        if not script_content or not script_content.strip():
            return None
        
        clean_content = self._strip_pmd_wrappers(script_content)
        if not clean_content:
            return None
        
        try:
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception as e:
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
        return content


class ScriptConsoleLogRule(Rule):
    """Validates that scripts don't contain console statements."""
    
    ID = "SCRIPT005"
    DESCRIPTION = "Ensures scripts don't contain console statements (production code)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_console_logs(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_console_logs(self, script_content, field_name, file_path, line_offset=1):
        """Check for console.log statements in script content."""
        # Simple regex check for console.log statements
        import re
        # TODO: Confirm what console methods exist
        console_log_pattern = r'console\.[info|warn|debug]\s*\('
        matches = list(re.finditer(console_log_pattern, script_content, re.IGNORECASE))
        
        for match in matches:
            relative_line = script_content[:match.start()].count('\n') + 1
            line_number = line_offset + relative_line - 1
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' contains console log statement. Remove debug statements from production code.",
                line=line_number,
                column=match.start() - script_content.rfind('\n', 0, match.start()) - 1,
                file_path=file_path
            )


class ScriptMagicNumberRule(Rule):
    """Validates that scripts don't contain magic numbers."""
    
    ID = "SCRIPT006"
    DESCRIPTION = "Ensures scripts don't contain magic numbers (use named constants)"
    SEVERITY = "INFO"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_magic_numbers(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_magic_numbers(self, script_content, field_name, file_path, line_offset=1):
        """Check for magic numbers in script content using AST analysis."""
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Define allowed numbers and contexts
        allowed_numbers = {0, 1, -1}  # Common legitimate numbers
        # We want to flag magic numbers regardless of their parent context
        
        findings = []
        
        def visit_node(node, parent=None):
            """Recursively visit AST nodes to find magic numbers."""
            # Check if the current node is a numeric literal
            if hasattr(node, 'data') and node.data == 'literal_expression':
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    try:
                        # Try to parse the value as a number
                        value = node.children[0].value
                        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                            number = int(value)
                            
                            # Check if this is a magic number
                            is_magic = number not in allowed_numbers
                            
                            if is_magic:
                                # Get line number from the token inside the literal_expression
                                relative_line = getattr(node.children[0], 'line', 1) or 1
                                line_number = line_offset + relative_line - 1
                                
                                findings.append(Finding(
                                    rule=self,
                                    message=f"File section '{field_name}' contains magic number '{number}'. Consider using a named constant instead.",
                                    line=line_number,
                                    column=1,
                                    file_path=file_path
                                ))
                    except (ValueError, AttributeError):
                        # Not a number, skip
                        pass
            
            # Recurse into children
            if hasattr(node, 'children'):
                for child in node.children:
                    visit_node(child, parent=node)
        
        # Start the traversal from the root of the AST
        visit_node(ast)
        
        # Yield all findings
        for finding in findings:
            yield finding
    
    def _parse_script_content(self, script_content):
        """Parse script content using Lark grammar."""
        if not script_content or not script_content.strip():
            return None
        
        clean_content = self._strip_pmd_wrappers(script_content)
        if not clean_content:
            return None
        
        try:
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception as e:
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
        return content


class ScriptLongFunctionRule(Rule):
    """Validates that functions don't exceed maximum line count."""
    
    ID = "SCRIPT007"
    DESCRIPTION = "Ensures functions don't exceed maximum line count (max 50 lines)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_long_functions(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_long_functions(self, script_content, field_name, file_path, line_offset=1):
        """Check for overly long functions in script content."""
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        max_lines = 50
        long_functions = self._find_long_functions(ast, max_lines)
        
        for func_info in long_functions:
            # Use line_offset as base, add relative line if available
            relative_line = func_info.get('line', 1) or 1
            line_number = line_offset + relative_line - 1
            
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' contains function '{func_info['name']}' with {func_info['lines']} lines (max recommended: {max_lines}). Consider breaking it into smaller functions.",
                line=line_number,
                column=1,
                file_path=file_path
            )
    
    def _find_long_functions(self, node, max_lines):
        """Find functions that exceed the maximum line count."""
        long_functions = []
        
        if hasattr(node, 'data'):
            if node.data == 'variable_declaration':
                # Check if this variable declaration contains a function expression
                if len(node.children) >= 2:
                    var_name = node.children[0].value if hasattr(node.children[0], 'value') else "unknown"
                    func_expr = node.children[1]
                    
                    if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                        # Find function body
                        func_body = None
                        for child in func_expr.children:
                            if hasattr(child, 'data') and child.data == 'source_elements':
                                func_body = child
                                break
                        
                        if func_body:
                            line_count = self._count_function_lines(func_body)
                            if line_count > max_lines:
                                # Get line number from the first token in the node
                                line_number = None
                                if hasattr(node, 'children') and len(node.children) > 0:
                                    for child in node.children:
                                        if hasattr(child, 'line') and child.line is not None:
                                            line_number = child.line
                                            break
                                
                                long_functions.append({
                                    'name': var_name,
                                    'lines': line_count,
                                    'line': line_number
                                })
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                child_functions = self._find_long_functions(child, max_lines)
                long_functions.extend(child_functions)
        
        return long_functions
    
    def _count_function_lines(self, func_body):
        """Count the number of lines in a function body."""
        # Count the number of statements in the function body
        if hasattr(func_body, 'children'):
            return len(func_body.children)
        return 1
    
    def _parse_script_content(self, script_content):
        """Parse script content using Lark grammar."""
        if not script_content or not script_content.strip():
            return None
        
        clean_content = self._strip_pmd_wrappers(script_content)
        if not clean_content:
            return None
        
        try:
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception as e:
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
        return content


class ScriptVariableNamingRule(Rule):
    """Validates that variables follow naming conventions."""
    
    ID = "SCRIPT008"
    DESCRIPTION = "Ensures variables follow lowerCamelCase naming convention"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_variable_naming(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_variable_naming(self, script_content, field_name, file_path, line_offset=1):
        """Check variable naming conventions in script content."""
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all variable declarations
        declared_vars = self._find_declared_variables(ast)
        
        for var_name, var_info in declared_vars.items():
            is_valid, suggestion = self._validate_camel_case(var_name)
            if not is_valid:
                # Use line_offset as base, add relative line if available
                relative_line = var_info.get('line', 1) or 1
                line_number = line_offset + relative_line - 1
                
                yield Finding(
                    rule=self,
                    message=f"File section '{field_name}' declares variable '{var_name}' that doesn't follow lowerCamelCase convention. Consider renaming to '{suggestion}'.",
                    line=line_number,
                    column=1,
                    file_path=file_path
                )
    
    def _find_declared_variables(self, node):
        """Find all variable declarations in the AST."""
        declared_vars = {}
        
        if hasattr(node, 'data'):
            if node.data == 'variable_declaration':
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    var_name = node.children[0].value
                    # Get line number from the first token in the node
                    line_number = None
                    if hasattr(node, 'children') and len(node.children) > 0:
                        for child in node.children:
                            if hasattr(child, 'line') and child.line is not None:
                                line_number = child.line
                                break
                    
                    declared_vars[var_name] = {
                        'line': line_number,
                        'type': 'declaration'
                    }
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                child_vars = self._find_declared_variables(child)
                declared_vars.update(child_vars)
        
        return declared_vars
    
    def _validate_camel_case(self, var_name):
        """Validate variable name using common camel case validation."""
        from .common_validations import validate_script_variable_camel_case
        return validate_script_variable_camel_case(var_name)
    
    def _parse_script_content(self, script_content):
        """Parse script content using Lark grammar."""
        if not script_content or not script_content.strip():
            return None
        
        clean_content = self._strip_pmd_wrappers(script_content)
        if not clean_content:
            return None
        
        try:
            from ..pmd_script_parser import pmd_script_parser
            return pmd_script_parser.parse(clean_content)
        except Exception as e:
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
        return content

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
            
        # Check if the full chain is protected
        if self._is_protected_chain(ast, chain):
            return False
            
        # Also check if any parent chain is protected (which would make this safe)
        for i in range(len(parts) - 1):
            partial_chain = '.'.join(parts[:i+1])
            if self._is_protected_chain(ast, partial_chain):
                return False
            
        return True


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
            

        # Calculate the script line offset
        line_offset = self._calculate_script_line_offset(pmd_model.source_content, pmd_model.script)
        return line_offset + relative_line - 1