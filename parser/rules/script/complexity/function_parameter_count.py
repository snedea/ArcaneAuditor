"""
SCRIPT013 - Function Parameter Count Rule

This rule flags functions that have too many parameters, indicating they may be doing too much
and should be refactored. The default threshold is 4 parameters.
"""

from typing import List, Dict, Any
from lark import Tree

from parser.rules.base import Rule, Finding
from parser.models import PMDModel, PodModel


class ScriptFunctionParameterCountRule(Rule):
    """Rule to detect functions with too many parameters."""
    
    DESCRIPTION = "Functions should not have too many parameters (max 4 by default)"
    SEVERITY = "WARNING"
    
    def __init__(self, config: Dict[str, Any] = None):
        # Default threshold - can be configured
        self.max_parameters = config.get("max_parameters", 4) if config else 4
    
    def analyze(self, context):
        """Main entry point - analyze all PMD models and standalone script files in the context."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model for function parameter count issues."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_function_parameters(field_value, field_name, pmd_model.file_path, line_offset)

    def visit_pod(self, pod_model: PodModel):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_function_parameters(field_value, field_name, pod_model.file_path, line_offset)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for function parameter count."""
        try:
            yield from self._check_function_parameters(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _check_function_parameters(self, script_content, field_name, file_path, line_offset=1):
        """Check for functions with too many parameters in script content."""
        # Parse the script content using the base class method (handles PMD wrappers)
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all function definitions
        function_definitions = self._find_function_definitions(ast)
        
        for func_def in function_definitions:
            param_count = self._count_parameters(func_def)
            if param_count > self.max_parameters:
                line_number = self._get_line_number(func_def)
                if line_number:
                    line_number = line_offset + line_number - 1
                
                yield Finding(
                    rule=self,
                    message=f"Function has {param_count} parameters (max allowed: {self.max_parameters}). Consider refactoring to reduce complexity.",
                    line=line_number or line_offset,
                    column=1,
                    file_path=file_path
                )
    
    def _find_function_definitions(self, ast: Tree) -> List[Tree]:
        """Find all function definition nodes in the AST."""
        function_definitions = []
        
        def traverse(node):
            if isinstance(node, Tree):
                # Check if this is a function expression (top-level or nested)
                if node.data == 'function_expression':
                    function_definitions.append(node)
                # Check if this is an arrow function
                elif node.data == 'arrow_function_expression':
                    function_definitions.append(node)
                
                # Recursively traverse children
                for child in node.children:
                    traverse(child)
        
        traverse(ast)
        return function_definitions
    
    def _count_parameters(self, function_node: Tree) -> int:
        """Count the number of parameters in a function definition."""
        if not isinstance(function_node, Tree):
            return 0
        
        if function_node.data == 'function_expression':
            # For function expressions, look for formal_parameter_list
            for child in function_node.children:
                if isinstance(child, Tree) and child.data == 'formal_parameter_list':
                    # Count the parameters in the parameter list
                    return self._count_parameter_list(child)
        elif function_node.data == 'arrow_function_expression':
            # For arrow functions, count identifier tokens directly
            return self._count_arrow_function_parameters(function_node)
        
        return 0
    
    def _count_parameter_list(self, parameter_list_node: Tree) -> int:
        """Count parameters in a formal parameter list."""
        if not isinstance(parameter_list_node, Tree):
            return 0
        
        count = 0
        for child in parameter_list_node.children:
            # In formal_parameter_list, each child is an IDENTIFIER token
            if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                count += 1
        
        return count
    
    def _count_arrow_function_parameters(self, arrow_function_node: Tree) -> int:
        """Count parameters in an arrow function."""
        if not isinstance(arrow_function_node, Tree):
            return 0
        
        count = 0
        for child in arrow_function_node.children:
            # In arrow functions, parameters are IDENTIFIER tokens
            if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                # Skip the arrow token and expression parts
                if hasattr(child, 'value') and child.value == '=>':
                    break
                count += 1
        
        return count
    
    def _get_line_number(self, node: Tree) -> int:
        """Get the line number for a tree node."""
        if hasattr(node, 'meta') and hasattr(node.meta, 'line'):
            return node.meta.line
        return 1  # Default to line 1 if no line info available
