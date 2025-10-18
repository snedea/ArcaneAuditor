"""Detector for function return consistency analysis."""

from typing import Any, List, Dict, Optional
from ...script.shared import (
    Violation, ScriptDetector, has_control_flow_structures, 
    is_script_expression_with_returns, get_function_body
)


class ReturnAnalysis:
    """Container for return analysis results - focused on facts, not policy."""
    
    def __init__(
        self, 
        has_return: bool = False, 
        all_paths_return: bool = False, 
        is_inconsistent: bool = False, 
        node_type: str = "unknown", 
        violations: Optional[List[Violation]] = None,
        has_unreachable_code: bool = False
    ):
        self.has_return = has_return
        self.all_paths_return = all_paths_return
        self.is_inconsistent = is_inconsistent
        self.node_type = node_type
        self.violations = violations or []
        self.has_unreachable_code = has_unreachable_code


class ReturnConsistencyVisitor:
    """Policy-agnostic visitor for analyzing return consistency in AST nodes."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        self.memo_cache: Dict[int, ReturnAnalysis] = {}
        self.file_path = file_path
        self.line_offset = line_offset
        
        # Method dispatch for performance
        self.visit_methods = {
            'function_expression': self._visit_function_expression,
            'statement_list': self._visit_statement_list,
            'return_statement': self._visit_return_statement,
            'if_statement': self._visit_if_statement,
            'while_statement': self._visit_while_statement,
            'for_statement': self._visit_for_statement,
        }
    
    def visit(self, node: Any) -> ReturnAnalysis:
        """Main entry point for visiting any node."""
        if not hasattr(node, 'data'):
            return ReturnAnalysis()
        
        # Check cache
        node_id = id(node)
        if node_id in self.memo_cache:
            return self.memo_cache[node_id]
        
        # Dispatch to appropriate handler
        visit_method = self.visit_methods.get(node.data, self._visit_default)
        result = visit_method(node)
        
        self.memo_cache[node_id] = result
        return result
    
    def _visit_function_expression(self, node: Any) -> ReturnAnalysis:
        """Analyze function expressions, distinguishing definitions from script expressions."""
        # Skip script expressions (fake functions)
        if is_script_expression_with_returns(node):
            return ReturnAnalysis(node_type="script_expression")
        
        # Analyze function body - each function should be analyzed independently
        function_body = self._extract_function_body(node)
        
        if function_body:
            # Create a new visitor instance for this function to avoid depth conflicts
            nested_visitor = ReturnConsistencyVisitor(self.file_path, self.line_offset)
            analysis = nested_visitor.visit(function_body)
            
            result = ReturnAnalysis(
                has_return=analysis.has_return,
                all_paths_return=analysis.all_paths_return,
                is_inconsistent=analysis.is_inconsistent,
                node_type="function_definition",
                violations=analysis.violations,
                has_unreachable_code=analysis.has_unreachable_code
            )
        else:
            result = ReturnAnalysis(node_type="function_definition")
        
        return result
    
    def _extract_function_body(self, node: Any) -> Optional[Any]:
        """Extract function body from function node."""
        # Try standard extraction first
        body = get_function_body(node)
        if body:
            return body
        
        # Fallback: search for body in children
        if hasattr(node, 'children'):
            for child in node.children:
                if hasattr(child, 'data') and child.data in ['source_elements', 'block_statement']:
                    return child
        
        return None
    
    def _visit_default(self, node: Any) -> ReturnAnalysis:
        """Default visitor for unknown node types."""
        if not hasattr(node, 'children'):
            return ReturnAnalysis()
        return self._analyze_children(node)
    
    def _visit_statement_list(self, node: Any) -> ReturnAnalysis:
        """Analyze statement lists (blocks, function bodies, etc.)."""
        return self._analyze_children(node)
    
    def _visit_return_statement(self, node: Any) -> ReturnAnalysis:
        """Return statements always return."""
        return ReturnAnalysis(
            has_return=True, 
            all_paths_return=True, 
            node_type="return"
        )
    
    def _visit_if_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze if statements for return consistency."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return ReturnAnalysis()
        
        # Find the if block (should be statement_list)
        if_block = self._find_statement_list(node.children)
        if not if_block:
            return self._analyze_children(node)
        
        if_analysis = self.visit(if_block)
        
        # Check for else/else-if blocks
        else_info = self._analyze_else_blocks(node)
        
        if else_info['has_else']:
            return self._handle_if_else(if_analysis, else_info)
        else:
            return self._handle_if_only(if_analysis)
    
    def _find_statement_list(self, children: List[Any]) -> Optional[Any]:
        """Find statement_list in children."""
        for child in children:
            if hasattr(child, 'data') and child.data == 'statement_list':
                return child
        return None
    
    def _analyze_else_blocks(self, node: Any) -> Dict[str, Any]:
        """Analyze else/else-if blocks in an if statement."""
        if len(node.children) < 5:
            return {'has_else': False, 'blocks': [], 'has_final_else': False}
        
        else_block = node.children[4]
        if not hasattr(else_block, 'data'):
            return {'has_else': False, 'blocks': [], 'has_final_else': False}
        
        blocks = [else_block]
        has_final_else = False
        
        if else_block.data in ['statement_list', 'block']:
            has_final_else = True
        elif else_block.data == 'if_statement':
            # Recursively check else-if
            else_if_analysis = self.visit(else_block)
            has_final_else = else_if_analysis.all_paths_return
        
        return {
            'has_else': True,
            'blocks': blocks,
            'has_final_else': has_final_else
        }
    
    def _handle_if_else(self, if_analysis: ReturnAnalysis, else_info: Dict) -> ReturnAnalysis:
        """Handle if-else analysis."""
        # Analyze all else blocks
        else_analyses = [self.visit(block) for block in else_info['blocks']]
        
        # Check for inconsistencies in branches
        if if_analysis.is_inconsistent or any(ea.is_inconsistent for ea in else_analyses):
            has_return = if_analysis.has_return or any(ea.has_return for ea in else_analyses)
            return ReturnAnalysis(
                has_return=has_return,
                all_paths_return=False,
                is_inconsistent=True, 
                node_type="if_else"
            )
        
        # Propagate unreachable code flag
        has_unreachable = if_analysis.has_unreachable_code or any(ea.has_unreachable_code for ea in else_analyses)
        
        # Calculate return characteristics
        all_else_return = any(ea.has_return for ea in else_analyses)
        all_paths_return = False
        is_inconsistent = False
        
        if else_info['has_final_else'] and else_analyses:
            final_else = else_analyses[-1]
            all_paths_return = if_analysis.all_paths_return and final_else.all_paths_return
            
            # Check for inconsistency
            if if_analysis.all_paths_return or final_else.all_paths_return:
                if not (if_analysis.all_paths_return and final_else.all_paths_return):
                    # Only inconsistent if IF returns but ELSE doesn't
                    # If ELSE returns but IF doesn't, that's a guard clause (OK)
                    if if_analysis.all_paths_return and not final_else.all_paths_return:
                        is_inconsistent = True
                    else:
                        is_inconsistent = False
        else:
            # Handle case where there's else-if but no final else
            if else_analyses:
                any_else_returns = any(ea.has_return for ea in else_analyses)
                if if_analysis.has_return or any_else_returns:
                    all_paths_return = False
                    is_inconsistent = False
        
        return ReturnAnalysis(
            has_return=if_analysis.has_return or all_else_return,
            all_paths_return=all_paths_return,
            is_inconsistent=is_inconsistent,
            node_type="if_else",
            has_unreachable_code=has_unreachable
        )
    
    def _handle_if_only(self, if_analysis: ReturnAnalysis) -> ReturnAnalysis:
        """Handle if without else."""
        return ReturnAnalysis(
            has_return=if_analysis.has_return,
            all_paths_return=False,
            is_inconsistent=False,
            node_type="if_no_else"
        )
    
    def _visit_while_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze while loops."""
        return self._analyze_loop(node, "while")
    
    def _visit_for_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze for loops."""
        return self._analyze_loop(node, "for")
    
    def _analyze_loop(self, node: Any, node_type: str) -> ReturnAnalysis:
        """Generic loop analysis."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return ReturnAnalysis(node_type=node_type)
        
        body_analysis = self.visit(node.children[1])
        return ReturnAnalysis(
            has_return=body_analysis.has_return,
            all_paths_return=False,
            is_inconsistent=body_analysis.is_inconsistent,
            node_type=node_type,
            violations=body_analysis.violations
        )
    
    def _analyze_children(self, node: Any) -> ReturnAnalysis:
        """Analyze all children of a node."""
        if not hasattr(node, 'children'):
            return ReturnAnalysis()
        
        state = {
            'has_any_return': False,
            'all_children_return': True,
            'has_inconsistency': False,
            'all_violations': [],
            'has_early_return_pattern': False,
            'has_final_return': False,
            'last_return_index': -1,
            'has_if_else_all_paths_return': False,
            'has_unreachable_code': False
        }
        
        # Analyze all children
        for i, child in enumerate(node.children):
            self._process_child(child, i, state)
        
        # Check if last non-empty child is a return statement
        non_empty_children = [c for c in node.children 
                             if hasattr(c, 'data') and c.data not in ['empty_statement', 'eos']]
        if non_empty_children and non_empty_children[-1].data == 'return_statement':
            state['has_final_return'] = True
        
        # Determine if all paths return
        all_paths_return = self._determine_all_paths_return(node, state)
        
        # Check for unreachable code
        self._check_unreachable_returns(node, state)
        
        return ReturnAnalysis(
            has_return=state['has_any_return'],
            all_paths_return=all_paths_return,
            is_inconsistent=state['has_inconsistency'],
            node_type="children",
            violations=state['all_violations'],
            has_unreachable_code=state.get('has_unreachable_code', False)
        )
    
    def _process_child(self, child: Any, index: int, state: Dict):
        """Process a single child node and update state."""
        child_analysis = self.visit(child)
        
        state['all_violations'].extend(child_analysis.violations)
        
        if child_analysis.is_inconsistent:
            state['has_inconsistency'] = True
        
        if child_analysis.has_return:
            state['has_any_return'] = True
            state['last_return_index'] = index
        
        # Check for early return pattern
        if (hasattr(child, 'data') and child.data == 'if_statement' and 
            child_analysis.has_return and not child_analysis.is_inconsistent):
            state['has_early_return_pattern'] = True
            
            if child_analysis.all_paths_return and child_analysis.node_type == 'if_else':
                state['has_if_else_all_paths_return'] = True
        
        if not child_analysis.all_paths_return:
            state['all_children_return'] = False
    
    def _check_unreachable_returns(self, node: Any, state: Dict):
        """Check for unreachable return statements after if-else."""
        if not state['has_if_else_all_paths_return']:
            return
        
        # Find last if-else that returns on all paths
        last_if_else_index = -1
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'if_statement':
                child_analysis = self.visit(child)
                if child_analysis.all_paths_return:
                    last_if_else_index = i
        
        # Check if there are returns after it
        if last_if_else_index >= 0 and state['last_return_index'] > last_if_else_index:
            state['has_inconsistency'] = True
            state['has_unreachable_code'] = True
    
    def _determine_all_paths_return(self, node: Any, state: Dict) -> bool:
        """Determine if all paths through this node return."""
        # Handle single statement cases
        if hasattr(node, 'children'):
            non_empty_children = [c for c in node.children 
                                 if hasattr(c, 'data') and c.data not in ['empty_statement', 'eos']]
            
            # Single return statement
            if (len(non_empty_children) == 1 and 
                non_empty_children[0].data == 'return_statement'):
                return True
            
            # Single if-else that returns on all paths
            if (len(non_empty_children) == 1 and 
                non_empty_children[0].data == 'if_statement'):
                child_analysis = self.visit(non_empty_children[0])
                if child_analysis.all_paths_return:
                    return True
        
        # If there's an if-else that covers all paths, all paths return
        if state.get('has_if_else_all_paths_return'):
            return True
        
        # Early return pattern + final return = all paths return
        if state['has_early_return_pattern'] and state['has_final_return']:
            return True
        
        # If there's a final return and control flow but no early returns, still valid
        # This handles cases like parseFunction where if statements don't contain returns
        # but all paths eventually lead to the final return
        # Only apply this if there are NO early returns at all AND no inconsistent patterns
        if (state['has_final_return'] and 
            not state['has_early_return_pattern'] and
            not state['has_inconsistency'] and
            state['last_return_index'] >= 0):
            return True
        
        # Check for unreachable code after if-else
        if state['has_if_else_all_paths_return']:
            for i, child in enumerate(node.children):
                if hasattr(child, 'data') and child.data == 'if_statement':
                    child_analysis = self.visit(child)
                    if child_analysis.all_paths_return:
                        for j in range(i + 1, len(node.children)):
                            next_child = node.children[j]
                            if hasattr(next_child, 'data'):
                                if next_child.data == 'return_statement':
                                    state['has_unreachable_code'] = True
                                    state['has_inconsistency'] = True
                                    break
                                elif next_child.data not in ['empty_statement', 'eos']:
                                    break
                        break
        
        return state['all_children_return'] and len(node.children) > 0


