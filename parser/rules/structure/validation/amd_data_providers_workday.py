#!/usr/bin/env python3
"""AMD dataProviders workday.com rule."""

import re
from typing import Generator, List, Dict, Any
from parser.rules.structure.shared.rule_base import StructureRuleBase
from parser.rules.base import Finding
from parser.models import ProjectContext


class AMDDataProvidersWorkdayRule(StructureRuleBase):
    """Rule to check for hardcoded *.workday.com URLs in AMD dataProviders."""

    ID = "AMDDataProvidersWorkdayRule"
    DESCRIPTION = "Ensures AMD dataProviders don't use hardcoded *.workday.com URLs"
    SEVERITY = "ACTION"

    def __init__(self):
        """Initialize the rule."""
        super().__init__()
        # Pattern to match *.workday.com URLs (both HTTP and HTTPS)
        self.workday_url_pattern = re.compile(
            r'https?://[a-zA-Z0-9.-]*\.workday\.com[^\s\'"]*',
            re.IGNORECASE
        )

    def visit_pmd(self, pmd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """PMD files don't need this validation."""
        return
        yield

    def visit_pod(self, pod_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't need this validation."""
        return
        yield

    def visit_amd(self, amd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        Analyze AMD file for hardcoded *.workday.com URLs in dataProviders.
        
        Args:
            amd_model: AMD model from ProjectContext
            context: ProjectContext containing file information
            
        Yields:
            Finding objects for each violation
        """
        # Check if dataProviders exist in the AMD model
        data_providers = amd_model.dataProviders or []
        if not data_providers:
            return
            yield
        
        # Check each dataProvider
        for provider in data_providers:
            if not isinstance(provider, dict):
                continue
                
            key = provider.get("key", "")
            value = provider.get("value", "")
            
            if not isinstance(value, str):
                continue
            
            # Check if the value contains hardcoded *.workday.com URLs
            if self.workday_url_pattern.search(value):
                finding = Finding(
                    rule=self,
                    message=f"AMD dataProvider '{key}' uses hardcoded *.workday.com URL: '{value}'. "
                           f"Consider using apiGatewayEndpoint variable instead for better portability.",
                    line=1,  # We don't have line tracking for AMD files yet
                    file_path=amd_model.file_path
                )
                yield finding

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
