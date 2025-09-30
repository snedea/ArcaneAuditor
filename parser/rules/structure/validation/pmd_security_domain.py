from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


class PMDSecurityDomainRule(Rule):
    """Ensures PMD pages have required security domains with selective exclusions."""
    
    DESCRIPTION = "Ensures PMD pages have at least one security domain defined (excludes microConclusion and error pages)"
    SEVERITY = "SEVERE"

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze all PMD models for security domain requirements."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model, context)

    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Check if a PMD model has required security domains with selective exclusions."""
        # Check if this page should be excluded from security domain requirements
        
        # Exclusion 1: MicroConclusion pages (presentation.microConclusion: true)
        if self._is_micro_conclusion_page(pmd_model):
            return  # Skip security domain check for microConclusion pages
        
        # Exclusion 2: Error pages (page ID in SMD errorPageConfigurations)
        if self._is_error_page(pmd_model, context):
            return  # Skip security domain check for error pages
        
        # Check if securityDomains is missing or empty for pages that require it
        # The compiler ensures domain validity, so we only check for presence
        if not pmd_model.securityDomains or len(pmd_model.securityDomains) == 0:
            yield Finding(
                rule=self,
                file_path=pmd_model.file_path,
                line=1,  # Security domains are typically defined at the top of PMD files
                message="PMD page is missing required securityDomains list. All PMD pages must define at least one security domain (excludes microConclusion and error pages)."
            )
    
    def _is_micro_conclusion_page(self, pmd_model: PMDModel) -> bool:
        """Check if the PMD page is a microConclusion page."""
        if not pmd_model.presentation:
            return False
        
        # Check if presentation.microConclusion is true
        # microConclusion is stored in the attributes dictionary
        return pmd_model.presentation.attributes.get('microConclusion', False) is True
    
    def _is_error_page(self, pmd_model: PMDModel, context: ProjectContext) -> bool:
        """Check if the PMD page is an error page defined in any SMD."""
        if not context.smd:
            return False
        
        # Get all error page IDs from the SMD file
        error_page_ids = set()
        error_pages = context.smd.get_error_pages()
        for error_page in error_pages:
            page_id = error_page.get('pageId', '')
            if page_id:
                error_page_ids.add(page_id)
        
        # Check if this PMD's pageId is in the error pages list
        return pmd_model.pageId in error_page_ids
