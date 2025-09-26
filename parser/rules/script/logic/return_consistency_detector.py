"""Detector for function return consistency analysis."""

from typing import Any, List, Dict
from ...script.shared import Violation, ScriptDetector, get_line_number, has_control_flow_structures, is_script_expression_with_returns, get_function_body


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
        
        # Method dispatch map for micro-optimization
        self.visit_methods = {
            'function_expression': self.visit_function_expression,
            'block_statement': self.visit_block_statement,
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
        
        # This is a real function definition - analyze it for return consistency
        function_body = get_function_body(node)
        if function_body:
            analysis = self.visit(function_body)
            
            # Return analysis without policy decisions - let the detector decide
            return ReturnAnalysis(
                has_return=analysis.has_return,
                all_paths_return=analysis.all_paths_return,
                is_inconsistent=analysis.is_inconsistent,
                node_type="function_definition",
                violations=analysis.violations
            )
        
        return ReturnAnalysis(node_type="function_definition")
    
    def visit_default(self, node: Any) -> ReturnAnalysis:
        """Default visitor for unknown node types."""
        if not hasattr(node, 'children'):
            return ReturnAnalysis()
        
        # For unknown nodes, analyze children
        return self.analyze_children(node)
    
    def visit_block_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze block statements (function bodies, if blocks, etc.)."""
        return self.analyze_children(node)
    
    def visit_return_statement(self, node: Any) -> ReturnAnalysis:
        """Return statements always return."""
        return ReturnAnalysis(has_return=True, all_paths_return=True, node_type="return")
    
    def visit_if_statement(self, node: Any) -> ReturnAnalysis:
        """Analyze if statements for return consistency."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return ReturnAnalysis()
        
        # Analyze if block
        if_block = node.children[1]
        if_analysis = self.visit(if_block)
        
        # Check for else block
        has_else = len(node.children) > 2
        if has_else:
            else_block = node.children[2]
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
            # No else block - if statement doesn't guarantee return
            return ReturnAnalysis(
                has_return=if_analysis.has_return,
                all_paths_return=False,  # No else means not all paths return
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
        
        for child in node.children:
            child_analysis = self.visit(child)
            
            # Collect violations from child
            all_violations.extend(child_analysis.violations)
            
            if child_analysis.is_inconsistent:
                has_inconsistency = True
            
            if child_analysis.has_return:
                has_any_return = True
            
            if not child_analysis.all_paths_return:
                all_children_return = False
        
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
        self._check_functions_with_visitor(ast, violations)
        return violations
    
    def _check_functions_with_visitor(self, node: Any, violations: List[Violation]):
        """Recursively check functions in AST nodes using the visitor pattern."""
        if hasattr(node, 'data') and node.data == 'function_expression':
            # Use the visitor to analyze the function expression
            visitor = ReturnConsistencyVisitor(self.file_path, self.line_offset)
            analysis = visitor.visit(node)
            
            # Apply policy decisions here (not in the visitor)
            if analysis.node_type == "function_definition":
                # Check for inconsistencies (mixed return patterns)
                if analysis.is_inconsistent:
                    violations.append(Violation(
                        message="Function has inconsistent return pattern - some paths return values, others don't",
                        line=get_line_number(node, self.line_offset)
                    ))
                # Only flag partial returns if there are control flow structures that create multiple paths
                # Don't flag simple sequential functions with a single return at the end
                elif analysis.has_return and not analysis.all_paths_return and has_control_flow_structures(node):
                    violations.append(Violation(
                        message="Function has some return statements but not all code paths return - consider adding else branches",
                        line=get_line_number(node, self.line_offset)
                    ))
            
            # Add any violations from the analysis
            violations.extend(analysis.violations)
        
        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                self._check_functions_with_visitor(child, violations)
