from ...base import Rule, Finding
from ....models import PMDModel, PodModel


class ScriptComplexityRule(Rule):
    """Validates that scripts don't exceed complexity thresholds."""
    
    DESCRIPTION = "Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)"
    SEVERITY = "WARNING"

    def analyze(self, context):
        """Main entry point - analyze all PMD models and standalone script files in the context."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)

    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_complexity(field_value, field_name, pmd_model.file_path, line_offset)

    def visit_pod(self, pod_model: PodModel):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_complexity(field_value, field_name, pod_model.file_path, line_offset)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for cyclomatic complexity."""
        try:
            yield from self._check_complexity(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _check_complexity(self, script_content, field_name, file_path, line_offset=1):
        """Check for excessive complexity in script content using Lark grammar."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        max_complexity = 10
        
        # Analyze complexity using AST
        complexity_info = self._analyze_ast_complexity(ast)
        complexity = complexity_info['complexity']
        line = complexity_info.get('line', 1)
        
        if complexity > max_complexity:
            # Use line_offset as base, add relative line if available
            relative_line = complexity_info.get('line', 1) or 1
            line_number = line_offset + relative_line - 1
            
            yield Finding(
                rule=self,
                message=f"File section '{field_name}' has complexity of {complexity} (max recommended: {max_complexity}). Consider refactoring.",
                line=line_number,
                column=1,
                file_path=file_path
            )
    
    def _analyze_ast_complexity(self, node):
        """Analyze cyclomatic complexity in AST nodes."""
        complexity = 1  # Base complexity
        line = None
        
        if hasattr(node, 'data'):
            # Count complexity-increasing constructs
            if node.data in ['if_statement', 'while_statement', 'for_statement', 'do_statement']:
                complexity += 1
                # Get line number from the first token in the node
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'logical_and_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'logical_or_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
            
            elif node.data == 'ternary_expression':
                complexity += 1
                if hasattr(node, 'children') and len(node.children) > 0:
                    for child in node.children:
                        if hasattr(child, 'line') and child.line is not None:
                            line = child.line
                            break
        
        # Recursively analyze children
        if hasattr(node, 'children'):
            for child in node.children:
                child_complexity = self._analyze_ast_complexity(child)
                complexity += child_complexity['complexity'] - 1  # Subtract 1 to avoid double-counting base complexity
                if child_complexity.get('line') and not line:
                    line = child_complexity['line']
        
        return {
            'complexity': complexity,
            'line': line
        }
