"""
Script validation rules - catches script quality violations that code reviewers should catch.

These are issues that compilers can't detect but violate code quality guidelines and best practices.
Examples: use of var vs let/const, nested block levels, code complexity metrics.

Note: Basic script validation (syntax errors, etc.) is handled by the compiler.
This tool focuses on script quality and best practices for code reviewers.
"""
from .base import Rule, Finding
from ..models import PMDModel
import re


class ScriptVarUsageRule(Rule):
    """Validates that scripts use 'let' or 'const' instead of 'var'."""
    
    ID = "SCRIPT001"
    DESCRIPTION = "Ensures scripts use 'let' or 'const' instead of 'var' (best practice)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        if not pmd_model.presentation:
            return

        # Check common script fields
        script_fields = ['onLoad', 'onSend', 'onReceive', 'onError', 'onClick', 'onChange']
        
        for field_name in script_fields:
            if hasattr(pmd_model.presentation, field_name):
                field_value = getattr(pmd_model.presentation, field_name)
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_var_usage(field_value, field_name, pmd_model.file_path)

    def _check_var_usage(self, script_content, field_name, file_path):
        """Check for use of 'var' in script content."""
        # Look for 'var' declarations (not in strings or comments)
        var_pattern = r'\bvar\s+\w+'
        matches = re.finditer(var_pattern, script_content)
        
        for match in matches:
            line_number = self._get_line_number_from_content(script_content, match.start())
            
            yield Finding(
                rule=self,
                message=f"Script field '{field_name}' uses 'var' declaration. Consider using 'let' or 'const' instead.",
                line=line_number,
                column=1,
                file_path=file_path
            )

    def _get_line_number_from_content(self, content, position):
        """Get approximate line number from content position."""
        return content[:position].count('\n') + 1


class ScriptNestingLevelRule(Rule):
    """Validates that scripts don't have excessive nesting levels."""
    
    ID = "SCRIPT002"
    DESCRIPTION = "Ensures scripts don't have excessive nesting levels (max 4 levels)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        if not pmd_model.presentation:
            return

        # Check common script fields
        script_fields = ['onLoad', 'onSend', 'onReceive', 'onError', 'onClick', 'onChange']
        
        for field_name in script_fields:
            if hasattr(pmd_model.presentation, field_name):
                field_value = getattr(pmd_model.presentation, field_name)
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_nesting_level(field_value, field_name, pmd_model.file_path)

    def _check_nesting_level(self, script_content, field_name, file_path):
        """Check for excessive nesting levels in script content."""
        max_nesting = 4
        current_nesting = 0
        max_nesting_found = 0
        
        for char in script_content:
            if char in '{([{':
                current_nesting += 1
                max_nesting_found = max(max_nesting_found, current_nesting)
            elif char in '})]}':
                current_nesting = max(0, current_nesting - 1)
        
        if max_nesting_found > max_nesting:
            yield Finding(
                rule=self,
                message=f"Script field '{field_name}' has {max_nesting_found} nesting levels (max recommended: {max_nesting}). Consider refactoring.",
                line=1,  # Could be enhanced with more precise line tracking
                column=1,
                file_path=file_path
            )


class ScriptComplexityRule(Rule):
    """Validates that scripts don't exceed complexity thresholds."""
    
    ID = "SCRIPT003"
    DESCRIPTION = "Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        if not pmd_model.presentation:
            return

        # Check common script fields
        script_fields = ['onLoad', 'onSend', 'onReceive', 'onError', 'onClick', 'onChange']
        
        for field_name in script_fields:
            if hasattr(pmd_model.presentation, field_name):
                field_value = getattr(pmd_model.presentation, field_name)
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_complexity(field_value, field_name, pmd_model.file_path)

    def _check_complexity(self, script_content, field_name, file_path):
        """Check for excessive complexity in script content."""
        # Simple cyclomatic complexity calculation
        complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch', '&&', '||', '?']
        complexity = 1  # Base complexity
        
        for keyword in complexity_keywords:
            # Count occurrences of complexity-increasing keywords
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, script_content, re.IGNORECASE)
            complexity += len(matches)
        
        max_complexity = 10
        
        if complexity > max_complexity:
            yield Finding(
                rule=self,
                message=f"Script field '{field_name}' has complexity of {complexity} (max recommended: {max_complexity}). Consider refactoring.",
                line=1,  # Could be enhanced with more precise line tracking
                column=1,
                file_path=file_path
            )
