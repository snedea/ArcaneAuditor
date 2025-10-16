"""Detector for function return consistency analysis."""

from typing import Any, List, Dict
from ...script.shared import Violation, ScriptDetector, has_control_flow_structures, is_script_expression_with_returns, get_function_body
from ...common import ASTLineUtils


class ReturnAnalysis:
    """Container for return analysis results - focused on facts, not policy."""
    def __init__(self, has_return: bool = False, all_paths_return: bool = False, 
                 is_inconsistent: bool = False, node_type: str = "unknown", 
                 violations: List[Violation] = None):
        self.has_return = has_return
        self.all_paths_return = all_paths_return
        self.is_inconsistent = is_inconsistent
        self.node_type = node_type
        self.violations = violations or []
    
    def __repr__(self):
        violation_preview = ""
        if self.violations:
            first_violation = self.violations[0]
            violation_preview = f", first_violation='{first_violation.message[:50]}...'"
        return f"ReturnAnalysis(has_return={self.has_return}, all_paths_return={self.all_paths_return}, is_inconsistent={self.is_inconsistent}, node_type='{self.node_type}', violations={len(self.violations)}{violation_preview})"


class ReturnConsistencyVisitor:
    """Policy-agnostic visitor for analyzing return consistency in AST nodes."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        self.memo_cache: Dict[int, ReturnAnalysis] = {}
        self.file_path = file_path
        self.line_offset = line_offset
        self.function_depth = 0  # Track nesting depth of functions
        
        # Method dispatch map for micro-optimization
        self.visit_methods = {
            'function_expression': self.visit_function_expression,
            'statement_list': self.visit_statement_list,
            'return_statement': self.visit_return_statement,
            'if_statement': self.visit_if_statement,
            'while_statement': self.visit_while_statement,
            'for_statement': self.visit_for_statement,
        }
    
    def visit(self, node: Any) -> ReturnAnalysis:
        """Main entry point for visiting any node."""
        if not hasattr(node, 'data'):
            return ReturnAnalysis()
        
        # Use memoization to avoid recomputing
        node_id = id(node)
        if node_id in self.memo_cache:
            return self.memo_cache[node_id]
        
        # Use method dispatch map for micro-optimization
        visit_method = self.visit_methods.get(node.data, self.visit_default)
        result = visit_method(node)
        
        # Cache the result
        self.memo_cache[node_id] = result
        return result
    
    def visit_function_expression(self, node: Any) -> ReturnAnalysis:
        """Analyze function expressions, distinguishing between definitions and script expressions."""
        # Check if this is a script expression (fake function) vs actual function definition
        if is_script_expression_with_returns(node):
            # This is a script expression with return statements, not a real function
            return ReturnAnalysis(node_type="script_expression")
        
        # Increment function depth for nested functions
        self.function_depth += 1
        
        # Skip analysis for inline functions (nested more than 1 level deep)
        if self.function_depth > 1:
            self.function_depth -= 1
            return ReturnAnalysis(node_type="inline_function")
        
        # This is a real function definition - analyze it for return consistency
        function_body = get_function_body(node)
        
        # If get_function_body doesn't work, try finding the body directly
        # (handles anonymous functions where body is at different index)
        if not function_body and hasattr(node, 'children'):
            for child in node.children:
                if hasattr(child, 'data') and child.data in ['source_elements', 'block_statement']:
                    function_body = child
                    break
        
        if function_body:
            analysis = self.visit(function_body)
            
            # Return analysis without policy decisions - let the detector decide
            result = ReturnAnalysis(
                has_return=analysis.has_return,
                all_paths_return=analysis.all_paths_return,
                is_inconsistent=analysis.is_inconsistent,
                node_type="function_definition",
                violations=analysis.violations
            )
        else:
            result = ReturnAnalysis(node_type="function_definition")
        
        # Decrement function depth
        self.function_depth -= 1
        return result
    
    def visit_default(self, node: Any) -> ReturnAnalysis:
        """Default visitor for unknown node types."""
        if not hasattr(node, 'children'):
            return ReturnAnalysis()
        
        # For unknown nodes, analyze children
        return self.analyze_children(node)
    
    def visit_statement_list(self, node: Any) -> ReturnAnalysis:
        """Analyze statement lists (if blocks, function bodies, etc.)."""
        return self.analyze_children(node)
    
    def visit_return_statement(self, node: Any) -> ReturnAnalysis:
        """Return statements always return."""
        return ReturnAnalysis(has_return=True, all_paths_return=True, node_type="return")
    
    def visit_if_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze if statements for return consistency."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return ReturnAnalysis()
        
        # The if statement structure is:
        # children[0]: condition
        # children[1]: empty_expression (not the if block!)
        # children[2]: statement_list (this is the actual if block!)
        
        # Find the actual if block - it should be a statement_list
        if_block = None
        for child in node.children:
            if hasattr(child, 'data') and child.data == 'statement_list':
                if_block = child
                break
        
        if if_block is None:
            # Fallback to analyzing all children
            return self.analyze_children(node)
        
        if_analysis = self.visit(if_block)
        
        # Check for else/else-if blocks
        # AST structure: [Token(if), expression, if_block, Token(else), else_block]
        has_else = False
        has_final_else = False
        else_blocks = []
        
        if len(node.children) >= 5:
            # Check if we have an else block (child[4])
            else_block = node.children[4]
            if hasattr(else_block, 'data') and else_block.data in ['statement_list', 'block']:
                has_else = True
                else_blocks.append(else_block)
                has_final_else = True
        
        if has_else:
            # Analyze all else/else-if blocks
            else_analyses = []
            all_else_return = False
            all_else_paths_return = True
            
            for else_block in else_blocks:
                else_analysis = self.visit(else_block)
                else_analyses.append(else_analysis)
                all_else_return = all_else_return or else_analysis.has_return
                all_else_paths_return = all_else_paths_return and else_analysis.all_paths_return
            
            # Check for inconsistencies in any branch
            if if_analysis.is_inconsistent:
                return ReturnAnalysis(is_inconsistent=True, node_type="if_else")
            
            for else_analysis in else_analyses:
                if else_analysis.is_inconsistent:
                    return ReturnAnalysis(is_inconsistent=True, node_type="if_else")
            
            # For if-else statements, we don't flag mixed return patterns as inconsistent
            # The parent context will determine if there are unreachable returns
            # Only consider "all paths return" if there's a final else block that returns
            all_paths_return = False
            if has_final_else:
                # Check if the final else block returns
                final_else_analysis = else_analyses[-1] if else_analyses else None
                if final_else_analysis and final_else_analysis.has_return:
                    all_paths_return = if_analysis.has_return and all_else_return
            
            result = ReturnAnalysis(
                has_return=if_analysis.has_return or all_else_return,
                all_paths_return=all_paths_return,
                node_type="if_else"
            )
            return result
        else:
            # No else block - the if statement itself doesn't guarantee all paths return
            # But it does return if the if block returns
            return ReturnAnalysis(
                has_return=if_analysis.has_return,
                all_paths_return=False,  # No else means not all paths return from this if statement
                is_inconsistent=if_analysis.is_inconsistent,
                node_type="if_no_else"
            )
    
    def _analyze_loop(self, node: Any, node_type: str) -> ReturnAnalysis:
        """Generic loop analysis for while/for statements."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return ReturnAnalysis(node_type=node_type)
        
        body_analysis = self.visit(node.children[1])
        return ReturnAnalysis(
            has_return=body_analysis.has_return,
            all_paths_return=False,  # Loops don't guarantee all paths return
            is_inconsistent=body_analysis.is_inconsistent,
            node_type=node_type,
            violations=body_analysis.violations
        )
    
    def visit_while_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze while loops."""
        return self._analyze_loop(node, "while")
    
    def visit_for_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze for loops."""
        return self._analyze_loop(node, "for")
    
    def analyze_children(self, node: Any) -> ReturnAnalysis:
        """Analyze all children of a node."""
        if not hasattr(node, 'children'):
            return ReturnAnalysis()
        
        has_any_return = False
        all_children_return = True
        has_inconsistency = False
        all_violations = []
        
        # Track if we have an early return pattern (if statement with return + final return)
        has_early_return_pattern = False
        has_final_return = False
        last_return_index = -1
        
        # Track if we have an if-else that returns on all paths (for unreachable return detection)
        has_if_else_all_paths_return = False
        
        for i, child in enumerate(node.children):
            child_analysis = self.visit(child)
            
            # Collect violations from child
            all_violations.extend(child_analysis.violations)
            
            if child_analysis.is_inconsistent:
                has_inconsistency = True
            
            if child_analysis.has_return:
                has_any_return = True
                last_return_index = i
            
            # Check for early return pattern: if statement with return followed by final return
            if (hasattr(child, 'data') and child.data == 'if_statement' and 
                child_analysis.has_return and not child_analysis.is_inconsistent):
                has_early_return_pattern = True
                
                # Check if this is an if-else that returns on all paths
                if child_analysis.all_paths_return:
                    has_if_else_all_paths_return = True
            
            # Track if this child doesn't return on all paths
            if not child_analysis.all_paths_return:
                all_children_return = False
        
        # Check if the last return statement is at the end (or near the end, ignoring empty statements)
        if last_return_index >= 0:
            # Check if there are only empty statements after the last return
            has_only_empty_after_return = True
            for i in range(last_return_index + 1, len(node.children)):
                child = node.children[i]
                if hasattr(child, 'data') and child.data not in ['empty_statement', 'eos']:
                    has_only_empty_after_return = False
                    break
            
            if has_only_empty_after_return:
                has_final_return = True
        
        # If we have early return pattern + final return, all paths do return
        if has_early_return_pattern and has_final_return:
            all_children_return = True
        
        
        # Check for unreachable returns: if-else returns on all paths but there are returns after it
        if has_if_else_all_paths_return and last_return_index >= 0:
            # Find the last if-else that returns on all paths
            last_if_else_all_paths_index = -1
            for i, child in enumerate(node.children):
                if (hasattr(child, 'data') and child.data == 'if_statement'):
                    child_analysis = self.visit(child)
                    if child_analysis.all_paths_return:
                        last_if_else_all_paths_index = i
            
            # If there are return statements after the last if-else that returns on all paths,
            # those returns are unreachable
            if last_if_else_all_paths_index >= 0 and last_return_index > last_if_else_all_paths_index:
                has_inconsistency = True
        
        
        return ReturnAnalysis(
            has_return=has_any_return,
            all_paths_return=all_children_return and len(node.children) > 0,
            is_inconsistent=has_inconsistency,
            node_type="children",
            violations=all_violations
        )


