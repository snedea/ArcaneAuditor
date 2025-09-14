from typing import List, Dict, Any, Generator
from lark import Tree

from parser.rules.base import Rule, Finding
from parser.models import PMDModel


class ScriptFunctionalMethodUsageRule(Rule):
    """Rule to detect manual loops that could be replaced with functional methods."""
    
    ID = "SCRIPT019"
    DESCRIPTION = "Detects manual loops that could be replaced with functional methods like map, filter, forEach"
    SEVERITY = "WARNING"
    
    def __init__(self, config: Dict[str, Any] = None):
        # No configuration needed for this rule
        pass
    
    def analyze(self, context):
        """Main entry point - analyze all PMD models in the context."""
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Analyzes script fields in a PMD model for manual loop issues."""
        # Use the generic script field finder to detect all fields containing <% %> patterns
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_manual_loops(field_value, field_name, pmd_model.file_path, line_offset)
    
    def _check_manual_loops(self, script_content, field_name, file_path, line_offset=1):
        """Check for manual loops that could use functional methods."""
        # Parse the script content using the base class method (handles PMD wrappers)
        ast = self._parse_script_content(script_content)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Find all for loops in the AST
        yield from self._find_manual_for_loops(ast, field_name, file_path, line_offset)
    
    def _find_manual_for_loops(self, ast: Tree, field_name: str, file_path: str, line_offset: int):
        """Find manual for loops that could use functional methods."""
        # Find all manual for loop types (not PMD for...in loops)
        for_loop_types = ['for_statement', 'for_let_statement', 'for_var_statement']
        
        for loop_type in for_loop_types:
            for_statements = ast.find_data(loop_type)
            
            for for_stmt in for_statements:
                if self._is_manual_for_loop(for_stmt):
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
    
    def _is_manual_for_loop(self, for_stmt: Tree) -> bool:
        """Check if a for loop is a manual loop that could use functional methods."""
        if not isinstance(for_stmt, Tree):
            return False
        
        # Check if it's a manual for loop type (not PMD for...in loops)
        manual_for_types = ['for_statement', 'for_let_statement', 'for_var_statement']
        if for_stmt.data not in manual_for_types:
            return False
        
        # Handle different for loop types with different structures
        if for_stmt.data == 'for_statement':
            # Traditional for loop: [init, condition, increment, body]
            if len(for_stmt.children) < 4:
                return False
            for_init = for_stmt.children[0]
            for_condition = for_stmt.children[1] 
            for_increment = for_stmt.children[2]
        elif for_stmt.data in ['for_let_statement', 'for_var_statement']:
            # For with declaration: [for, let/var, init, condition, increment, body]
            if len(for_stmt.children) < 6:
                return False
            for_init = for_stmt.children[2]
            for_condition = for_stmt.children[3]
            for_increment = for_stmt.children[4]
        else:
            return False
        
        # Check if it's a manual loop pattern:
        # for(let i = 0; i < array.length; i++) { ... }
        return (self._is_counter_initialization(for_init) and
                self._is_length_condition(for_condition) and
                self._is_counter_increment(for_increment))
    
    def _is_counter_initialization(self, init_node) -> bool:
        """Check if initialization is a counter variable (let i = 0)."""
        if not isinstance(init_node, Tree):
            return False
        
        # Look for variable assignment like "let i = 0" or "var i = 0"
        if init_node.data in ['variable_declaration', 'variable_statement']:
            return True
        
        # Look for assignment expression like "i = 0"
        if init_node.data == 'assignment_expression':
            return True
        
        return False
    
    def _is_length_condition(self, condition_node) -> bool:
        """Check if condition is array.length comparison."""
        if not isinstance(condition_node, Tree):
            return False
        
        # Look for binary expressions like "i < array.length"
        if condition_node.data == 'relational_expression':
            return True
        
        # Look for member expressions that access .length
        if condition_node.data == 'member_dot_expression':
            return True
        
        # Recursively check child nodes for length access
        for child in condition_node.children:
            if isinstance(child, Tree) and self._is_length_condition(child):
                return True
        
        return False
    
    def _is_counter_increment(self, increment_node) -> bool:
        """Check if increment is a counter increment (i++ or i += 1)."""
        if not isinstance(increment_node, Tree):
            return False
        
        # Look for unary increment (i++)
        if increment_node.data == 'unary_expression':
            return True
        
        # Look for post increment (i++)
        if increment_node.data == 'post_increment_expression':
            return True
        
        # Look for pre increment (++i)
        if increment_node.data == 'pre_increment_expression':
            return True
        
        # Look for assignment increment (i += 1)
        if increment_node.data == 'assignment_expression':
            return True
        
        # Look for assignment operator increment (i += 2)
        if increment_node.data == 'assignment_operator_expression':
            return True
        
        # Look for post decrement (i--)
        if increment_node.data == 'post_decrease_expression':
            return True
        
        # Look for pre decrement (--i)
        if increment_node.data == 'pre_decrease_expression':
            return True
        
        return False
    
    def _suggest_functional_method(self, for_stmt: Tree) -> str:
        """Suggest an appropriate functional method based on loop analysis."""
        # Analyze the loop body to determine the best suggestion
        if len(for_stmt.children) > 3:
            loop_body = for_stmt.children[3]
            analysis = self._analyze_loop_body(loop_body)
            
            if analysis['is_mapping']:
                return "map()"
            elif analysis['is_filtering']:
                return "filter()"
            elif analysis['is_side_effect']:
                return "forEach()"
            elif analysis['is_reducing']:
                return "reduce()"
        
        # Default suggestion
        return "functional methods like map(), filter(), or forEach()"
    
    def _analyze_loop_body(self, loop_body: Tree) -> Dict[str, bool]:
        """Analyze the loop body to determine what type of operation it performs."""
        analysis = {
            'is_mapping': False,
            'is_filtering': False,
            'is_side_effect': False,
            'is_reducing': False
        }
        
        if not isinstance(loop_body, Tree):
            return analysis
        
        # Look for common patterns in the loop body
        self._traverse_for_patterns(loop_body, analysis)
        
        return analysis
    
    def _traverse_for_patterns(self, node: Tree, analysis: Dict[str, bool]):
        """Traverse AST nodes to identify loop patterns."""
        if not isinstance(node, Tree):
            return
        
        # Check for push operations (mapping or filtering)
        if node.data == 'call_expression':
            if self._is_array_push(node):
                analysis['is_mapping'] = True
            elif self._is_console_log(node):
                analysis['is_side_effect'] = True
        
        # Check for if statements (filtering)
        if node.data == 'if_statement':
            analysis['is_filtering'] = True
        
        # Check for assignment operations (reducing or mapping)
        if node.data == 'assignment_expression':
            analysis['is_reducing'] = True
        
        # Recursively check children
        for child in node.children:
            if isinstance(child, Tree):
                self._traverse_for_patterns(child, analysis)
    
    def _is_array_push(self, call_node: Tree) -> bool:
        """Check if a call expression is an array push operation."""
        if not isinstance(call_node, Tree) or call_node.data != 'call_expression':
            return False
        
        # Look for .push() method calls
        if len(call_node.children) > 0:
            member_expr = call_node.children[0]
            if isinstance(member_expr, Tree) and member_expr.data == 'member_dot_expression':
                if len(member_expr.children) > 1:
                    method_node = member_expr.children[1]
                    if hasattr(method_node, 'value') and method_node.value == 'push':
                        return True
        
        return False
    
    def _is_console_log(self, call_node: Tree) -> bool:
        """Check if a call expression is a console.log operation."""
        if not isinstance(call_node, Tree) or call_node.data != 'call_expression':
            return False
        
        # Look for console.log() method calls
        if len(call_node.children) > 0:
            member_expr = call_node.children[0]
            if isinstance(member_expr, Tree) and member_expr.data == 'member_dot_expression':
                if len(member_expr.children) > 1:
                    method_node = member_expr.children[1]
                    if hasattr(method_node, 'value') and method_node.value in ['log', 'info', 'warn', 'error']:
                        return True
        
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
