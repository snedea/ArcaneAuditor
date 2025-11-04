"""
Rule to validate that file names follow lowerCamelCase naming convention.

All Workday Extend files (PMD, POD, AMD, SMD, Script) should follow lowerCamelCase
naming convention for consistency and maintainability.
"""
import re
import os
from typing import Generator

from ...base import Finding, Rule
from ....models import ProjectContext


class FileNameLowerCamelCaseRule(Rule):
    """
    Validates that all file names follow lowerCamelCase naming convention.
    
    This rule checks:
    - PMD files
    - POD files
    - Script files
    
    Valid pattern: starts with lowercase letter, followed by letters/numbers
    Examples: myPage.pmd, helperFunctions.script
    """
    
    ID = "FileNameLowerCamelCaseRule"
    DESCRIPTION = "Ensures all file names follow lowerCamelCase naming convention"
    SEVERITY = "ADVICE"
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        Analyze all files in the context for naming convention compliance.
        
        Args:
            context: The fully-built ProjectContext containing all application models.
            
        Yields:
            Finding objects for any files with invalid naming conventions.
        """
        # Check PMD files
        for pmd_model in context.pmds.values():
            yield from self._check_filename(pmd_model.file_path)
        
        # Check POD files
        for pod_model in context.pods.values():
            yield from self._check_filename(pod_model.file_path)

        # Check Script files
        for script_model in context.scripts.values():
            yield from self._check_filename(script_model.file_path)
    
    def _check_filename(self, file_path: str) -> Generator[Finding, None, None]:
        """
        Check if a filename follows lowerCamelCase convention.
        
        Args:
            file_path: Path to the file (can include directory path)
            
        Yields:
            Finding if the filename doesn't follow lowerCamelCase convention.
        """
        if not file_path:
            return
        
        # Extract just the filename (without path) and without extension
        filename_with_ext = os.path.basename(file_path)
        
        # Strip job ID prefix if present (format: uuid_filename.ext)
        # Job IDs are UUIDs with dashes in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        # Only match actual UUIDs (8-4-4-4-12 hex digits), not arbitrary hex sequences
        filename_with_ext = re.sub(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', '', filename_with_ext)
        
        filename, ext = os.path.splitext(filename_with_ext)
        
        # Pattern: must start with lowercase letter, followed by letters/numbers
        # Valid: myPage, helperFunctions
        # Invalid: MyPage, my_page, MYPAGE, 2myPage, helper_functions
        
        # Pure lowerCamelCase (no underscores)
        pure_camel_case = re.compile(r'^[a-z][a-zA-Z0-9]*$')

        # Check if it matches either pattern
        if not (pure_camel_case.match(filename)):
            yield Finding(
                rule=self,
                message=f"File '{filename_with_ext}' doesn't follow lowerCamelCase naming convention. Should start with lowercase letter and use camelCase (e.g., 'myPage.pmd', 'helperFunctions.script').",
                file_path=file_path,
                line=1
            )

