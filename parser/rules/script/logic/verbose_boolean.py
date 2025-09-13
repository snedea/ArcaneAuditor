from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


class ScriptVerboseBooleanCheckRule(Rule):
    """Validates that scripts don't use overly verbose boolean checks like 'if(var == true) { return true } else { return false }'."""
    
    ID = "SCRIPT011"
    DESCRIPTION = "Ensures scripts don't use overly verbose boolean checks (if(var == true) return true else return false)"
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
                yield from self._check_verbose_boolean_patterns(field_value, field_name, pmd_model.file_path, line_offset)

    def _check_verbose_boolean_patterns(self, script_content, field_name, file_path, line_offset=1):
        """Check for overly verbose boolean patterns in script content using AST parsing."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Store the original script content for operator detection
        self._original_script_content = script_content
        
        # Find verbose boolean patterns in if statements and ternary expressions
        yield from self._find_verbose_if_statements(ast, field_name, file_path, line_offset)
        yield from self._find_verbose_ternary_expressions(ast, field_name, file_path, line_offset)

    def _find_verbose_if_statements(self, ast, field_name, file_path, line_offset):
        """Find verbose boolean patterns in if statements."""
        # Find all if_statement nodes in the AST
        if_statements = ast.find_data('if_statement')
        for if_stmt in if_statements:
            verbose_info = self._analyze_if_statement_for_verbosity(if_stmt)
            if verbose_info:
                # Get line number from the if statement
                line_number = self._get_line_number_from_node(if_stmt, line_offset)
                
                yield Finding(
                    rule=self,
                    message=f"File section '{field_name}' has verbose boolean check: '{verbose_info['pattern']}'. Consider simplifying to '{verbose_info['suggestion']}'.",
                    line=line_number,
                    column=1,
                    file_path=file_path
                )

    def _find_verbose_ternary_expressions(self, ast, field_name, file_path, line_offset):
        """Find verbose boolean patterns in ternary expressions."""
        # Find all ternary_expression nodes in the AST
        ternary_expressions = ast.find_data('ternary_expression')
        for ternary_expr in ternary_expressions:
            verbose_info = self._analyze_ternary_expression_for_verbosity(ternary_expr)
            if verbose_info:
                # Get line number from the ternary expression
                line_number = self._get_line_number_from_node(ternary_expr, line_offset)
                
                yield Finding(
                    rule=self,
                    message=f"File section '{field_name}' has verbose boolean check: '{verbose_info['pattern']}'. Consider simplifying to '{verbose_info['suggestion']}'.",
                    line=line_number,
                    column=1,
                    file_path=file_path
                )

    def _analyze_if_statement_for_verbosity(self, if_node):
        """Analyze an if statement to see if it's a verbose boolean pattern."""
        if not hasattr(if_node, 'children') or len(if_node.children) < 5:
            return None
        
        # Based on actual AST structure: [IF, condition, then_statement, ELSE, else_statement]
        condition = if_node.children[1]  # equality_expression
        then_statement = if_node.children[2]  # return_statement
        else_statement = if_node.children[4] if len(if_node.children) > 4 else None  # return_statement
        
        # Check if this is a verbose boolean pattern
        return self._check_verbose_boolean_condition(condition, then_statement, else_statement)

    def _analyze_ternary_expression_for_verbosity(self, ternary_node):
        """Analyze a ternary expression to see if it's a verbose boolean pattern."""
        if not hasattr(ternary_node, 'children') or len(ternary_node.children) < 3:
            return None
        
        # Get condition, true_value, and false_value
        condition = ternary_node.children[0]
        true_value = ternary_node.children[1]
        false_value = ternary_node.children[2]
        
        # Check if this is a verbose boolean pattern
        return self._check_verbose_ternary_condition(condition, true_value, false_value)

    def _check_verbose_boolean_condition(self, condition, then_stmt, else_stmt):
        """Check if condition + then/else statements form a verbose boolean pattern."""
        # Extract the condition pattern
        condition_info = self._extract_condition_info(condition)
        if not condition_info:
            return None
        
        # Check if then and else statements are simple return statements
        then_return = self._extract_simple_return_value(then_stmt)
        else_return = self._extract_simple_return_value(else_stmt)
        
        if then_return is None or else_return is None:
            return None
        
        # Check for verbose patterns
        return self._check_verbose_pattern(condition_info, then_return, else_return, "if")

    def _check_verbose_ternary_condition(self, condition, true_value, false_value):
        """Check if ternary condition + values form a verbose boolean pattern."""
        # Extract the condition pattern
        condition_info = self._extract_condition_info(condition)
        if not condition_info:
            return None
        
        # Check if true and false values are boolean literals
        true_literal = self._extract_boolean_literal(true_value)
        false_literal = self._extract_boolean_literal(false_value)
        
        if true_literal is None or false_literal is None:
            return None
        
        # Check for verbose patterns
        return self._check_verbose_pattern(condition_info, true_literal, false_literal, "ternary")

    def _check_verbose_pattern(self, condition_info, true_return, false_return, pattern_type="if"):
        """Check for verbose boolean patterns and return suggestion."""
        variable = condition_info['variable']
        operator = condition_info['operator']
        comparison = condition_info['comparison']
        
        # Check for verbose patterns
        if operator == '==' and comparison == 'true':
            if true_return == 'true' and false_return == 'false':
                if pattern_type == "ternary":
                    return {
                        'pattern': f"{variable} == true ? true : false",
                        'suggestion': f"{variable}"
                    }
                else:
                    return {
                        'pattern': f"if({variable} == true) return true else return false",
                        'suggestion': f"return {variable}"
                    }
        
        elif operator == '!=' and comparison == 'true':
            if true_return == 'false' and false_return == 'true':
                if pattern_type == "ternary":
                    return {
                        'pattern': f"{variable} != true ? false : true",
                        'suggestion': f"{variable}"
                    }
                else:
                    return {
                        'pattern': f"if({variable} != true) return false else return true",
                        'suggestion': f"return {variable}"
                    }
        
        elif operator == '==' and comparison == 'false':
            if true_return == 'false' and false_return == 'true':
                if pattern_type == "ternary":
                    return {
                        'pattern': f"{variable} == false ? false : true",
                        'suggestion': f"!{variable}"
                    }
                else:
                    return {
                        'pattern': f"if({variable} == false) return false else return true",
                        'suggestion': f"return !{variable}"
                    }
        
        elif operator == '!=' and comparison == 'false':
            if true_return == 'true' and false_return == 'false':
                if pattern_type == "ternary":
                    return {
                        'pattern': f"{variable} != false ? true : false",
                        'suggestion': f"{variable}"
                    }
                else:
                    return {
                        'pattern': f"if({variable} != false) return true else return false",
                        'suggestion': f"return {variable}"
                    }
        
        return None

    def _extract_condition_info(self, condition_node):
        """Extract information about a comparison condition."""
        if not hasattr(condition_node, 'data'):
            return None
        
        # Handle parenthesized expressions by extracting the inner expression
        if condition_node.data == 'parenthesized_expression':
            if len(condition_node.children) > 0:
                # Extract the inner expression from the parentheses
                inner_expression = condition_node.children[0]
                return self._extract_condition_info(inner_expression)
        
        if condition_node.data == 'equality_expression':
            if len(condition_node.children) >= 2:
                left = condition_node.children[0]
                right = condition_node.children[1]
                
                # Extract variable name from left side
                variable_name = self._extract_identifier_name(left)
                if not variable_name:
                    return None
                
                # Extract comparison value from right side
                comparison_value = self._extract_boolean_literal(right)
                if comparison_value is None:
                    return None
                
                # Detect the actual operator by examining the source content
                operator_str = self._detect_operator_from_source(condition_node, variable_name, comparison_value)
                
                return {
                    'variable': variable_name,
                    'operator': operator_str,
                    'comparison': comparison_value
                }
        
        return None

    def _extract_identifier_name(self, node):
        """Extract identifier name from a node."""
        if hasattr(node, 'data') and node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        return None

    def _extract_boolean_literal(self, node):
        """Extract boolean literal value from a node."""
        # Check if it's a literal_expression with boolean value
        if hasattr(node, 'data') and node.data == 'literal_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                value = node.children[0].value
                if value in ['true', 'false']:
                    return value
        
        # Check if it's an identifier_expression with boolean value (true/false can be identifiers)
        if hasattr(node, 'data') and node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                value = node.children[0].value
                if value in ['true', 'false']:
                    return value
                    
        return None

    def _extract_simple_return_value(self, stmt_node):
        """Extract simple return value from a statement."""
        if not hasattr(stmt_node, 'data'):
            return None
        
        if stmt_node.data == 'return_statement':
            if len(stmt_node.children) > 1:
                return_node = stmt_node.children[1]  # The actual return value
                return self._extract_boolean_literal(return_node)
        
        return None

    def _get_line_number_from_node(self, node, line_offset):
        """Get line number from an AST node."""
        # Try to find a line number from any child token
        if hasattr(node, 'children'):
            for child in node.children:
                if hasattr(child, 'line') and child.line is not None:
                    return line_offset + child.line - 1
        
        # Fallback to line 1 if no line number found
        return line_offset

    def _detect_operator_from_source(self, condition_node, variable_name, comparison_value):
        """Detect the actual operator used in the source by examining the original script content."""
        import re
        
        if not hasattr(self, '_original_script_content'):
            return "=="  # Default fallback
        
        # Create a regex pattern to find the comparison in the source
        # Look for patterns like "variable == true" or "variable != true"
        pattern = rf'{re.escape(variable_name)}\s*([!=]+)\s*{re.escape(comparison_value)}'
        
        matches = re.findall(pattern, self._original_script_content)
        if matches:
            operator = matches[0]
            if operator == '==':
                return '=='
            elif operator == '!=':
                return '!='
        
        # Default fallback
        return "=="
