"""
Example Custom Rule - Custom Script Comment Quality Rule

This is an example of how to create a custom validation rule using the modern
Arcane Auditor unified architecture (2025). It demonstrates:

- Unified rule architecture with ScriptRuleBase
- Generator-based analysis pattern
- Dual script analysis (PMD embedded + standalone script files)  
- Modern Violation creation (no column tracking - removed in 2025)
- Context-based AST caching for performance
- Hash-based line number calculation (exact, no off-by-one errors)
- Proper error handling and AST parsing
- Configuration support through custom_settings
- Readable widget paths with id/label/type priority
"""

from typing import Generator
from ...script.shared import ScriptRuleBase
from ...common.violation import Violation
from ...base import Finding
from ....models import ProjectContext, PMDModel


class CustomScriptCommentQualityRule(ScriptRuleBase):
    """
    Example custom rule that checks for minimum comment density in script functions.
    
    This rule demonstrates the modern Arcane Auditor unified architecture:
    - Unified rule architecture with ScriptRuleBase
    - Generator-based analysis (yields violations instead of returning lists)
    - Dual script analysis (PMD embedded scripts + standalone .script files)
    - Modern Violation creation with automatic field population
    - Configurable thresholds through custom_settings
    - Proper error handling for parsing failures
    """
    
    IS_EXAMPLE = True  # Flag to exclude from automatic discovery
    
    DESCRIPTION = "Functions should have adequate comments for maintainability (configurable threshold)"
    SEVERITY = "INFO"
    
    def __init__(self, config: dict = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        # Configurable threshold - can be overridden in rule configuration
        self.min_comment_density = self.config.get('min_comment_density', 0.1)  # 10% default
        self.min_function_lines = self.config.get('min_function_lines', 5)  # Only check functions > 5 lines
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        Modern unified analysis pattern: Uses ScriptRuleBase for automatic iteration.
        
        The ScriptRuleBase handles:
        1. PMD embedded scripts (onLoad, script, onSubmit, etc.) with hash-based line mapping
        2. POD embedded scripts with exact line numbers
        3. Standalone script files (util.script, helper.script, etc.)
        4. Context-based AST caching for performance
        5. Readable widget paths (id -> label -> type priority)
        """
        
        # Use the unified architecture - base class handles iteration
        # Iterate through all PMD files and their script fields
        for pmd_model in context.pmds.values():
            script_fields = self.find_script_fields(pmd_model, context)
            
            for field_path, field_value, display_name, line_offset in script_fields:
                # line_offset uses hash-based lookup for exact positioning
                yield from self._check_comment_quality(
                    field_value, 
                    display_name,  # Now includes readable widget identifiers!
                    pmd_model.file_path, 
                    line_offset,
                    context
                )
    
    
    def _check_comment_quality(self, script_content: str, field_name: str, file_path: str, line_offset: int, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """
        Check comment quality in script content using AST parsing.
        
        This demonstrates:
        - Using built-in script parser with context-level caching (faster, memory-efficient)
        - AST traversal for function detection
        - Comment density calculation
        - Modern Violation creation (no column tracking - removed in 2025)
        - Hash-based line numbers (exact positioning, no off-by-one errors)
        """
        try:
            # Parse script using built-in Lark grammar parser with context-level caching
            # Context caching avoids redundant parsing of duplicate scripts
            ast = self.get_cached_ast(script_content, context)
            
            if ast is None:
                return  # Skip if parsing failed
            
            # Find all function definitions in the AST
            functions = self._find_functions_in_ast(ast, script_content)
            
            for func_info in functions:
                comment_density = self._calculate_comment_density(func_info, script_content)
                
                # Only check functions that meet minimum line threshold
                if func_info['line_count'] >= self.min_function_lines and comment_density < self.min_comment_density:
                    # Create Violation (internal format for detectors)
                    violation = Violation(
                        message=f"Function '{func_info['name']}' has low comment density "
                               f"({comment_density:.1%}, minimum: {self.min_comment_density:.1%}). "
                               f"Consider adding comments to improve code maintainability.",
                        line=line_offset + func_info['start_line'],  # Hash-based line numbers are exact
                        metadata={'function_name': func_info['name'], 'density': comment_density}
                    )
                    
                    # Convert to Finding (external format for rules engine)
                    # Note: No column field - column tracking removed in 2025
                    yield Finding(
                        rule=self,  # Automatically populates rule_id, severity, description
                        message=violation.message,
                        line=violation.line,
                        file_path=file_path
                    )
        
        except Exception as e:
            # Handle parsing errors gracefully - don't crash the entire analysis
            print(f"Error analyzing script comments in {file_path} ({field_name}): {e}")
    
    def _find_functions_in_ast(self, ast, script_content: str) -> list:
        """
        Find all function definitions in the AST.
        
        This is a simplified example - in a real implementation you'd:
        1. Traverse the AST to find function_declaration nodes
        2. Extract function names, start/end positions
        3. Calculate line counts and positions
        """
        functions = []
        lines = script_content.split('\n')
        
        # Simple pattern matching for demonstration
        # In a real rule, you'd traverse the AST properly
        for i, line in enumerate(lines):
            if 'function' in line and ('=' in line or 'function ' in line):
                func_name = self._extract_function_name(line)
                if func_name:
                    # Calculate function boundaries (simplified)
                    start_line = i
                    end_line = self._find_function_end(lines, i)
                    line_count = end_line - start_line + 1
                    
                    functions.append({
                        'name': func_name,
                        'start_line': start_line,
                        'end_line': end_line,
                        'line_count': line_count,
                        'content': '\n'.join(lines[start_line:end_line + 1])
                    })
        
        return functions
    
    def _extract_function_name(self, line: str) -> str:
        """Extract function name from a line of code."""
        # Simplified function name extraction
        if 'const ' in line and '= function' in line:
            # const myFunction = function() {...}
            start = line.find('const ') + 6
            end = line.find(' =')
            if end > start:
                return line[start:end].strip()
        elif 'function ' in line:
            # function myFunction() {...}
            start = line.find('function ') + 9
            end = line.find('(')
            if end > start:
                return line[start:end].strip()
        
        return 'anonymous'
    
    def _find_function_end(self, lines: list, start_index: int) -> int:
        """Find the end line of a function (simplified brace matching)."""
        brace_count = 0
        started = False
        
        for i in range(start_index, len(lines)):
            line = lines[i]
            
            # Count braces to find function end
            for char in line:
                if char == '{':
                    brace_count += 1
                    started = True
                elif char == '}':
                    brace_count -= 1
                    
                    # Function ends when braces are balanced
                    if started and brace_count == 0:
                        return i
        
        # Fallback: assume function is 10 lines if we can't find the end
        return min(start_index + 10, len(lines) - 1)
    
    def _calculate_comment_density(self, func_info: dict, script_content: str) -> float:
        """
        Calculate comment density for a function.
        
        Returns the ratio of comment lines to total lines within the function.
        """
        func_content = func_info['content']
        lines = func_content.split('\n')
        
        comment_lines = 0
        total_lines = len([line for line in lines if line.strip()])  # Non-empty lines
        
        for line in lines:
            stripped = line.strip()
            # Count single-line comments and multi-line comment lines
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.endswith('*/'):
                comment_lines += 1
        
        return comment_lines / total_lines if total_lines > 0 else 0.0


# Additional example: Structure validation rule using unified architecture
from ...structure.shared import StructureRuleBase
from ...base import Finding
from ....models import PodModel

class CustomPMDSectionValidationRule(StructureRuleBase):
    """
    Example custom PMD structure rule.
    
    Demonstrates validation of PMD file structure and organization.
    """
    
    IS_EXAMPLE = True  # Exclude from discovery
    
    DESCRIPTION = "PMD files should follow organizational structure standards"
    SEVERITY = "WARNING"
    
    def __init__(self, config: dict = None):
        """Initialize with configuration."""
        self.config = config or {}
        self.required_sections = self.config.get('required_sections', ['id', 'presentation'])
        self.max_endpoints = self.config.get('max_endpoints', 10)
    
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
                yield Finding(
                    rule=self,
                    message=f"PMD file is missing required section: '{section}'. "
                           f"This section is required by organizational standards.",
                    line=1,
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
      "severity_override": "WARNING",
      "custom_settings": {
        "min_comment_density": 0.15,
        "min_function_lines": 8
      }
    },
    "CustomPMDSectionValidationRule": {
      "enabled": true,
      "severity_override": "SEVERE",
      "custom_settings": {
        "required_sections": ["id", "presentation", "endPoints"],
        "max_endpoints": 5
      }
    }
  }
}
"""