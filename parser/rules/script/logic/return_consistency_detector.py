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
        
        # Check for else block (would be after the statement_list)
        has_else = len(node.children) > 3
        if has_else:
            else_block = node.children[3]  # else block would be at index 3
            else_analysis = self.visit(else_block)
            
            # Both branches must be consistent
            if if_analysis.is_inconsistent or else_analysis.is_inconsistent:
                return ReturnAnalysis(is_inconsistent=True, node_type="if_else")
            
            # Check for mixed return patterns
            if if_analysis.has_return != else_analysis.has_return:
                return ReturnAnalysis(is_inconsistent=True, node_type="if_else")
            
            return ReturnAnalysis(
                has_return=if_analysis.has_return or else_analysis.has_return,
                all_paths_return=if_analysis.all_paths_return and else_analysis.all_paths_return,
                node_type="if_else"
            )
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
        
        for i, child in enumerate(node.children):
            child_analysis = self.visit(child)
            
            # Collect violations from child
            all_violations.extend(child_analysis.violations)
            
            if child_analysis.is_inconsistent:
                has_inconsistency = True
            
            if child_analysis.has_return:
                has_any_return = True
                
                # Check if this is a final return (last statement)
                if i == len(node.children) - 1:
                    has_final_return = True
            
            # Check for early return pattern: if statement with return followed by final return
            if (hasattr(child, 'data') and child.data == 'if_statement' and 
                child_analysis.has_return and not child_analysis.is_inconsistent):
                has_early_return_pattern = True
            
            # Only set all_children_return to False if this child doesn't return AND
            # it's not part of an early return + final return pattern
            if not child_analysis.all_paths_return:
                # If this is an if statement that returns, don't mark as inconsistent yet
                # We'll check if there's a final return after it
                if not (hasattr(child, 'data') and child.data == 'if_statement' and child_analysis.has_return):
                    all_children_return = False
        
        # If we have early return pattern + final return, all paths do return
        if has_early_return_pattern and has_final_return:
            all_children_return = True
        
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
    