class ReturnConsistencyDetector(ScriptDetector):
    """Detector for function return consistency violations."""
    
    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """Detect return consistency violations in the AST."""
        violations = []
        self._check_functions_with_visitor(ast, violations, ast)
        return violations
    
    def _check_functions_with_visitor(self, node: Any, violations: List[Violation], full_ast: Any):
        """Recursively check functions in AST nodes using the visitor pattern."""
        if hasattr(node, 'data') and node.data == 'function_expression':
            # Use the visitor to analyze the function expression
            visitor = ReturnConsistencyVisitor(self.file_path, self.line_offset)
            analysis = visitor.visit(node)
            
            # Apply policy decisions here (not in the visitor)
            if analysis.node_type == "function_definition":
                # Get the function name for context
                function_name = self.get_function_context_for_node(node, full_ast)
                
                # Check for inconsistencies (mixed return patterns)
                if analysis.is_inconsistent:
                    if function_name:
                        message = f"Function '{function_name}' has inconsistent return pattern - some paths return values, others don't"
                    else:
                        message = "Function has inconsistent return pattern - some paths return values, others don't"
                    
                    violations.append(Violation(
                        message=message,
                        line=self.get_line_number_from_token(node)
                    ))
                # Only flag partial returns if there are control flow structures that create multiple paths
                # Don't flag simple sequential functions with a single return at the end
                elif analysis.has_return and not analysis.all_paths_return and has_control_flow_structures(node):
                    if function_name:
                        message = f"Function '{function_name}' has some return statements but not all code paths return - consider adding else branches"
                    else:
                        message = "Function has some return statements but not all code paths return - consider adding else branches"
                    
                    violations.append(Violation(
                        message=message,
                        line=self.get_line_number_from_token(node)
                    ))
                # Note: We no longer flag functions with no return statements (void functions)
                # as these are valid patterns for side-effect only functions
            elif analysis.node_type == "inline_function":
                # Skip analysis for inline functions - they are implementation details
                pass
            
            # Add any violations from the analysis
            violations.extend(analysis.violations)
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                self._check_functions_with_visitor(child, violations, full_ast)
    
    def _function_appears_to_compute_value(self, function_node: Any) -> bool:
        """
        Heuristic to determine if a function appears to compute a value.
        Returns True if the function has variable declarations or assignments
        that suggest it's computing something but not returning it.
        """
        function_body = get_function_body(function_node)
        
        # If get_function_body doesn't work, try finding the body directly
        # (handles anonymous functions where body is at different index)
        if not function_body and hasattr(function_node, 'children'):
            for child in function_node.children:
                if hasattr(child, 'data') and child.data in ['source_elements', 'block_statement']:
                    function_body = child
                    break
        
        if not function_body:
            return False
        
        # Check if function body has variable declarations
        has_variable_declarations = self._has_variable_declarations(function_body)
        
        # If there are variable declarations, the function likely computes something
        return has_variable_declarations
    
    def _has_variable_declarations(self, node: Any) -> bool:
        """Recursively check if a node contains variable declarations."""
        if not hasattr(node, 'data'):
            return False
        
        # Check if this node is a variable declaration
        if node.data == 'variable_declaration':
            return True
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                if self._has_variable_declarations(child):
                    return True
        
        return False
    
