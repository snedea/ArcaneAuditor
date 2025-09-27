"""Detector for unused functions in script code."""

from typing import Any, List, Set
from ...script.shared import ScriptDetector, Violation
from ...script.shared.ast_utils import get_line_number


class UnusedFunctionsDetector(ScriptDetector):
    """Detects unused functions in script code."""

    def __init__(self, file_path: str = "", line_offset: int = 1, all_declared_functions: Set[str] = None, all_function_calls: Set[str] = None):
        """Initialize detector with file context and function registry."""
        super().__init__(file_path, line_offset)
        self.all_declared_functions = all_declared_functions or set()
        self.all_function_calls = all_function_calls or set()

    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """
        Analyze AST and return list of unused function violations.
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Find all function expressions in this script
        for function_node in ast.find_data('function_expression'):
            function_name = self._get_function_name(function_node)
            
            if function_name and function_name not in self.all_function_calls:
                violations.append(Violation(
                    message=f"Unused function '{function_name}' - function is declared but never called",
                    line=self.get_line_number(function_node),
                    column=1,
                    metadata={
                        'function_name': function_name
                    }
                ))
        
        return violations

    def _get_function_name(self, node: Any) -> str:
        """Extract function name from a function expression node."""
        if hasattr(node, 'children') and len(node.children) > 0:
            name_node = node.children[0]
            if hasattr(name_node, 'value'):
                return name_node.value
        return ""
