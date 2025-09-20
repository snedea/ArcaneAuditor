"""
Example Custom Rule - Custom Script Comment Quality Rule

This is an example of how to create a custom validation rule using the modern
Arcane Auditor architecture (2025). It demonstrates:

- Generator-based analysis pattern
- Dual script analysis (PMD embedded + standalone script files)  
- Modern Finding creation with automatic field population
- Proper error handling and AST parsing
- Configuration support through custom_settings
"""

from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, ScriptModel


class CustomScriptCommentQualityRule(Rule):
    """
    Example custom rule that checks for minimum comment density in script functions.
    
    This rule demonstrates the modern Arcane Auditor rule architecture:
    - Generator-based analysis (yields findings instead of returning lists)
    - Dual script analysis (PMD embedded scripts + standalone .script files)
    - Modern Finding creation with automatic field population
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
        Modern analysis pattern: Generator-based with dual script analysis.
        
        Analyzes both:
        1. PMD embedded scripts (onLoad, script, onSubmit, etc.)
        2. Standalone script files (util.script, helper.script, etc.)
        """
        
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_scripts(pmd_model)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)
    
    def _analyze_pmd_scripts(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze script content within PMD files using automatic field discovery."""
        # Use built-in script field discovery
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_comment_quality(field_value, field_name, pmd_model.file_path, line_offset)
    
    def _analyze_script_file(self, script_model: ScriptModel) -> Generator[Finding, None, None]:
        """Analyze standalone script files with proper error handling."""
        try:
            yield from self._check_comment_quality(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")
    
    def _check_comment_quality(self, script_content: str, field_name: str, file_path: str, line_offset: int) -> Generator[Finding, None, None]:
        """
        Check comment quality in script content using AST parsing.
        
        This demonstrates:
        - Using built-in script parser
        - AST traversal for function detection
        - Comment density calculation
        - Modern Finding creation
        """
        try:
            # Parse script using built-in Lark grammar parser
            ast = self._parse_script_content(script_content)
            
            # Find all function definitions in the AST
            functions = self._find_functions_in_ast(ast, script_content)
            
            for func_info in functions:
                comment_density = self._calculate_comment_density(func_info, script_content)
                
                # Only check functions that meet minimum line threshold
                if func_info['line_count'] >= self.min_function_lines and comment_density < self.min_comment_density:
                    yield Finding(
                        rule=self,  # Automatically populates rule_id, severity, description
                        message=f"Function '{func_info['name']}' has low comment density "
                               f"({comment_density:.1%}, minimum: {self.min_comment_density:.1%}). "
                               f"Consider adding comments to improve code maintainability.",
                        line=line_offset + func_info['start_line'],
                        column=1,
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


# Additional example: Structure validation rule
class CustomPMDSectionValidationRule(Rule):
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
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD structure compliance."""
        for pmd_model in context.pmds.values():
            yield from self._validate_pmd_structure(pmd_model)
    
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
                    column=1,
                    file_path=pmd_model.file_path
                )
        
        # Check endpoint count
        if pmd_model.endpoints and len(pmd_model.endpoints) > self.max_endpoints:
            yield Finding(
                rule=self,
                message=f"PMD has too many endpoints ({len(pmd_model.endpoints)} > {self.max_endpoints}). "
                       f"Consider splitting into multiple PMD files for better maintainability.",
                line=1,
                column=1,
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
      "severity_override": "ERROR",
      "custom_settings": {
        "required_sections": ["id", "presentation", "endPoints"],
        "max_endpoints": 5
      }
    }
  }
}
"""