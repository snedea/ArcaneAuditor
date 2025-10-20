"""
Example Custom Rule - Custom Script Comment Quality Rule

This is an example of how to create a custom validation rule using the
Arcane Auditor unified architecture. It demonstrates:

- Unified rule architecture with ScriptRuleBase
- Generator-based analysis pattern
- Dual script analysis (PMD embedded + standalone script files)  
- Clean violation creation (line numbers only, no column tracking)
- Context-based AST caching for performance
- Hash-based line number calculation (exact, no off-by-one errors)
- Proper error handling and AST parsing
- Configuration support through custom_settings and apply_settings method
- Readable widget paths with id/label/type priority
"""

from typing import Generator, List
from lark import Tree
from ...script.shared import ScriptRuleBase, ScriptDetector, Violation
from ...base import Finding
from ....models import ProjectContext


# Step 1: Create Detector (AST detection logic)
class CommentQualityDetector(ScriptDetector):
    """Detects functions with low comment density."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1, min_comment_density: float = 0.1, min_function_lines: int = 5):
        """Initialize detector with configuration."""
        super().__init__(file_path, line_offset)
        self.min_comment_density = min_comment_density
        self.min_function_lines = min_function_lines
    
    def detect(self, ast: Tree, field_name: str = "") -> List[Violation]:
        """Find functions with low comment density."""
        violations = []
        
        # Find all function definitions in the AST
        functions = self._find_functions_in_ast(ast)
        
        for func_info in functions:
            comment_density = self._calculate_comment_density(func_info)
            
            # Only check functions that meet minimum line threshold
            if func_info['line_count'] >= self.min_function_lines and comment_density < self.min_comment_density:
                line_number = self.get_line_from_tree_node(func_info['node'])
                
                violations.append(Violation(
                    message=f"Function '{func_info['name']}' has low comment density "
                           f"({comment_density:.1%}, minimum: {self.min_comment_density:.1%}). "
                           f"Consider adding comments to improve code maintainability.",
                    line=line_number,
                    metadata={'function_name': func_info['name'], 'density': comment_density}
                ))
        
        return violations
    
    def _find_functions_in_ast(self, ast: Tree) -> list:
        """Find all function definitions in the AST."""
        functions = []
        
        # Find function declaration nodes
        for func_node in ast.find_data('function_declaration'):
            func_name = self._extract_function_name(func_node)
            line_count = self._estimate_function_length(func_node)
            
            functions.append({
                'name': func_name,
                'node': func_node,
                'line_count': line_count
            })
        
        return functions
    
    def _extract_function_name(self, func_node: Tree) -> str:
        """Extract function name from AST node."""
        # Simplified - in real implementation, traverse the AST properly
        if len(func_node.children) > 0:
            return str(func_node.children[0]) if hasattr(func_node.children[0], 'value') else 'anonymous'
        return 'anonymous'
    
    def _estimate_function_length(self, func_node: Tree) -> int:
        """Estimate function length from AST node."""
        # Simplified estimation - in real implementation, calculate actual line count
        return 10  # Placeholder
    
    def _calculate_comment_density(self, func_info: dict) -> float:
        """Calculate comment density for a function."""
        # Simplified calculation - in real implementation, analyze actual comments
        return 0.05  # Placeholder - 5% comment density


# Step 2: Create Rule (orchestration)
class CustomScriptCommentQualityRule(ScriptRuleBase):
    """
    Example custom rule that checks for minimum comment density in script functions.
    
    This rule demonstrates the detector pattern:
    - Detector handles AST analysis and violation detection
    - Rule orchestrates detector usage and configuration
    - Clean separation of concerns
    """
    
    IS_EXAMPLE = True  # Flag to exclude from automatic discovery
    
    DESCRIPTION = "Functions should have adequate comments for maintainability (configurable threshold)"
    SEVERITY = "ADVICE"
    DETECTOR = CommentQualityDetector  # Reference to detector class
    
    def __init__(self, config: dict = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        # Default values - can be overridden via apply_settings()
        self.min_comment_density = 0.1  # 10% default
        self.min_function_lines = 5  # Only check functions > 5 lines
        
        # Apply initial configuration if provided
        if config:
            self.apply_settings(config)
    
    def apply_settings(self, settings: dict):
        """
        Apply custom settings to the rule.
        This method is called by the rules engine to apply configuration.
        
        Args:
            settings: Dictionary containing custom settings
        """
        if 'min_comment_density' in settings:
            self.min_comment_density = settings['min_comment_density']
        if 'min_function_lines' in settings:
            self.min_function_lines = settings['min_function_lines']
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _create_detector(self, file_path: str, line_offset: int) -> CommentQualityDetector:
        """Create detector instance with current configuration."""
        return CommentQualityDetector(
            file_path=file_path,
            line_offset=line_offset,
            min_comment_density=self.min_comment_density,
            min_function_lines=self.min_function_lines
        )


# Additional example: Structure validation rule using unified architecture
from ...structure.shared import StructureRuleBase
from ...base import Finding
from ....models import PodModel, PMDModel, ProjectContext

class CustomPMDSectionValidationRule(StructureRuleBase):
    """
    Example custom PMD structure rule.
    
    Demonstrates validation of PMD file structure and organization.
    """
    
    IS_EXAMPLE = True  # Exclude from discovery
    
    DESCRIPTION = "PMD files should follow organizational structure standards"
    SEVERITY = "ACTION"
    
    def __init__(self, config: dict = None):
        """Initialize with configuration."""
        self.config = config or {}
        # Default values - can be overridden via apply_settings()
        self.required_sections = ['id', 'presentation']
        self.max_endpoints = 10
        
        # Apply initial configuration if provided
        if config:
            self.apply_settings(config)
    
    def apply_settings(self, settings: dict):
        """
        Apply custom settings to the rule.
        This method is called by the rules engine to apply configuration.
        
        Args:
            settings: Dictionary containing custom settings
        """
        if 'required_sections' in settings:
            self.required_sections = settings['required_sections']
        if 'max_endpoints' in settings:
            self.max_endpoints = settings['max_endpoints']
    
    def get_description(self) -> str:
        """Required by StructureRuleBase."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD structure compliance."""
        yield from self._validate_pmd_structure(pmd_model)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't need structure validation for this rule."""
        yield  # Make it a generator
    
    def _validate_pmd_structure(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Validate PMD file structure."""
        
        # Check for required sections
        for section in self.required_sections:
            if not hasattr(pmd_model, section) or getattr(pmd_model, section) is None:
                # Use unified line calculation method for consistency
                line_number = self.get_section_line_number(pmd_model, section) if section != 'id' else 1
                yield Finding(
                    rule=self,
                    message=f"PMD file is missing required section: '{section}'. "
                           f"This section is required by organizational standards.",
                    line=line_number,
                    file_path=pmd_model.file_path
                )
        
        # Check endpoint count
        if pmd_model.endpoints and len(pmd_model.endpoints) > self.max_endpoints:
            yield Finding(
                rule=self,
                message=f"PMD has too many endpoints ({len(pmd_model.endpoints)} > {self.max_endpoints}). "
                       f"Consider splitting into multiple PMD files for better maintainability.",
                line=1,
                file_path=pmd_model.file_path
            )


# Example configuration for these rules:
"""
{
  "rules": {
    "CustomScriptCommentQualityRule": {
      "enabled": true,
      "severity_override": "ADVICE",
      "custom_settings": {
        "min_comment_density": 0.15,
        "min_function_lines": 8
      }
    },
    "CustomPMDSectionValidationRule": {
      "enabled": true,
      "severity_override": "ACTION",
      "custom_settings": {
        "required_sections": ["id", "presentation", "endPoints"],
        "max_endpoints": 5
      }
    }
  }
}
"""