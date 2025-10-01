"""Script unused functions rule using unified architecture."""

from typing import Generator, Set
from ...script.shared import ScriptRuleBase
from ...base import Finding
from .unused_functions_detector import UnusedFunctionsDetector


class ScriptUnusedFunctionRule(ScriptRuleBase):
    """Validates that functions are not declared but never used."""

    DESCRIPTION = "Ensures functions are not declared but never used"
    SEVERITY = "WARNING"
    DETECTOR = UnusedFunctionsDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector."""
        # Parse the script content
        ast = self._parse_script_content(script_content, context)
        if not ast:
            return
        
        # Collect function declarations and calls within this script
        all_declared_functions = self._collect_function_declarations(ast)
        all_function_calls = self._collect_function_calls(ast)
        
        # Use detector to find violations
        detector = self.DETECTOR(file_path, line_offset, all_declared_functions, all_function_calls)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        for violation in violations:
            yield Finding(
                rule=self,
                message=violation.message,
                line=violation.line,
                file_path=file_path
            )
    
    def _collect_function_declarations(self, ast) -> Set[str]:
        """Collect all function declarations from the AST."""
        declared_functions = set()
        
        try:
            # Find all function expressions (function declarations)
            for function_node in ast.find_data('function_expression'):
                function_name = self._get_function_name_from_node(function_node)
                if function_name:
                    declared_functions.add(function_name)
        except Exception:
            pass  # If AST traversal fails, return empty set
        
        return declared_functions
    
    def _collect_function_calls(self, ast) -> Set[str]:
        """Collect all function calls from the AST."""
        function_calls = set()
        
        try:
            # Find all function calls
            for call_node in ast.find_data('call_expression'):
                function_name = self._get_function_name_from_call_node(call_node)
                if function_name:
                    function_calls.add(function_name)
        except Exception:
            pass  # If AST traversal fails, return empty set
        
        return function_calls
    
    def _get_function_name_from_node(self, node) -> str:
        """Extract function name from a function expression node."""
        try:
            if hasattr(node, 'children') and len(node.children) > 0:
                name_node = node.children[0]
                if hasattr(name_node, 'value'):
                    return name_node.value
        except Exception:
            pass
        return ""
    
    def _get_function_name_from_call_node(self, node) -> str:
        """Extract function name from a call expression node."""
        try:
            if hasattr(node, 'children') and len(node.children) > 0:
                # The first child should be the function being called
                function_node = node.children[0]
                if hasattr(function_node, 'value'):
                    return function_node.value
                elif hasattr(function_node, 'children') and len(function_node.children) > 0:
                    # Handle cases like obj.method()
                    return function_node.children[-1].value if hasattr(function_node.children[-1], 'value') else ""
        except Exception:
            pass
        return ""