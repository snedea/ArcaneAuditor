"""Detector for unused functions in script code."""

from typing import Any, List, Set
from lark import Tree
from ...script.shared import ScriptDetector, Violation
from ...common import ASTLineUtils


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
        
        In PMD Script, all functions are anonymous and assigned to variables.
        We check if the variable name is in the list of declared functions
        but not in the list of function calls.
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Check which declared function variables are never called
        unused_functions = self.all_declared_functions - self.all_function_calls
        
        # For each unused function, find its declaration line and report it
        for var_name in unused_functions:
            line_number = self._find_function_variable_declaration_line(ast, var_name)
            if line_number:
                violations.append(Violation(
                    message=f"Unused function variable '{var_name}' - function is declared but never called",
                    line=line_number,
                    metadata={
                        'variable_name': var_name
                    }
                ))
        
        return violations

    def _find_function_variable_declaration_line(self, ast: Any, var_name: str) -> int:
        """Find the line number where a function variable is declared."""
        try:
            for var_statement in ast.find_data('variable_statement'):
                for child in var_statement.iter_subtrees():
                    if child.data == 'variable_declaration':
                        if len(child.children) >= 1:
                            identifier = child.children[0]
                            if hasattr(identifier, 'value') and identifier.value == var_name:
                                # Check if it's a function assignment
                                if len(child.children) >= 2:
                                    initializer = child.children[1]
                                    if self._is_function_assignment(initializer):
                                        return self.get_line_from_tree_node(var_statement)
        except Exception:
            pass
        return self.line_offset
    
    def _is_function_assignment(self, initializer_node: Any) -> bool:
        """Check if an initializer node assigns a function."""
        try:
            for subtree in initializer_node.iter_subtrees():
                if subtree.data in ('function_expression', 'arrow_function_expression'):
                    return True
        except Exception:
            pass
        return False
