from typing import List, Dict, Any, Generator
from lark import Tree

from parser.rules.base import Rule, Finding
from parser.models import PMDModel


class ScriptStringConcatRule(Rule):
    """Rule to detect string concatenation using + operator when PMD templates should be used instead."""
    
    DESCRIPTION = "Detects string concatenation with + operator - use PMD templates with backticks and {{ }} instead"
    SEVERITY = "WARNING"
    
    def __init__(self, config: Dict[str, Any] = None):
        # No configuration needed for this rule
        pass
    
    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model for string concatenation issues."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_string_concatenation(field_value, field_name, pmd_model.file_path, line_offset)
    
    def _check_string_concatenation(self, script_content, field_name, file_path, line_offset=1):
        """Check for string concatenation using + operator in script content."""
        # Parse the script content using the base class method (handles PMD wrappers)
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all addition expressions that involve string concatenation
        yield from self._find_string_concatenation_expressions(ast, field_name, file_path, line_offset)
    
    def _find_string_concatenation_expressions(self, ast: Tree, field_name: str, file_path: str, line_offset: int):
        """Find expressions that use + operator for string concatenation."""
        # Find all addition expressions in the AST
        addition_expressions = ast.find_data('additive_expression')
        
        for add_expr in addition_expressions:
            if self._is_string_concatenation(add_expr):
                line_number = self._get_line_number_from_node(add_expr)
                if line_number:
                    line_number = line_offset + line_number - 1
                
                # Extract the concatenation expression for better error message
                concat_text = self._extract_expression_text(add_expr)
                
                yield Finding(
                    rule=self,
                    message=f"File section '{field_name}' uses string concatenation with + operator: '{concat_text}'. Consider using PMD template strings with backticks and {{{{ }}}} syntax instead (e.g., `Hello {{{{name}}}}!`).",
                    line=line_number or line_offset,
                    column=1,
                    file_path=file_path
                )
    
    def _is_string_concatenation(self, add_expr: Tree) -> bool:
        """Check if an addition expression is actually string concatenation."""
        if not isinstance(add_expr, Tree) or add_expr.data != 'additive_expression':
            return False
        
        # Check if any operand involves strings
        # The AST structure shows that additive expressions can have multiple operands
        # when there are chained + operations like "a" + b + "c"
        for operand in add_expr.children:
            if self._involves_string(operand):
                return True
            # Recursively check if any operand is itself a string concatenation
            if isinstance(operand, Tree) and self._is_string_concatenation(operand):
                return True
        
        return False
    
    def _involves_string(self, node) -> bool:
        """Check if a node involves string operations."""
        if not isinstance(node, Tree):
            return False
        
        # Check if it's a string literal
        if node.data == 'literal_expression':
            if len(node.children) > 0:
                child = node.children[0]
                if hasattr(child, 'value') and isinstance(child.value, str) and child.value.startswith(('"', "'")):
                    return True
        
        # Check if it's a template literal (backticks)
        if node.data == 'literal_expression':
            if len(node.children) > 0:
                child = node.children[0]
                if hasattr(child, 'value') and isinstance(child.value, str) and child.value.startswith('`'):
                    return True
        
        # Recursively check child nodes for string operations
        for child in node.children:
            if isinstance(child, Tree) and self._involves_string(child):
                return True
        
        return False
    
    def _extract_expression_text(self, node: Tree) -> str:
        """Extract readable text representation of an expression."""
        if not isinstance(node, Tree):
            return str(node)
        
        if node.data == 'additive_expression':
            if len(node.children) >= 3:
                left = self._extract_expression_text(node.children[0])
                operator = node.children[1].value if hasattr(node.children[1], 'value') else '+'
                right = self._extract_expression_text(node.children[2])
                return f"{left} {operator} {right}"
        
        elif node.data == 'literal_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        elif node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        # For other node types, try to extract meaningful text
        text_parts = []
        for child in node.children:
            if hasattr(child, 'value'):
                text_parts.append(child.value)
            elif isinstance(child, Tree):
                text_parts.append(self._extract_expression_text(child))
        
        return ' '.join(text_parts) if text_parts else str(node.data)
    
    def _get_line_number_from_node(self, node: Tree) -> int:
        """Get the line number from an AST node."""
        if hasattr(node, 'meta') and hasattr(node.meta, 'line'):
            return node.meta.line
        elif hasattr(node, 'line'):
            return node.line
        elif hasattr(node, 'children') and len(node.children) > 0:
            # Try to get line from first child
            child = node.children[0]
            if hasattr(child, 'meta') and hasattr(child.meta, 'line'):
                return child.meta.line
            elif hasattr(child, 'line'):
                return child.line
        return 1  # Default fallback