class ReturnConsistencyDetector(ScriptDetector):
    """Detector for function return consistency violations."""
    
    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """Detect return consistency violations in the AST."""
        violations = []
        self._check_node(ast, violations, ast)
        return violations
    
    def _check_node(self, node: Any, violations: List[Violation], full_ast: Any):
        """Recursively check nodes for return consistency issues."""
        if hasattr(node, 'data') and node.data == 'function_expression':
            self._analyze_function(node, violations, full_ast)
        
        # Recurse to children
        if hasattr(node, 'children'):
            for child in node.children:
                self._check_node(child, violations, full_ast)
    
    def _analyze_function(self, node: Any, violations: List[Violation], full_ast: Any):
        """Analyze a single function for return consistency."""
        # Extract the function body first
        function_body = self._extract_function_body(node)
        if not function_body:
            return
        
        # Create a visitor that will analyze only the outer function's procedural code
        visitor = ReturnConsistencyVisitor(self.file_path, self.line_offset)
        
        # Analyze only the outer function's procedural code, excluding nested functions
        analysis = self._analyze_outer_function_only(function_body, visitor)
        
        # Apply policy decisions
        function_name = self.get_function_context_for_node(node, full_ast)
        
        # Check for unreachable code FIRST
        if analysis.has_unreachable_code:
            violations.append(self._create_violation(
                function_name,
                "has unreachable return statement - the if-else block above returns on all paths, making code after it unreachable. Remove the unreachable return statement",
                node
            ))
        # Check for "not all code paths return"
        elif (analysis.has_return and 
              not analysis.all_paths_return and 
              has_control_flow_structures(node)):
            violations.append(self._create_violation(
                function_name,
                "has some return statements but not all code paths return - consider adding else branches or a final return statement",
                node
            ))
        # Check for general inconsistency
        elif analysis.is_inconsistent:
            violations.append(self._create_violation(
                function_name,
                "has inconsistent return pattern - some paths return values, others don't",
                node
            ))
    
    def _analyze_outer_function_only(self, function_body: Any, visitor: 'ReturnConsistencyVisitor') -> 'ReturnAnalysis':
        """Analyze only the outer function's procedural code, excluding nested functions."""
        if not hasattr(function_body, 'children'):
            return ReturnAnalysis()
        
        # Collect only the procedural statements, excluding nested function definitions
        procedural_statements = []
        
        for child in function_body.children:
            # Skip nested function definitions
            if hasattr(child, 'data'):
                if child.data in ['function_expression', 'arrow_function', 'function_declaration']:
                    # This is a nested function - skip it for outer function analysis
                    continue
                elif child.data == 'variable_statement':
                    # Check if this variable statement contains a function expression
                    if self._contains_function_expression(child):
                        # This is a nested function declaration - skip it
                        continue
            
            # This is procedural code - include it in analysis
            procedural_statements.append(child)
        
        # If no procedural statements, return empty analysis
        if not procedural_statements:
            return ReturnAnalysis()
        
        # Create a mock AST node with only the procedural statements
        class MockAST:
            def __init__(self, children):
                self.children = children
                self.data = 'source_elements'
        
        mock_ast = MockAST(procedural_statements)
        
        # Analyze only the procedural code
        return visitor.visit(mock_ast)
    
    def _contains_function_expression(self, variable_statement: Any) -> bool:
        """Check if a variable statement contains a function expression."""
        if not hasattr(variable_statement, 'children'):
            return False
        
        for child in variable_statement.children:
            if hasattr(child, 'data') and child.data == 'variable_declaration':
                if hasattr(child, 'children') and len(child.children) >= 2:
                    func_expr = child.children[1]
                    if hasattr(func_expr, 'data') and func_expr.data == 'function_expression':
                        return True
        
        return False
    
    def _extract_function_body(self, node: Any) -> Optional[Any]:
        """Extract function body from function node."""
        # Try standard extraction first
        body = get_function_body(node)
        if body:
            return body
        
        # Fallback: search for body in children
        if hasattr(node, 'children'):
            for child in node.children:
                if hasattr(child, 'data') and child.data in ['source_elements', 'block_statement']:
                    return child
        
        return None
    
    def _create_violation(self, function_name: Optional[str], message_suffix: str, node: Any) -> Violation:
        """Create a violation with appropriate message."""
        if function_name:
            message = f"Function '{function_name}' {message_suffix}"
        else:
            message = f"Function {message_suffix}"
        
        return Violation(
            message=message,
            line=self.get_line_number_from_token(node)
        )