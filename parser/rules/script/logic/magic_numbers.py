from ...base import Rule, Finding
from ....models import PMDModel, PodModel


class ScriptMagicNumberRule(Rule):
    """Validates that scripts don't contain magic numbers."""
    
    DESCRIPTION = "Ensures scripts don't contain magic numbers (use named constants)"
    SEVERITY = "INFO"

    def analyze(self, context):
        """Main entry point - analyze all PMD models and standalone script files in the context."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model, context)
        
        # Analyze POD embedded scripts
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model, context)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)

    def visit_pmd(self, pmd_model: PMDModel, context=None):
        """Analyzes script fields in a PMD model."""
        script_fields = self.find_script_fields(pmd_model, context)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_magic_numbers(field_value, field_name, pmd_model.file_path, line_offset, context)

    def visit_pod(self, pod_model: PodModel, context=None):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_magic_numbers(field_value, field_name, pod_model.file_path, line_offset, context)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for magic numbers."""
        try:
            yield from self._check_magic_numbers(script_model.source, "script", script_model.file_path, 1, None)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

    def _check_magic_numbers(self, script_content, field_name, file_path, line_offset=1, context=None):
        """Check for magic numbers in script content using AST analysis."""
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Define allowed numbers and contexts
        allowed_numbers = {0, 1, -1}  # Common legitimate numbers
        # We want to flag magic numbers regardless of their parent context
        
        findings = []
        
        def visit_node(node, parent=None):
            """Recursively visit AST nodes to find magic numbers."""
            # Check if the current node is a numeric literal
            if hasattr(node, 'data') and node.data == 'literal_expression':
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    try:
                        # Try to parse the value as a number
                        value = node.children[0].value
                        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                            number = int(value)
                            
                            # Check if this is a magic number
                            is_magic = number not in allowed_numbers
                            
                            if is_magic:
                                # Get line number from the token inside the literal_expression
                                relative_line = getattr(node.children[0], 'line', 1) or 1
                                line_number = line_offset + relative_line - 1
                                
                                findings.append(Finding(
                                    rule=self,
                                    message=f"File section '{field_name}' contains magic number '{number}'. Consider using a named constant instead.",
                                    line=line_number,
                                    column=1,
                                    file_path=file_path
                                ))
                    except (ValueError, AttributeError):
                        # Not a number, skip
                        pass
            
            # Recurse into children
            if hasattr(node, 'children'):
                for child in node.children:
                    visit_node(child, parent=node)
        
        # Start the traversal from the root of the AST
        visit_node(ast)
        
        # Yield all findings
        for finding in findings:
            yield finding
