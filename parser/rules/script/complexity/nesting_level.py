from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


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
