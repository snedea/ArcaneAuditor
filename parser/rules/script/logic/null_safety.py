"""Script null safety rule using unified architecture."""

from typing import Generator, Set, List, Tuple
from ...script.shared import ScriptRuleBase
from ...base import Finding
from ....models import PMDModel
from .null_safety_detector import NullSafetyDetector


class ScriptNullSafetyRule(ScriptRuleBase):
    """Validates that property access chains are properly null-safe."""

    DESCRIPTION = "Ensures property access chains are protected against null reference exceptions"
    SEVERITY = "WARNING"
    DETECTOR = NullSafetyDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _analyze_fields(self, model, script_fields: List[Tuple[str, str, str, int]], context=None) -> Generator[Finding, None, None]:
        """Analyze script fields with cross-field protection awareness."""
        # First pass: collect safe variables from exclude fields
        safe_variables = self._collect_safe_variables_from_exclude_fields(script_fields, context)
        
        # Collect endpoint names from the context
        endpoint_names = self._collect_endpoint_names(context) if context else set()
        
        # Second pass: analyze all fields with collected safe variables and endpoint names
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                ast = self._parse_script_content(field_value, context)
                if ast:
                    # Use detector to find violations with cross-field safe variables and endpoint names
                    detector = self.DETECTOR(model.file_path, line_offset, safe_variables, endpoint_names)
                    violations = detector.detect(ast, field_name)
                    
                    # Convert violations to findings
                    for violation in violations:
                        yield Finding(
                            rule=self,
                            message=violation.message,
                            line=violation.line,
                            file_path=model.file_path
                        )

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector - not used in field-level analysis."""
        # This method is not used when _analyze_fields is overridden
        # Return empty generator to avoid NoneType iteration errors
        yield from []

    def _collect_safe_variables_from_exclude_fields(self, script_fields: List[Tuple[str, str, str, int]], context=None) -> Set[str]:
        """Collect variables that are safe due to empty checks in exclude/render fields."""
        safe_variables = set()
        
        # Group fields by context (endpoints and widgets) to understand cross-field relationships
        context_fields = {}
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                # Extract context name from field path (endpoint or widget)
                context_name = self._extract_context_name(field_path)
                if context_name:
                    if context_name not in context_fields:
                        context_fields[context_name] = []
                    context_fields[context_name].append((field_path, field_value, field_name, line_offset))
        
        # For each context, check if exclude or render fields protect variables used in other fields
        for context_name, fields in context_fields.items():
            # Find exclude and render fields (both provide protection)
            protected_fields = [f for f in fields if 'exclude' in f[2].lower() or 'render' in f[2].lower()]
            
            if protected_fields:
                # Extract safe variables from protected fields
                for field_path, field_value, field_name, line_offset in protected_fields:
                    ast = self._parse_script_content(field_value, context)
                    if ast:
                        safe_vars = self._extract_safe_variables_from_protection_checks(ast)
                        safe_variables.update(safe_vars)
        
        return safe_variables

    def _extract_context_name(self, field_path: str) -> str:
        """Extract context name from field path (endpoint or widget)."""
        # Field paths look like: "inboundEndpoints.2.exclude" or "widgets.0.render"
        parts = field_path.split('.')
        if len(parts) >= 2:
            if parts[0] in ['inboundEndpoints', 'outboundEndpoints']:
                # For endpoints, group by the endpoint index
                return f"{parts[0]}.{parts[1]}"
            elif parts[0] in ['widgets', 'pods']:
                # For widgets/pods, group by the widget index
                return f"{parts[0]}.{parts[1]}"
        return ""

    def _extract_endpoint_name(self, field_path: str) -> str:
        """Extract endpoint name from field path (legacy method)."""
        return self._extract_context_name(field_path)

    def _collect_endpoint_names(self, context) -> Set[str]:
        """Collect all endpoint names from the project context."""
        endpoint_names = set()
        
        if not context or not hasattr(context, 'pmds'):
            return endpoint_names
        
        # Collect endpoint names from all PMD models
        for pmd_model in context.pmds.values():
            # Collect inbound endpoint names
            if pmd_model.inboundEndpoints:
                for endpoint in pmd_model.inboundEndpoints:
                    if isinstance(endpoint, dict) and 'name' in endpoint:
                        endpoint_names.add(endpoint['name'])
            
            # Collect outbound endpoint names
            if pmd_model.outboundEndpoints:
                for endpoint in pmd_model.outboundEndpoints:
                    if isinstance(endpoint, dict) and 'name' in endpoint:
                        endpoint_names.add(endpoint['name'])
        
        # Collect endpoint names from POD models
        if hasattr(context, 'pods'):
            for pod_model in context.pods.values():
                if hasattr(pod_model, 'seed') and hasattr(pod_model.seed, 'endPoints'):
                    for endpoint in pod_model.seed.endPoints:
                        if isinstance(endpoint, dict) and 'name' in endpoint:
                            endpoint_names.add(endpoint['name'])
        
        return endpoint_names

    def _extract_safe_variables_from_protection_checks(self, ast) -> Set[str]:
        """Extract variables that are checked with empty() or render conditions and are therefore safe."""
        safe_variables = set()
        
        # Look for empty expressions (exclude fields)
        for node in ast.iter_subtrees():
            if node.data in ['empty_expression', 'not_empty_expression', 'empty_function_expression']:
                if len(node.children) > 1:
                    # Extract the variable being checked
                    checked_var = self._extract_variable_from_node(node.children[1])
                    if checked_var:
                        safe_variables.add(checked_var)
        
        # Look for render conditions (render fields)
        # Render fields typically contain boolean expressions that protect variables
        for node in ast.iter_subtrees():
            if node.data in ['boolean_expression', 'comparison_expression', 'logical_and_expression', 'logical_or_expression']:
                # Extract variables from boolean expressions in render fields
                render_vars = self._extract_variables_from_boolean_expression(node)
                safe_variables.update(render_vars)
        
        return safe_variables

    def _extract_variables_from_boolean_expression(self, node) -> Set[str]:
        """Extract variables from boolean expressions (used in render fields)."""
        variables = set()
        
        # Recursively traverse the boolean expression
        for child in node.children:
            if hasattr(child, 'data'):
                if child.data == 'identifier_expression':
                    var_name = self._extract_variable_from_node(child)
                    if var_name:
                        variables.add(var_name)
                elif child.data == 'member_dot_expression':
                    var_name = self._extract_variable_from_node(child)
                    if var_name:
                        variables.add(var_name)
                else:
                    # Recursively check child nodes
                    variables.update(self._extract_variables_from_boolean_expression(child))
        
        return variables

    def _extract_variable_from_node(self, node) -> str:
        """Extract variable name from a node."""
        if not hasattr(node, 'data'):
            return ""
            
        if node.data == 'identifier_expression' and len(node.children) > 0:
            return node.children[0].value if hasattr(node.children[0], 'value') else str(node.children[0])
        elif node.data == 'member_dot_expression':
            # Extract property chain
            detector = self.DETECTOR("", 1, set())
            return detector._extract_property_chain(node) or ""
        
        return ""