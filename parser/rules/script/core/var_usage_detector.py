"""Variable usage detection logic for ScriptVarUsageRule."""

from typing import Generator
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class VarUsageDetector(ScriptDetector):
    """Detects use of 'var' instead of 'let' or 'const' in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(line_offset)
        self.file_path = file_path
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect use of 'var' declarations in the AST."""
        # Find all variable_statement nodes in the AST
        var_statements = ast.find_data('variable_statement')
        for var_stmt in var_statements:
            # Check if the variable statement uses VAR keyword
            if len(var_stmt.children) > 0 and hasattr(var_stmt.children[0], 'type') and var_stmt.children[0].type == 'VAR':
                # Get the variable declaration (second child)
                var_declaration = var_stmt.children[1]
                if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                    var_name = var_declaration.children[0].value
                    # Get line number from the VAR token (first child)
                    relative_line = getattr(var_stmt.children[0], 'line', 1) or 1
                    line_number = self.line_offset + relative_line - 1
                    
                    yield Violation(
                        message=f"File section '{field_name}' uses 'var' declaration for variable '{var_name}'. Consider using 'let' or 'const' instead.",
                        line=line_number,
                        column=1
                    )
