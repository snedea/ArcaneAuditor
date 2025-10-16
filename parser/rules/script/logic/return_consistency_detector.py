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
        has_unreachable_code: bool = False  # Track if we found unreachable returns
    ):
        self.has_return = has_return
        self.all_paths_return = all_paths_return
        self.is_inconsistent = is_inconsistent
        self.node_type = node_type
        self.violations = violations or []
        self.has_unreachable_code = has_unreachable_code
    
    def __repr__(self):
        violation_preview = ""
        if self.violations:
            msg = self.violations[0].message
            violation_preview = f", first_violation='{msg[:50]}...'"
        
        return (
            f"ReturnAnalysis("
            f"has_return={self.has_return}, "
            f"all_paths_return={self.all_paths_return}, "
            f"is_inconsistent={self.is_inconsistent}, "
            f"node_type='{self.node_type}', "
            f"violations={len(self.violations)}"
            f"{violation_preview})"
        )


class ReturnConsistencyVisitor:
    """Policy-agnostic visitor for analyzing return consistency in AST nodes."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        self.memo_cache: Dict[int, ReturnAnalysis] = {}
        self.file_path = file_path
        self.line_offset = line_offset
        self.function_depth = 0
        
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
        
        self.function_depth += 1
        
        # Skip nested functions (implementation details)
        if self.function_depth > 1:
            self.function_depth -= 1
            return ReturnAnalysis(node_type="inline_function")
        
        # Analyze function body
        function_body = self._extract_function_body(node)
        
        if function_body:
            analysis = self.visit(function_body)
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
        
        self.function_depth -= 1
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
        
        # Check for inconsistencies or unreachable code in branches
        if if_analysis.is_inconsistent or any(ea.is_inconsistent for ea in else_analyses):
            return ReturnAnalysis(is_inconsistent=True, node_type="if_else")
        
        # Propagate unreachable code flag from children
        has_unreachable = if_analysis.has_unreachable_code or any(ea.has_unreachable_code for ea in else_analyses)
        
        # Calculate return characteristics
        all_else_return = any(ea.has_return for ea in else_analyses)
        all_paths_return = False
        is_inconsistent = False
        
        if else_info['has_final_else'] and else_analyses:
            final_else = else_analyses[-1]
            all_paths_return = if_analysis.has_return and final_else.has_return
            
            # NEW: Check for inconsistency - if ANY branch returns but not ALL branches return
            # This catches: if{return} else-if{return} else{NO return}
            if if_analysis.has_return or final_else.has_return:
                # At least one branch returns
                if not (if_analysis.has_return and final_else.has_return):
                    # But not ALL branches return - inconsistent!
                    is_inconsistent = True
        
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
            all_paths_return=False,  # No else = not all paths return
            is_inconsistent=if_analysis.is_inconsistent,
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
            all_paths_return=False,  # Loops don't guarantee return
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
            'has_unreachable_code': False  # Track unreachable returns specifically
        }
        
        # First pass: analyze all children
        for i, child in enumerate(node.children):
            self._process_child(child, i, state)
        
        # Determine if all paths return (this also sets has_unreachable_code if needed)
        all_paths_return = self._determine_all_paths_return(node, state)
        
        # Second pass: check for unreachable code (old logic, keep for other patterns)
        self._check_unreachable_returns(node, state)
        
        return ReturnAnalysis(
            has_return=state['has_any_return'],
            all_paths_return=all_paths_return,
            is_inconsistent=state['has_inconsistency'],
            node_type="children",
            violations=state['all_violations'],
            has_unreachable_code=state.get('has_unreachable_code', False)  # Pass through unreachable flag
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
            
            # IMPORTANT: Only flag as "all paths return" if this is an if-else with a FINAL else
            # Don't flag standalone if statements or if-else-if without a final else
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
            state['has_unreachable_code'] = True  # Mark that we found unreachable code
    
    def _determine_all_paths_return(self, node: Any, state: Dict) -> bool:
        """Determine if all paths through this node return."""
        # Check if final statement is a return
        if state['last_return_index'] >= 0:
            has_only_empty_after = self._has_only_empty_after(
                node.children, 
                state['last_return_index']
            )
            if has_only_empty_after:
                state['has_final_return'] = True
        
        # Early return pattern + final return = all paths return
        if state['has_early_return_pattern'] and state['has_final_return']:
            return True
        
        # CRITICAL: Check if we have an if-else that returns on all paths
        # If so, check if there's ANY code after it (including returns)
        if state['has_if_else_all_paths_return']:
            # Find the if-else statement that returns on all paths
            for i, child in enumerate(node.children):
                if hasattr(child, 'data') and child.data == 'if_statement':
                    child_analysis = self.visit(child)
                    if child_analysis.all_paths_return:
                        # Check if there's ANY non-empty statement after this if-else
                        for j in range(i + 1, len(node.children)):
                            next_child = node.children[j]
                            # If we find a return statement after an if-else that covers all paths,
                            # that return is unreachable
                            if hasattr(next_child, 'data'):
                                if next_child.data == 'return_statement':
                                    state['has_unreachable_code'] = True
                                    state['has_inconsistency'] = True
                                    break
                                elif next_child.data not in ['empty_statement', 'eos']:
                                    # Found other non-empty code after complete if-else
                                    break
                        break
        
        return state['all_children_return'] and len(node.children) > 0
    
    def _has_only_empty_after(self, children: List[Any], index: int) -> bool:
        """Check if only empty statements exist after given index."""
        for i in range(index + 1, len(children)):
            child = children[i]
            if hasattr(child, 'data') and child.data not in ['empty_statement', 'eos']:
                return False
        return True


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
        visitor = ReturnConsistencyVisitor(self.file_path, self.line_offset)
        analysis = visitor.visit(node)
        
        # Skip inline functions
        if analysis.node_type != "function_definition":
            return
        
        # Add violations from analysis
        violations.extend(analysis.violations)
        
        # Apply policy decisions
        function_name = self.get_function_context_for_node(node, full_ast)
        
        # IMPORTANT: Check for unreachable code FIRST, even if is_inconsistent is True
        # Unreachable code is a subset of inconsistent, but needs a better message
        if analysis.has_unreachable_code:
            violations.append(self._create_violation(
                function_name,
                "has unreachable return statement - the if-else block above returns on all paths, making code after it unreachable. Remove the unreachable return statement",
                node
            ))
        # Only check is_inconsistent if we haven't already flagged unreachable code
        elif analysis.is_inconsistent:
            violations.append(self._create_violation(
                function_name,
                "has inconsistent return pattern - some paths return values, others don't",
                node
            ))
        # Check if the function has control flow with mixed returns
        elif (analysis.has_return and 
              not analysis.all_paths_return and 
              has_control_flow_structures(node)):
            # If the analysis found returns and not all paths return, flag it
            violations.append(self._create_violation(
                function_name,
                "has some return statements but not all code paths return - consider adding else branches or a final return statement",
                node
            ))
    
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