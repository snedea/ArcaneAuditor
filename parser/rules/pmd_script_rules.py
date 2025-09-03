# In rules/pmd_script_rules.py
from ..models import PMDModel
from .base import Rule, Finding
from lark import Tree

class NoVarInPMDRule(Rule):
    ID = "PMD001"
    DESCRIPTION = "Detects the use of 'var' in PMD Script."
    SEVERITY = "INFO"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes the onLoad script within a PMD model."""
        script_ast = pmd_model.get_onLoad_ast()
        
        if not script_ast:
            return

        # Lark's AST has a `find_data` method to find all nodes of a certain type
        for var_node in script_ast.find_data("variable_statement"):
            # The node object contains line and column info
            yield Finding(
                rule=self,
                message="Legacy 'var' declaration found. Use 'let' or 'const' instead.",
                line=var_node.line,
                column=var_node.column,
            )