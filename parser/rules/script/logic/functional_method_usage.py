from typing import Dict, Any
from lark import Tree

from parser.rules.base import Rule, Finding
from parser.models import PMDModel, PodModel


class ScriptFunctionalMethodUsageRule(Rule):
    """Rule to detect manual loops that could be replaced with functional methods."""
    
    DESCRIPTION = "Detects manual loops that could be replaced with functional methods like map, filter, forEach"
    SEVERITY = "WARNING"
    
    def __init__(self, config: Dict[str, Any] = None, context=None):
        # No configuration needed for this rule
        pass
    
    def analyze(self, context):
        """Main entry point - analyze all PMD models, POD models, and standalone script files in the context."""
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
        """Analyzes script fields in a PMD model for manual loop issues."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model, context)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_manual_loops(field_value, field_name, pmd_model.file_path, line_offset, context)
    
    def visit_pod(self, pod_model: PodModel, context=None):
        """Analyzes script fields in a POD model."""
        script_fields = self.find_pod_script_fields(pod_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_manual_loops(field_value, field_name, pod_model.file_path, line_offset, context)

    def _analyze_script_file(self, script_model):
        """Analyze standalone script files for manual loops."""
        try:
            yield from self._check_manual_loops(script_model.source, "script", script_model.file_path, 1, None)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")
    
    def _check_manual_loops(self, script_content, field_name, file_path, line_offset=1, context=None):
        """Check for manual loops that could use functional methods."""
        # Parse the script content using the base class method (handles PMD wrappers)
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all manual for loops in the AST using a single efficient traversal
        yield from self._find_manual_for_loops(ast, field_name, file_path, line_offset)
    
    def _find_manual_for_loops(self, ast: Tree, field_name: str, file_path: str, line_offset: int):
        """Find manual for loops that could use functional methods using efficient AST traversal."""
        # Define manual for loop types (exclude PMD for...in loops)
        manual_for_types = {'for_statement', 'for_let_statement', 'for_var_statement'}
        
        # Use efficient traversal to find all manual for loops
        for for_stmt in ast.find_data('for_statement'):
            if self._is_counter_based_loop(for_stmt):
                yield from self._create_finding(for_stmt, field_name, file_path, line_offset)
        
        for for_stmt in ast.find_data('for_let_statement'):
            if self._is_counter_based_loop(for_stmt):
                yield from self._create_finding(for_stmt, field_name, file_path, line_offset)
        
        for for_stmt in ast.find_data('for_var_statement'):
            if self._is_counter_based_loop(for_stmt):
                yield from self._create_finding(for_stmt, field_name, file_path, line_offset)
    
    def _create_finding(self, for_stmt: Tree, field_name: str, file_path: str, line_offset: int):
        """Create a finding for a detected manual for loop."""
        line_number = self._get_line_number_from_node(for_stmt)
        if line_number:
            line_number = line_offset + line_number - 1
        
        # Analyze the loop to suggest appropriate functional method
        suggestion = self._suggest_functional_method(for_stmt)
        
        yield Finding(
            rule=self,
            message=f"File section '{field_name}' uses manual for loop that could be replaced with functional method. Consider using {suggestion} instead for better readability and maintainability.",
            line=line_number or line_offset,
            column=1,
            file_path=file_path
        )
    
    def _is_counter_based_loop(self, for_stmt: Tree) -> bool:
        """Check if a for loop is a counter-based loop that could use functional methods."""
        if not isinstance(for_stmt, Tree):
            return False
        
        # Extract loop components based on loop type
        loop_components = self._extract_loop_components(for_stmt)
        if not loop_components:
            return False
        
        init, condition, increment = loop_components
        
        # Check if it's a counter-based loop pattern:
        # 1. Initializes a counter variable (let i = 0) OR initializes with array.length (let i = array.length - 1)
        # 2. Compares counter to array length (i < array.length) OR compares to literal (i >= 0 for reverse)
        # 3. Increments/decrements counter (i++, i--, i += n, etc.)
        return (self._is_counter_initialization(init) and
                (self._is_array_length_condition(condition) or self._is_array_length_initialization(init)) and
                self._is_counter_increment(increment))
    
    def _extract_loop_components(self, for_stmt: Tree) -> tuple:
        """Extract initialization, condition, and increment components from a for loop."""
        if not isinstance(for_stmt, Tree) or len(for_stmt.children) < 4:
            return None
        
        # Handle different for loop structures efficiently
        if for_stmt.data == 'for_statement':
            # Traditional for loop: [init, condition, increment, body]
            return (for_stmt.children[0], for_stmt.children[1], for_stmt.children[2])
        elif for_stmt.data in ['for_let_statement', 'for_var_statement']:
            # For with declaration: [for, let/var, init, condition, increment, body]
            if len(for_stmt.children) >= 6:
                return (for_stmt.children[2], for_stmt.children[3], for_stmt.children[4])
        
        return None
    
    def _is_counter_initialization(self, init_node) -> bool:
        """Check if initialization creates a counter variable."""
        if not isinstance(init_node, Tree):
            return False
        
        # Accept variable declarations and assignments
        return init_node.data in {
            'variable_declaration', 
            'variable_statement', 
            'assignment_expression'
        }
    
    def _is_array_length_condition(self, condition_node) -> bool:
        """Check if condition compares counter to array length."""
        if not isinstance(condition_node, Tree):
            return False
        
        # Use efficient AST traversal to find length access
        return self._has_length_access(condition_node)
    
    def _has_length_access(self, node: Tree) -> bool:
        """Efficiently check if a node or its children access .length property."""
        if not isinstance(node, Tree):
            return False
        
        # Direct length access
        if (node.data == 'member_dot_expression' and 
            len(node.children) >= 2 and 
            hasattr(node.children[1], 'value') and 
            node.children[1].value == 'length'):
            return True
        
        # Check children recursively
        for child in node.children:
            if isinstance(child, Tree) and self._has_length_access(child):
                return True
        
        return False
    
    def _is_array_length_initialization(self, init_node) -> bool:
        """Check if initialization involves array.length (e.g., let i = array.length - 1)."""
        if not isinstance(init_node, Tree):
            return False
        
        # For variable declarations, check the initializer
        if init_node.data in ['variable_declaration', 'variable_statement']:
            if len(init_node.children) >= 2:
                initializer = init_node.children[1]
                return self._has_length_access(initializer)
        
        # For assignment expressions, check the right-hand side
        if init_node.data == 'assignment_expression':
            if len(init_node.children) >= 2:
                rhs = init_node.children[1]
                return self._has_length_access(rhs)
        
        return False
    
    def _is_counter_increment(self, increment_node) -> bool:
        """Check if increment modifies a counter variable."""
        if not isinstance(increment_node, Tree):
            return False
        
        # Define all valid increment/decrement patterns
        increment_types = {
            'unary_expression',           # i++
            'post_increment_expression',  # i++
            'pre_increment_expression',   # ++i
            'post_decrease_expression',   # i--
            'pre_decrease_expression',    # --i
            'assignment_expression',      # i = i + 1
            'assignment_operator_expression'  # i += n
        }
        
        return increment_node.data in increment_types
    
    def _suggest_functional_method(self, for_stmt: Tree) -> str:
        """Suggest an appropriate functional method based on loop body analysis."""
        # Extract loop body efficiently
        loop_components = self._extract_loop_components(for_stmt)
        if not loop_components or len(for_stmt.children) <= 3:
            return "functional methods like map(), filter(), or forEach()"
        
        # Get the body (last component)
        body_index = 3 if for_stmt.data == 'for_statement' else 5
        if len(for_stmt.children) <= body_index:
            return "functional methods like map(), filter(), or forEach()"
        
        loop_body = for_stmt.children[body_index]
        
        # Analyze loop body patterns efficiently
        patterns = self._analyze_loop_patterns(loop_body)
        
        if patterns['has_array_push']:
            if patterns['has_conditional']:
                return "filter()"
            else:
                return "map()"
        elif patterns['has_side_effects']:
            return "forEach()"
        elif patterns['has_accumulation']:
            return "reduce()"
        
        return "functional methods like map(), filter(), or forEach()"
    
    def _analyze_loop_patterns(self, loop_body: Tree) -> Dict[str, bool]:
        """Efficiently analyze loop body to identify functional patterns."""
        patterns = {
            'has_array_push': False,
            'has_conditional': False,
            'has_side_effects': False,
            'has_accumulation': False
        }
        
        if not isinstance(loop_body, Tree):
            return patterns
        
        # Use efficient single-pass traversal
        self._traverse_loop_body(loop_body, patterns)
        return patterns
    
    def _traverse_loop_body(self, node: Tree, patterns: Dict[str, bool]):
        """Efficient single-pass traversal to identify loop patterns."""
        if not isinstance(node, Tree):
            return
        
        # Check for key patterns
        if node.data == 'call_expression':
            if self._is_array_push_call(node):
                patterns['has_array_push'] = True
            elif self._is_side_effect_call(node):
                patterns['has_side_effects'] = True
        elif node.data == 'if_statement':
            patterns['has_conditional'] = True
        elif node.data == 'assignment_expression':
            patterns['has_accumulation'] = True
        
        # Traverse children
        for child in node.children:
            if isinstance(child, Tree):
                self._traverse_loop_body(child, patterns)
    
    def _is_array_push_call(self, call_node: Tree) -> bool:
        """Check if call is an array push operation."""
        if (len(call_node.children) > 0 and 
            isinstance(call_node.children[0], Tree) and 
            call_node.children[0].data == 'member_dot_expression'):
            
            member_expr = call_node.children[0]
            return (len(member_expr.children) >= 2 and 
                    hasattr(member_expr.children[1], 'value') and 
                    member_expr.children[1].value == 'push')
        
        return False
    
    def _is_side_effect_call(self, call_node: Tree) -> bool:
        """Check if call is a side effect operation (console.log, etc.)."""
        if (len(call_node.children) > 0 and 
            isinstance(call_node.children[0], Tree) and 
            call_node.children[0].data == 'member_dot_expression'):
            
            member_expr = call_node.children[0]
            return (len(member_expr.children) >= 2 and 
                    hasattr(member_expr.children[1], 'value') and 
                    member_expr.children[1].value in ['log', 'info', 'warn', 'error'])
        
        return False
    
    def _get_line_number_from_node(self, node: Tree) -> int:
        """Get the line number from an AST node."""
        if hasattr(node, 'meta') and hasattr(node.meta, 'line'):
            return node.meta.line
        elif hasattr(node, 'line'):
            return node.line
        elif hasattr(node, 'children') and len(node.children) > 0:
            # Try to get line from first child
            child = node.children[0]
            if hasattr(child, 'meta') and hasattr(child.meta, 'line'):
                return child.meta.line
            elif hasattr(child, 'line'):
                return child.line
        return 1  # Default fallback