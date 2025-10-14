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
        # 1. Initializes a counter variable (let i = 0) OR initializes with array.size() (let i = array.size() - 1)
        # 2. Compares counter to array size (i < array.size()) OR compares to literal (i >= 0 for reverse)
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
        """Check if condition compares counter to array size."""
        if not isinstance(condition_node, Tree):
            return False
        
        # Use efficient AST traversal to find .size() access
        return self._has_length_access(condition_node)

    def _has_length_access(self, node: Tree) -> bool:
        """Efficiently check if a node or its children access .size() method (PMD Script)."""
        if not isinstance(node, Tree):
            return False
        
        # Check for .size() method call (PMD Script lists use this)
        if node.data == 'arguments_expression':
            # Check if this is a call to .size()
            if len(node.children) >= 1:
                function_node = node.children[0]
                if (isinstance(function_node, Tree) and 
                    function_node.data == 'member_dot_expression' and
                    len(function_node.children) >= 2 and
                    hasattr(function_node.children[1], 'value') and
                    function_node.children[1].value == 'size'):
                    return True
        
        # Check children recursively
        for child in node.children:
            if isinstance(child, Tree) and self._has_length_access(child):
                return True
        
        return False

    def _is_array_length_initialization(self, init_node) -> bool:
        """Check if initialization involves array.size() (e.g., let i = array.size() - 1)."""
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
        elif patterns['has_mutation']:
            return "map()"
        
        return "functional methods like map(), filter(), or forEach()"

    def _analyze_loop_patterns(self, loop_body: Tree) -> Dict[str, bool]:
        """Efficiently analyze loop body to identify functional patterns."""
        patterns = {
            'has_array_push': False,
            'has_conditional': False,
            'has_side_effects': False,
            'has_accumulation': False,
            'has_mutation': False
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
            # Distinguish between accumulation and mutation
            if self._is_accumulation_assignment(node):
                patterns['has_accumulation'] = True
            elif self._is_mutation_assignment(node):
                patterns['has_mutation'] = True
        
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
        """Check if call is a side effect operation (console.debug, etc.)."""
        if (len(call_node.children) > 0 and 
            isinstance(call_node.children[0], Tree) and 
            call_node.children[0].data == 'member_dot_expression'):
            
            member_expr = call_node.children[0]
            return (len(member_expr.children) >= 2 and 
                    hasattr(member_expr.children[1], 'value') and 
                    member_expr.children[1].value in ['debug', 'info', 'warn', 'error'])
        
        return False
    
    def _is_accumulation_assignment(self, assignment_node: Tree) -> bool:
        """Check if assignment is accumulation (result += array[i] or result = result + array[i])."""
        if not isinstance(assignment_node, Tree) or len(assignment_node.children) < 2:
            return False
        
        # Check for compound assignment operators (+=, -=, *=, etc.)
        if assignment_node.data == 'assignment_operator_expression':
            return True
        
        # Check for regular assignment where right side contains the left variable
        # e.g., result = result + array[i]
        left_var = assignment_node.children[0]
        right_expr = assignment_node.children[1]
        
        if not isinstance(left_var, Tree) or not isinstance(right_expr, Tree):
            return False
        
        # Check if right expression contains the left variable (accumulation pattern)
        return self._contains_variable_reference(right_expr, left_var)
    
    def _is_mutation_assignment(self, assignment_node: Tree) -> bool:
        """Check if assignment is array mutation (array[i] = value)."""
        if not isinstance(assignment_node, Tree) or len(assignment_node.children) < 2:
            return False
        
        left_side = assignment_node.children[0]
        
        # Check if left side is array access (array[index])
        return self._is_array_access(left_side)
    
    def _contains_variable_reference(self, node: Tree, target_var: Tree) -> bool:
        """Check if node contains a reference to the target variable."""
        if not isinstance(node, Tree):
            return False
        
        # Check if this node is the same variable
        if node.data == target_var.data:
            # Compare variable names if available
            if (len(node.children) > 0 and len(target_var.children) > 0 and
                hasattr(node.children[0], 'value') and hasattr(target_var.children[0], 'value')):
                return node.children[0].value == target_var.children[0].value
        
        # Check children recursively
        for child in node.children:
            if isinstance(child, Tree) and self._contains_variable_reference(child, target_var):
                return True
        
        return False
    
    def _is_array_access(self, node: Tree) -> bool:
        """Check if node represents array access (array[index])."""
        if not isinstance(node, Tree):
            return False
        
        # Check for bracket notation: array[index] (PMD Script uses member_index_expression)
        if node.data in ['bracket_expression', 'member_index_expression']:
            return True
        
        # Check for dot notation with numeric access (less common but possible)
        if (node.data == 'member_dot_expression' and 
            len(node.children) >= 2 and
            hasattr(node.children[1], 'value')):
            # Check if it's a numeric property (array.0, array.1, etc.)
            try:
                int(node.children[1].value)
                return True
            except ValueError:
                pass
        
        return False
