from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


class PMDSecurityDomainRule(Rule):
    """Ensures PMD pages have required security domains defined."""
    
    DESCRIPTION = "Ensures PMD pages have at least one security domain defined"
    SEVERITY = "SEVERE"

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze all PMD models for security domain requirements."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Check if a PMD model has required security domains."""
        # Check if securityDomains is missing or empty
        # The compiler ensures domain validity, so we only check for presence
        if not pmd_model.securityDomains or len(pmd_model.securityDomains) == 0:
            yield Finding(
                rule=self,
                file_path=pmd_model.file_path,
                line=1,  # Security domains are typically defined at the top of PMD files
                message="PMD page is missing required securityDomains list. All PMD pages must define at least one security domain."
            )
