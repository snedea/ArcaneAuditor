from typing import Generator
from ...base import Finding
from ...line_number_utils import LineNumberUtils
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class FooterPodRequiredRule(StructureRuleBase):
    """Ensures footer uses pod structure - either direct pod or footer with pod children."""
    
    DESCRIPTION = "Ensures footer uses pod structure (direct pod or footer with pod children)"
    SEVERITY = "INFO"

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes the footer structure within a PMD model."""
        if not pmd_model.presentation:
            return

        footer = pmd_model.presentation.footer
        if not isinstance(footer, dict):
            return

        # Check if footer is missing entirely or empty
        if not footer or len(footer) == 0:
            yield self._create_finding(
                message="Footer section is missing. Footer should use pod structure.",
                file_path=pmd_model.file_path,
                line=1
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
                yield self._create_finding(
                    message="Footer must utilize a pod.",
                    file_path=pmd_model.file_path,
                    line=line_number
                )
                return

            # Check if the first (and only expected) child is a pod
            if len(children) > 0:
                child = children[0]
                if isinstance(child, dict) and child.get('type') == 'pod':
                    return  # Valid pod child
                else:
                    line_number = self._get_footer_line_number(pmd_model)
                    yield self._create_finding(
                        message="Footer must utilize a pod.",
                        file_path=pmd_model.file_path,
                        line=line_number
                    )
            else:
                line_number = self._get_footer_line_number(pmd_model)
                yield self._create_finding(
                    message="Footer must utilize a pod.",
                    file_path=pmd_model.file_path,
                    line=line_number
                )
            return

        # If we get here, footer has invalid structure
        line_number = self._get_footer_line_number(pmd_model)
        yield self._create_finding(
            message="Footer must utilize a pod.",
            file_path=pmd_model.file_path,
            line=line_number
        )

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't have footers, so this rule doesn't apply to them."""
        return
        yield  # This line will never be reached, but makes it a generator

    def _get_footer_line_number(self, pmd_model: PMDModel) -> int:
        """Get approximate line number for the footer section."""
        return LineNumberUtils.find_section_line_number(pmd_model, 'footer')
