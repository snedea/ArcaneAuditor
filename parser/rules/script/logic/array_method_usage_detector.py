"""Array method usage detection logic for ScriptArrayMethodUsageRule."""

from typing import Generator, Dict, Any
from lark import Tree
from ...script.shared import ScriptDetector
from ...common import Violation


class ArrayMethodUsageDetector(ScriptDetector):
    """Detects manual loops that could be replaced with array higher-order methods."""

    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)

    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect manual for loops that could use array higher-order methods."""
        if ast is None:
            return
        yield from self._find_manual_for_loops(ast, field_name)

    def _find_manual_for_loops(self, ast: Tree, field_name: str):
        """Find manual for loops that could use array higher-order methods using efficient AST traversal."""
        # Define manual for loop types (exclude PMD for...in loops)
        manual_for_types = {'for_statement', 'for_let_statement', 'for_var_statement'}
        
        # Use efficient traversal to find all manual for loops
        for for_stmt in ast.find_data('for_statement'):
            if self._is_counter_based_loop(for_stmt):
                yield from self._create_violation(for_stmt, field_name, ast)
        
        for for_stmt in ast.find_data('for_let_statement'):
            if self._is_counter_based_loop(for_stmt):
                yield from self._create_violation(for_stmt, field_name, ast)
        
        for for_stmt in ast.find_data('for_var_statement'):
            if self._is_counter_based_loop(for_stmt):
                yield from self._create_violation(for_stmt, field_name, ast)

    def _create_violation(self, for_stmt: Tree, field_name: str, ast: Tree):
        """Create a violation for a detected manual for loop."""
        # Get line number from the first token in the for statement
        line_number = self.get_line_from_tree_node(for_stmt)
        
        # Analyze the loop to suggest appropriate array higher-order method
        suggestion = self._suggest_array_method(for_stmt)
        
        # Check if this manual for loop is inside a function
        function_name = self.get_function_context_for_node(for_stmt, ast)
        
        if function_name:
            message = f"File section '{field_name}' uses manual for loop in function '{function_name}' that could be replaced with array higher-order method. Consider using {suggestion} instead for better readability and maintainability."
        else:
            message = f"File section '{field_name}' uses manual for loop that could be replaced with array higher-order method. Consider using {suggestion} instead for better readability and maintainability."
        
        yield Violation(
            message=message,
            line=line_number
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

    def _suggest_array_method(self, for_stmt: Tree) -> str:
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
