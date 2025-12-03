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

PATTERN COMPARISON:
- Pattern 1: Constructor parameters (valid but more complex)
- Pattern 2: Set attributes after creation (RECOMMENDED - simpler)
"""

from typing import Generator
from lark import Tree
from ...script.shared import ScriptRuleBase, ScriptDetector
from ...common import Violation
from ...base import Finding
from ....models import ProjectContext


# Step 1: Create Detector (AST detection logic)
class CommentQualityDetector(ScriptDetector):
    """Detects functions with low comment density."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        """Initialize detector with file info only."""
        super().__init__(file_path, line_offset)
        # Configuration defaults - will be set by rule
        self.min_comment_density = 0.1
        self.min_function_lines = 5
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Find functions with low comment density."""
        # Find all function definitions in the AST
        functions = self._find_functions_in_ast(ast)
        
        for func_info in functions:
            comment_density = self._calculate_comment_density(func_info)
            
            # Only check functions that meet minimum line threshold
            if func_info['line_count'] >= self.min_function_lines and comment_density < self.min_comment_density:
                line_number = self.get_line_from_tree_node(func_info['node'])
                
                yield Violation(
                    message=f"Function '{func_info['name']}' has low comment density "
                           f"({comment_density:.1%}, minimum: {self.min_comment_density:.1%}). "
                           f"Consider adding comments to improve code maintainability.",
                    line=line_number
                )
    
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
    - Custom settings support via AVAILABLE_SETTINGS
    - Grimoire documentation via DOCUMENTATION
    
    PATTERN 2 (RECOMMENDED): Set attributes after detector creation
    This is simpler and more flexible than passing parameters to constructor.
    """
    
    IS_EXAMPLE = True  # Flag to exclude from automatic discovery
    
    DESCRIPTION = "Functions should have adequate comments for maintainability (configurable threshold)"
    SEVERITY = "ADVICE"
    DETECTOR = CommentQualityDetector  # Reference to detector class
    
    # Define custom settings that users can configure in the UI
    AVAILABLE_SETTINGS = {
        'min_comment_density': {
            'type': 'float',
            'default': 0.1,
            'description': 'Minimum comment density required (0.0 to 1.0, where 0.1 = 10%)'
        },
        'min_function_lines': {
            'type': 'int',
            'default': 5,
            'description': 'Minimum function length (in lines) before checking comment density'
        }
    }
    
    # Grimoire documentation - displayed in the UI when users view rule details
    DOCUMENTATION = {
        'why': '''Well-commented code is easier to understand, maintain, and debug. Functions without adequate comments force developers to read through implementation details to understand purpose and behavior. Comments explain the "why" behind code, making it self-documenting and reducing cognitive load for future maintainers.''',
        'catches': [
            'Functions with low comment density (fewer comments relative to code)',
            'Long functions without explanatory comments',
            'Functions that require reading implementation to understand purpose'
        ],
        'examples': '''**Example violations:**

```javascript
// ❌ Function with low comment density
const processPayment = function(amount, currency) {
    const rate = getExchangeRate(currency);
    const converted = amount * rate;
    const fee = calculateFee(converted);
    const total = converted + fee;
    return submitPayment(total);
    // No comments explaining the logic flow
};
```

**Fix:**

```javascript
// ✅ Well-commented function
const processPayment = function(amount, currency) {
    // Convert amount to base currency using current exchange rate
    const rate = getExchangeRate(currency);
    const converted = amount * rate;
    
    // Calculate processing fee (2% of converted amount)
    const fee = calculateFee(converted);
    const total = converted + fee;
    
    // Submit payment to payment gateway
    return submitPayment(total);
};
```''',
        'recommendation': 'Add comments to explain the purpose and logic flow of functions, especially for complex operations. Comments should explain "why" rather than "what" (the code already shows what). Focus on business logic, edge cases, and non-obvious decisions.'
    }
    
    def __init__(self, config: dict = None):
        """Initialize with optional configuration."""
        super().__init__()
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
    
    def _check(self, script_content: str, field_name: str, file_path: str, 
               line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """
        Override _check to pass configuration to detector.
        This demonstrates PATTERN 2 (RECOMMENDED): Set attributes after creation.
        """
        # Parse the script content with context for caching
        ast = self._parse_script_content(script_content, context)
        if not ast:
            return
        
        # Create detector and configure it (PATTERN 2 - RECOMMENDED)
        detector = self.DETECTOR(file_path, line_offset)
        detector.min_comment_density = self.min_comment_density
        detector.min_function_lines = self.min_function_lines
        
        # Use detector to find violations and yield them directly
        for violation in detector.detect(ast, field_name):
            yield Finding(
                rule=self,
                message=violation.message,
                line=violation.line,
                file_path=file_path
            )


# Alternative Pattern 1 Example (for comparison):
class CommentQualityDetectorPattern1(ScriptDetector):
    """
    Alternative detector using PATTERN 1: Constructor parameters.
    This is valid but more complex than Pattern 2.
    """
    
    def __init__(self, file_path: str = "", line_offset: int = 1, 
                 min_comment_density: float = 0.1, min_function_lines: int = 5):
        """Initialize detector with configuration parameters."""
        super().__init__(file_path, line_offset)
        self.min_comment_density = min_comment_density
        self.min_function_lines = min_function_lines
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Find functions with low comment density."""
        # Same implementation as Pattern 2 detector
        functions = self._find_functions_in_ast(ast)
        
        for func_info in functions:
            comment_density = self._calculate_comment_density(func_info)
            
            if func_info['line_count'] >= self.min_function_lines and comment_density < self.min_comment_density:
                line_number = self.get_line_from_tree_node(func_info['node'])
                
                yield Violation(
                    message=f"Function '{func_info['name']}' has low comment density "
                           f"({comment_density:.1%}, minimum: {self.min_comment_density:.1%}). "
                           f"Consider adding comments to improve code maintainability.",
                    line=line_number
                )
    
    def _find_functions_in_ast(self, ast: Tree) -> list:
        """Find all function definitions in the AST."""
        functions = []
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
        if len(func_node.children) > 0:
            return str(func_node.children[0]) if hasattr(func_node.children[0], 'value') else 'anonymous'
        return 'anonymous'
    
    def _estimate_function_length(self, func_node: Tree) -> int:
        """Estimate function length from AST node."""
        return 10  # Placeholder
    
    def _calculate_comment_density(self, func_info: dict) -> float:
        """Calculate comment density for a function."""
        return 0.05  # Placeholder - 5% comment density


