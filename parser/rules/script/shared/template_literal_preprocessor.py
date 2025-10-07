#!/usr/bin/env python3
"""Template Literal Preprocessor for PMD Script Grammar Enhancement.

This module provides a preprocessor that enhances template literals with {{ }} interpolation
by parsing them into a more structured AST without modifying the core grammar.
"""

import re
from typing import List, Dict, Any, Union
from lark import Tree, Token

class TemplateLiteralPreprocessor:
    """Preprocessor for template literals with {{ }} interpolation."""
    
    def __init__(self):
        self.interpolation_pattern = re.compile(r'\{\{([^}]+)\}\}')
    
    def preprocess_template_literal(self, template_token: Token) -> Tree:
        """
        Convert a TEMPLATE_LITERAL token into a structured template_literal_expression tree.
        
        Args:
            template_token: The TEMPLATE_LITERAL token from the original grammar
            
        Returns:
            Tree: A template_literal_expression tree with parsed interpolation
        """
        template_content = template_token.value
        
        # Remove the backticks
        content = template_content[1:-1]  # Remove first and last character (backticks)
        
        # Parse the content into parts
        parts = self._parse_template_content(content)
        
        # Create the template_literal_expression tree
        children = []
        for part in parts:
            if part['type'] == 'text':
                children.append(Tree('template_text', [Token('TEMPLATE_TEXT', part['content'])]))
            elif part['type'] == 'interpolation':
                # Parse the interpolation expression
                expr_tree = self._parse_interpolation_expression(part['content'])
                children.append(Tree('template_interpolation', [expr_tree]))
        
        return Tree('template_literal_expression', children)
    
    def _parse_template_content(self, content: str) -> List[Dict[str, str]]:
        """Parse template content into text and interpolation parts."""
        parts = []
        last_end = 0
        
        for match in self.interpolation_pattern.finditer(content):
            # Add text before the interpolation
            if match.start() > last_end:
                text_content = content[last_end:match.start()]
                if text_content:  # Only add non-empty text
                    parts.append({'type': 'text', 'content': text_content})
            
            # Add the interpolation
            interpolation_content = match.group(1).strip()
            parts.append({'type': 'interpolation', 'content': interpolation_content})
            
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(content):
            text_content = content[last_end:]
            if text_content:  # Only add non-empty text
                parts.append({'type': 'text', 'content': text_content})
        
        return parts
    
    def _parse_interpolation_expression(self, expression: str) -> Tree:
        """
        Parse an interpolation expression into an AST.
        This is a simplified parser for common expressions.
        """
        expression = expression.strip()
        
        # Handle simple property access (e.g., "user.profile.email")
        if '.' in expression and not any(op in expression for op in ['??', '?', ':', '&&', '||', '+', '-', '*', '/']):
            parts = expression.split('.')
            if len(parts) >= 2:
                # Create a member_dot_expression tree
                return self._create_property_access_tree(parts)
        
        # Handle null coalescing (e.g., "user.profile.email ?? ''")
        if '??' in expression:
            left, right = expression.split('??', 1)
            left_tree = self._parse_interpolation_expression(left.strip())
            right_tree = self._parse_interpolation_expression(right.strip())
            return Tree('null_coalescing_expression', [left_tree, right_tree])
        
        # Handle simple identifiers
        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', expression):
            return Tree('identifier_expression', [Token('IDENTIFIER', expression)])
        
        # Handle string literals
        if (expression.startswith('"') and expression.endswith('"')) or \
           (expression.startswith("'") and expression.endswith("'")):
            return Tree('literal_expression', [Token('STRING_LITERAL', expression)])
        
        # Fallback: treat as identifier
        return Tree('identifier_expression', [Token('IDENTIFIER', expression)])
    
    def _create_property_access_tree(self, parts: List[str]) -> Tree:
        """Create a member_dot_expression tree from property parts."""
        if len(parts) == 1:
            return Tree('identifier_expression', [Token('IDENTIFIER', parts[0])])
        
        # Build the tree from right to left
        right_part = parts[-1]
        left_parts = parts[:-1]
        
        if len(left_parts) == 1:
            left_tree = Tree('identifier_expression', [Token('IDENTIFIER', left_parts[0])])
        else:
            left_tree = self._create_property_access_tree(left_parts)
        
        return Tree('member_dot_expression', [left_tree, Token('IDENTIFIER', right_part)])

