#!/usr/bin/env python3
"""Template Expression Preprocessor for PMD Script Grammar Enhancement.

This module provides a preprocessor that handles template expressions with multiple
script blocks (<% %>) mixed with literal text by parsing them into a structured AST.
"""

import re
from typing import List, Dict, Any, Union
from lark import Tree, Token

class TemplateExpressionPreprocessor:
    """Preprocessor for template expressions with multiple script blocks."""
    
    def __init__(self):
        # Pattern to match script blocks: <% ... %>
        self.script_block_pattern = re.compile(r'<%(.*?)%>', re.DOTALL)
    
    def preprocess_template_expression(self, template_value: str) -> Tree:
        """
        Convert a template expression string into a structured template_expression tree.
        
        Args:
            template_value: The template expression string (e.g., "<% true %> foo <% false %>")
            
        Returns:
            Tree: A template_expression tree with parsed script blocks and text parts
        """
        # Remove surrounding quotes if present
        content = template_value.strip()
        if (content.startswith('"') and content.endswith('"')) or \
           (content.startswith("'") and content.endswith("'")):
            content = content[1:-1]
        
        # Parse the content into parts
        parts = self._parse_template_content(content)
        
        # Create the template_expression tree
        children = []
        for part in parts:
            if part['type'] == 'text':
                children.append(Tree('template_text', [Token('TEMPLATE_TEXT', part['content'])]))
            elif part['type'] == 'script':
                # Parse the script block expression
                script_content = part['content'].strip()
                if script_content:
                    # Ensure the script content is parsed as a complete program
                    # Add semicolon if it doesn't end with one
                    if not script_content.endswith(';'):
                        script_content += ';'
                    
                    # Parse the script content into an AST
                    from ....pmd_script_parser import parse_with_preprocessor
                    script_ast = parse_with_preprocessor(script_content)
                    if script_ast:
                        # Create a script block tree with the parsed AST
                        children.append(Tree('template_script_block', [script_ast]))
        
        return Tree('template_expression', children)
    
    def _parse_template_content(self, content: str) -> List[Dict[str, str]]:
        """Parse template content into text and script block parts."""
        parts = []
        last_end = 0
        
        for match in self.script_block_pattern.finditer(content):
            # Add text before the script block
            if match.start() > last_end:
                text_content = content[last_end:match.start()]
                if text_content:  # Only add non-empty text
                    parts.append({'type': 'text', 'content': text_content})
            
            # Add the script block
            script_content = match.group(1).strip()
            parts.append({'type': 'script', 'content': script_content})
            
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(content):
            text_content = content[last_end:]
            if text_content:  # Only add non-empty text
                parts.append({'type': 'text', 'content': text_content})
        
        return parts
    
    def is_template_expression(self, value: str) -> bool:
        """
        Check if a string value is a template expression (contains script blocks).
        
        Args:
            value: The string value to check
            
        Returns:
            bool: True if this is a template expression with script blocks
        """
        if not isinstance(value, str):
            return False
        
        # Strip quotes first, then check for script blocks
        stripped = value.strip()
        
        # Remove surrounding quotes if present
        if (stripped.startswith('"') and stripped.endswith('"')) or \
           (stripped.startswith("'") and stripped.endswith("'")):
            stripped = stripped[1:-1]
        
        # Check if it contains script blocks
        has_script_blocks = '<%' in stripped and '%>' in stripped
        
        if not has_script_blocks:
            return False
        
        # Check if it's a pure script block (starts with <% and ends with %>)
        # A pure script block has NO text outside the script tags
        is_pure_script = stripped.startswith('<%') and stripped.endswith('%>') and \
                         stripped.count('<%') == 1 and stripped.count('%>') == 1
        
        # It's a template expression if it has script blocks but is not a pure script block
        return not is_pure_script
