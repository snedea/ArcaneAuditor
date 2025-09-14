"""
Example Custom Rule - Custom Script Comment Quality Rule

This is an example of how to create a custom validation rule.
It demonstrates the basic structure and patterns to follow.
"""

from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel
from typing import List


class CustomScriptCommentQualityRule(Rule):
    """
    Example custom rule that checks for minimum comment density in script functions.
    
    This rule demonstrates:
    - Custom rule class name (CustomScriptCommentQualityRule)
    - Basic rule structure
    - Script parsing and analysis
    - Finding generation
    """
    
    IS_EXAMPLE = True  # Flag to exclude from automatic discovery
    
    def __init__(self):
        super().__init__()
        self.ID = "RULE000"  # Base class default
        self.SEVERITY = "INFO"
        self.DESCRIPTION = "Functions should have at least one comment for every 10 lines of code"
        self.min_comment_density = 0.1  # 10% comment density minimum
    
    def analyze(self, context: ProjectContext) -> List[Finding]:
        """Analyze PMD files for comment quality violations."""
        findings = []
        
        for pmd_file in context.pmds.values():
            if pmd_file.script:
                findings.extend(self._analyze_script_content(pmd_file))
        
        return findings
    
    def _analyze_script_content(self, pmd_file: PMDModel) -> List[Finding]:
        """Analyze script content for comment quality."""
        findings = []
        
        try:
            # Parse the script content
            script_ast = self._parse_script_content(pmd_file.script)
            
            # Find all function definitions
            functions = self._find_functions(script_ast)
            
            for func in functions:
                comment_density = self._calculate_comment_density(func, pmd_file.script)
                
                if comment_density < self.min_comment_density:
                    finding = Finding(
                        rule=self,
                        message=f"Function '{func.get('name', 'anonymous')}' has low comment density "
                               f"({comment_density:.1%}). Consider adding more comments to improve readability.",
                        line=self._get_line_number(func),
                        column=1,
                        file_path=pmd_file.file_path
                    )
                    findings.append(finding)
        
        except Exception as e:
            # Handle parsing errors gracefully
            print(f"Error analyzing script in {pmd_file.file_path}: {e}")
        
        return findings
    
    def _find_functions(self, ast) -> List[dict]:
        """Find all function definitions in the AST."""
        # This is a simplified example - you'd need to implement proper AST traversal
        functions = []
        # Implementation would depend on the AST structure from your parser
        return functions
    
    def _calculate_comment_density(self, func: dict, script_content: str) -> float:
        """Calculate comment density for a function."""
        # This is a simplified example - you'd need to implement proper analysis
        # Count comment lines vs total lines within the function scope
        return 0.15  # Example: 15% comment density
    
    def _get_line_number(self, func: dict) -> int:
        """Get the line number for a function."""
        # This would extract the actual line number from the AST
        return 1  # Example line number
