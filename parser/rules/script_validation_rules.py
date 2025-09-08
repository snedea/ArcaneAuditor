"""
Script validation rules - catches script quality violations that code reviewers should catch.

These are issues that compilers can't detect but violate code quality guidelines and best practices.
Examples: use of var vs let/const, nested block levels, code complexity metrics.

Note: Basic script validation (syntax errors, etc.) is handled by the compiler.
This tool focuses on script quality and best practices for code reviewers.
"""
from .base import Rule, Finding
from ..models import PMDModel
import re


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
        
        for field_path, field_value, field_name in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_var_usage(field_value, field_name, pmd_model.file_path)

    def _check_var_usage(self, script_content, field_name, file_path):
        """Check for use of 'var' in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, report the issue and skip this script
            print(f"⚠️ Failed to parse script in '{field_name}' - skipping var usage check")
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
                    line_number = var_stmt.line if hasattr(var_stmt, 'line') else 1
                    
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
            print(f"⚠️ Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        # Remove <% at the beginning and %> at the end
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
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
        
        for field_path, field_value, field_name in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_nesting_level(field_value, field_name, pmd_model.file_path)

    def _check_nesting_level(self, script_content, field_name, file_path):
        """Check for excessive nesting levels in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, fall back to simple character counting
            print(f"⚠️ Failed to parse script in '{field_name}' - using fallback nesting analysis")
            yield from self._check_nesting_level_fallback(script_content, field_name, file_path)
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
            
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' has {max_nesting_found} nesting levels{context_info} (max recommended: {max_nesting}). Consider refactoring.",
                line=nesting_info.get('line', 1),
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
            print(f"⚠️ Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        # Remove <% at the beginning and %> at the end
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
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
        
        return {
            'max_nesting': max_nesting,
            'function_context': function_context,
            'line': getattr(node, 'line', None)
        }
    
    def _check_nesting_level_fallback(self, script_content, field_name, file_path):
        """Fallback nesting level check using simple character counting."""
        max_nesting = 4
        current_nesting = 0
        max_nesting_found = 0
        function_context = self._extract_function_context(script_content)
        
        for char in script_content:
            if char in '{([{':
                current_nesting += 1
                max_nesting_found = max(max_nesting_found, current_nesting)
            elif char in '})]}':
                current_nesting = max(0, current_nesting - 1)
        
        if max_nesting_found > max_nesting:
            # Create a more descriptive message with function context
            if function_context:
                context_info = f" in function '{function_context}'"
            else:
                context_info = ""
            
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' has {max_nesting_found} nesting levels{context_info} (max recommended: {max_nesting}). Consider refactoring.",
                line=1,
                column=1,
                file_path=file_path
            )
    
    def _extract_function_context(self, script_content):
        """Extract function name if the script content contains a function definition."""
        # Look for function declarations: function name() { or var name = function() {
        function_patterns = [
            r'function\s+(\w+)\s*\(',
            r'var\s+(\w+)\s*=\s*function\s*\(',
            r'let\s+(\w+)\s*=\s*function\s*\(',
            r'const\s+(\w+)\s*=\s*function\s*\(',
            r'(\w+)\s*:\s*function\s*\('
        ]
        
        for pattern in function_patterns:
            match = re.search(pattern, script_content)
            if match:
                return match.group(1)
        
        return None


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
        
        for field_path, field_value, field_name in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_complexity(field_value, field_name, pmd_model.file_path)

    def _check_complexity(self, script_content, field_name, file_path):
        """Check for excessive complexity in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, fall back to regex-based complexity calculation
            print(f"⚠️ Failed to parse script in '{field_name}' - using fallback complexity analysis")
            yield from self._check_complexity_fallback(script_content, field_name, file_path)
            return
        
        max_complexity = 10
        
        # Analyze complexity using AST
        complexity_info = self._analyze_ast_complexity(ast)
        complexity = complexity_info['complexity']
        line = complexity_info.get('line', 1)
        
        if complexity > max_complexity:
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' has complexity of {complexity} (max recommended: {max_complexity}). Consider refactoring.",
                line=line,
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
            print(f"⚠️ Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        # Remove <% at the beginning and %> at the end
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
        return content
    
    def _analyze_ast_complexity(self, node):
        """Analyze cyclomatic complexity in AST nodes."""
        complexity = 1  # Base complexity
        line = None
        
        if hasattr(node, 'data'):
            # Count complexity-increasing constructs
            if node.data in ['if_statement', 'while_statement', 'for_statement', 'do_statement']:
                complexity += 1
                line = getattr(node, 'line', line)
            
            elif node.data == 'logical_and_expression':
                complexity += 1
                line = getattr(node, 'line', line)
            
            elif node.data == 'logical_or_expression':
                complexity += 1
                line = getattr(node, 'line', line)
            
            elif node.data == 'ternary_expression':
                complexity += 1
                line = getattr(node, 'line', line)
        
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
    
    def _check_complexity_fallback(self, script_content, field_name, file_path):
        """Fallback complexity check using regex keyword counting."""
        # Simple cyclomatic complexity calculation
        complexity_keywords = ['if', 'else', 'for', 'while', '&&', '||', '?']
        complexity = 1  # Base complexity
        
        for keyword in complexity_keywords:
            # Count occurrences of complexity-increasing keywords
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, script_content, re.IGNORECASE)
            complexity += len(matches)
        
        max_complexity = 10
        
        if complexity > max_complexity:
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' has complexity of {complexity} (max recommended: {max_complexity}). Consider refactoring.",
                line=1,
                column=1,
                file_path=file_path
            )