class CustomScriptCommentQualityRulePattern1(ScriptRuleBase):
    """
    Alternative rule using PATTERN 1: Constructor parameters.
    This is valid but more complex than Pattern 2.
    """
    
    IS_EXAMPLE = True
    DESCRIPTION = "Functions should have adequate comments for maintainability (Pattern 1 example)"
    SEVERITY = "ADVICE"
    DETECTOR = CommentQualityDetectorPattern1
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self.min_comment_density = 0.1
        self.min_function_lines = 5
        
        if config:
            self.apply_settings(config)
    
    def apply_settings(self, settings: dict):
        """Apply custom settings to the rule."""
        if 'min_comment_density' in settings:
            self.min_comment_density = settings['min_comment_density']
        if 'min_function_lines' in settings:
            self.min_function_lines = settings['min_function_lines']
    
    def get_description(self) -> str:
        return self.DESCRIPTION
    
    def _check(self, script_content: str, field_name: str, file_path: str, 
               line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """
        Override _check using PATTERN 1: Constructor parameters.
        This is more complex than Pattern 2.
        """
        ast = self._parse_script_content(script_content, context)
        if not ast:
            return
        
        # PATTERN 1: Pass configuration to constructor
        detector = self.DETECTOR(
            file_path=file_path,
            line_offset=line_offset,
            min_comment_density=self.min_comment_density,
            min_function_lines=self.min_function_lines
        )
        
        # Use detector to find violations
        for violation in detector.detect(ast, field_name):
            yield Finding(
                rule=self,
                message=violation.message,
                line=violation.line,
                file_path=file_path
            )


# Additional example: Structure validation rule using unified architecture
from ...structure.shared import StructureRuleBase
from ...base import Finding
from ....models import PodModel, PMDModel, ProjectContext

class CustomPMDSectionValidationRule(StructureRuleBase):
    """
    Example custom PMD structure rule.
    
    Demonstrates validation of PMD file structure and organization.
    Includes custom settings and Grimoire documentation.
    """
    
    IS_EXAMPLE = True  # Exclude from discovery
    
    DESCRIPTION = "PMD files should follow organizational structure standards"
    SEVERITY = "ACTION"
    
    # Define custom settings that users can configure in the UI
    AVAILABLE_SETTINGS = {
        'required_sections': {
            'type': 'list',
            'default': ['id', 'presentation'],
            'description': 'List of required section names that must be present in PMD files'
        },
        'max_endpoints': {
            'type': 'int',
            'default': 10,
            'description': 'Maximum number of endpoints allowed per PMD file'
        }
    }
    
    # Grimoire documentation - displayed in the UI when users view rule details
    DOCUMENTATION = {
        'why': '''PMD files that follow consistent organizational structure are easier to navigate, maintain, and review. Required sections ensure all necessary configuration is present, and limiting endpoint count prevents files from becoming too complex and hard to manage.''',
        'catches': [
            'PMD files missing required organizational sections',
            'PMD files with too many endpoints (indicating need for splitting)',
            'Inconsistent file structure across the application'
        ],
        'examples': '''**Example violations:**

```json
// ❌ Missing required sections
{
  "id": "myPage",
  "endPoints": [...]
  // Missing 'presentation' section
}
```

**Fix:**

```json
// ✅ Complete structure with all required sections
{
  "id": "myPage",
  "presentation": {
    "body": {...}
  },
  "endPoints": [...]
}
```''',
        'recommendation': 'Ensure all PMD files include required organizational sections. If a PMD file has too many endpoints, consider splitting it into multiple focused files for better maintainability.'
    }
    
    def __init__(self, config: dict = None):
        """Initialize with configuration."""
        super().__init__()
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
# The custom_settings values correspond to the AVAILABLE_SETTINGS schema defined above
"""
{
  "rules": {
    "CustomScriptCommentQualityRule": {
      "enabled": true,
      "severity_override": "ADVICE",
      "custom_settings": {
        "min_comment_density": 0.15,  // Overrides default of 0.1 (10%)
        "min_function_lines": 8        // Overrides default of 5
      }
    },
    "CustomPMDSectionValidationRule": {
      "enabled": true,
      "severity_override": "ACTION",
      "custom_settings": {
        "required_sections": ["id", "presentation", "endPoints"],  // Overrides default list
        "max_endpoints": 5  // Overrides default of 10
      }
    }
  }
}
"""