from ...base import Rule, Finding
from ...line_number_utils import LineNumberUtils
from ....models import PMDModel
from typing import Dict, Any, List


class FooterPodRequiredRule(Rule):
    """Ensures footer uses pod structure - either direct pod or footer with pod children."""
    
    DESCRIPTION = "Ensures footer uses pod structure (direct pod or footer with pod children)"
    SEVERITY = "INFO"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes the footer structure within a PMD model."""
        if not pmd_model.presentation or not pmd_model.presentation.footer:
            return

        footer = pmd_model.presentation.footer
        if not isinstance(footer, dict):
            return

        # Check if footer is missing entirely
        if not footer:
            yield Finding(
                rule=self,
                message="Footer section is missing. Footer should use pod structure.",
                line=1,
                column=1,
                file_path=pmd_model.file_path
            )
            return

        # Check if footer uses direct pod structure
        if footer.get('type') == 'pod':
            return  # Valid pod structure

        # Check if footer uses footer type with pod children
        if footer.get('type') == 'footer':
            children = footer.get('children', [])
            if not isinstance(children, list) or len(children) == 0:
                line_number = self._get_footer_line_number(pmd_model)
                yield Finding(
                    rule=self,
                    message="Footer must utilize a pod.",
                    line=line_number,
                    column=1,
                    file_path=pmd_model.file_path
                )
                return

            # Check if the first (and only expected) child is a pod
            if len(children) > 0:
                child = children[0]
                if isinstance(child, dict) and child.get('type') == 'pod':
                    return  # Valid pod child
                else:
                    line_number = self._get_footer_line_number(pmd_model)
                    yield Finding(
                        rule=self,
                        message="Footer must utilize a pod.",
                        line=line_number,
                        column=1,
                        file_path=pmd_model.file_path
                    )
            else:
                line_number = self._get_footer_line_number(pmd_model)
                yield Finding(
                    rule=self,
                    message="Footer must utilize a pod.",
                    line=line_number,
                    column=1,
                    file_path=pmd_model.file_path
                )
            return

        # If we get here, footer has invalid structure
        line_number = self._get_footer_line_number(pmd_model)
        yield Finding(
            rule=self,
            message="Footer must utilize a pod.",
            line=line_number,
            column=1,
            file_path=pmd_model.file_path
        )

    def _get_footer_line_number(self, pmd_model: PMDModel) -> int:
        """Get approximate line number for the footer section."""
        return LineNumberUtils.find_section_line_number(pmd_model, 'footer')
