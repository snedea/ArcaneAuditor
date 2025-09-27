"""Descriptive parameter detection logic for ScriptDescriptiveParameterRule."""

from typing import Generator, Dict, List
from lark import Tree
from ...script.shared import ScriptDetector
from ...common import Violation
import re


class DescriptiveParameterDetector(ScriptDetector):
    """Detects non-descriptive parameter names in functional methods."""

    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(line_offset)
        self.file_path = file_path
        
        # Functional methods that should have descriptive parameters
        self.functional_methods = {
            'map', 'filter', 'find', 'forEach', 'reduce', 'sort'
        }
        
        # Allowed single-letter parameter names (traditional index variables)
        self.allowed_letters = {'i', 'j', 'k'}

    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect non-descriptive parameter names in functional methods."""
        if ast is None:
            return
        
        # Use AST traversal to find arrow function expressions in call expressions
        violations = self._find_arrow_function_violations(ast)
        for violation in violations:
            yield Violation(
                message=f"Parameter '{violation['param_name']}' in {violation['method_name']}() should be more descriptive. "
                       f"Consider using '{violation['suggested_name']}' instead. Single-letter parameters make nested functional "
                       f"methods harder to read and debug.",
                line=violation['line'],
                column=violation['column']
            )

    def set_original_content(self, content: str):
        """Set the original script content for pattern-based analysis."""
        self._original_content = content

    def _find_arrow_function_violations(self, ast: Tree) -> List[Dict]:
        """Find violations using AST traversal for arrow function expressions."""
        violations = []
        processed_arrow_functions = set()
        
        # Find all arguments expressions (which contain method calls with arrow functions)
        arguments_expressions = ast.find_data('arguments_expression')
        for args_expr in arguments_expressions:
            violations.extend(self._analyze_arguments_expression(args_expr, processed_arrow_functions))
        
        # Also find all arrow functions and check if they're part of functional method calls
        arrow_functions = ast.find_data('arrow_function_expression')
        for arrow_func in arrow_functions:
            if id(arrow_func) not in processed_arrow_functions:
                violations.extend(self._analyze_arrow_function_context(arrow_func, ast))
        
        return violations

    def _analyze_arguments_expression(self, args_expr: Tree, processed_arrow_functions: set) -> List[Dict]:
        """Analyze an arguments expression to find arrow function violations."""
        violations = []
        
        if not hasattr(args_expr, 'children') or len(args_expr.children) < 2:
            return violations
        
        # Get the function being called (first child)
        function_node = args_expr.children[0]
        method_name = self._extract_method_name(function_node)
        
        if method_name not in self.functional_methods:
            return violations
        
        # Look for arrow function expressions in the second child and its descendants
        second_child = args_expr.children[1]
        if second_child is not None:
            # If it's an argument_list, check each argument individually
            if second_child.data == 'argument_list':
                for arg in second_child.children:
                    if hasattr(arg, 'find_data'):
                        arrow_functions = arg.find_data('arrow_function_expression')
                        for arrow_func in arrow_functions:
                            processed_arrow_functions.add(id(arrow_func))
                            violations.extend(self._analyze_arrow_function(arrow_func, method_name, function_node))
            else:
                # For single argument cases, check the child directly
                arrow_functions = second_child.find_data('arrow_function_expression')
                for arrow_func in arrow_functions:
                    processed_arrow_functions.add(id(arrow_func))
                    violations.extend(self._analyze_arrow_function(arrow_func, method_name, function_node))
        
        return violations

    def _analyze_arrow_function_context(self, arrow_func: Tree, ast: Tree) -> List[Dict]:
        """Analyze an arrow function to see if it's part of a functional method call."""
        violations = []
        
        # This is a simplified approach - we'll analyze the arrow function
        # and assume it's part of a functional method call if it has problematic parameters
        # This avoids the complexity of tracking parent/sibling relationships
        
        # Check if this arrow function has problematic parameters
        if not hasattr(arrow_func, 'children'):
            return violations
        
        # Handle single parameter arrow functions: param => expression
        if len(arrow_func.children) == 2:
            param_node = arrow_func.children[0]
            if hasattr(param_node, 'value'):
                param_name = param_node.value
                if self._is_problematic_parameter(param_name):
                    # Use a generic method name since we can't easily determine the context
                    method_name = "functional method"
                    context = "item"
                    suggested_name = self._suggest_parameter_name("map", context, 0)  # Default to map suggestions
                    
                    violations.append({
                        'method_name': method_name,
                        'param_name': param_name,
                        'suggested_name': suggested_name,
                        'line': self.get_line_number(arrow_func),
                        'column': 1,  # Approximate
                        'context': context,
                        'param_index': 0
                    })
        
        # Handle multi-parameter arrow functions: (param1, param2) => expression
        elif len(arrow_func.children) > 2:
            # The last child is the expression, the rest are parameters
            for i in range(len(arrow_func.children) - 1):
                param_node = arrow_func.children[i]
                if hasattr(param_node, 'value'):
                    param_name = param_node.value
                    if self._is_problematic_parameter(param_name):
                        # Use a generic method name since we can't easily determine the context
                        method_name = "functional method"
                        context = "item"
                        suggested_name = self._suggest_parameter_name("reduce", context, i)  # Default to reduce suggestions
                        
                        violations.append({
                            'method_name': method_name,
                            'param_name': param_name,
                            'suggested_name': suggested_name,
                            'line': self.get_line_number(arrow_func),
                            'column': 1,  # Approximate
                            'context': context,
                            'param_index': i
                        })
        
        return violations

    def _extract_method_name(self, function_node: Tree) -> str:
        """Extract method name from function node."""
        if function_node.data == 'member_dot_expression':
            if len(function_node.children) >= 2 and hasattr(function_node.children[1], 'value'):
                return function_node.children[1].value
        elif function_node.data == 'identifier_expression':
            if len(function_node.children) > 0 and hasattr(function_node.children[0], 'value'):
                return function_node.children[0].value
        return ""

    def _analyze_arrow_function(self, arrow_func: Tree, method_name: str, context_node: Tree) -> List[Dict]:
        """Analyze an arrow function for parameter violations."""
        violations = []
        
        if not hasattr(arrow_func, 'children'):
            return violations
        
        # Handle single parameter arrow functions: param => expression
        if len(arrow_func.children) == 2:
            param_node = arrow_func.children[0]
            if hasattr(param_node, 'value'):
                param_name = param_node.value
                if self._is_problematic_parameter(param_name):
                    context = self._extract_context_from_node(context_node)
                    suggested_name = self._suggest_parameter_name(method_name, context, 0)
                    
                    violations.append({
                        'method_name': method_name,
                        'param_name': param_name,
                        'suggested_name': suggested_name,
                        'line': self.get_line_number(arrow_func),
                        'column': 1,  # Approximate
                        'context': context,
                        'param_index': 0
                    })
        
        # Handle multi-parameter arrow functions: (param1, param2) => expression
        # In this case, parameters are separate children before the expression
        elif len(arrow_func.children) > 2:
            # The last child is the expression, the rest are parameters
            for i in range(len(arrow_func.children) - 1):
                param_node = arrow_func.children[i]
                if hasattr(param_node, 'value'):
                    param_name = param_node.value
                    if self._is_problematic_parameter(param_name):
                        context = self._extract_context_from_node(context_node)
                        suggested_name = self._suggest_parameter_name(method_name, context, i)
                        
                        violations.append({
                            'method_name': method_name,
                            'param_name': param_name,
                            'suggested_name': suggested_name,
                            'line': self.get_line_number(arrow_func),
                            'column': 1,  # Approximate
                            'context': context,
                            'param_index': i
                        })
        
        return violations

    def _is_problematic_parameter(self, param_name: str) -> bool:
        """Check if parameter name is problematic."""
        return (len(param_name) == 1 and 
                param_name.lower() not in self.allowed_letters and
                param_name.isalpha())

    def _extract_context_from_node(self, context_node: Tree) -> str:
        """Extract context from AST node."""
        if context_node.data == 'member_dot_expression':
            if len(context_node.children) > 0:
                obj_node = context_node.children[0]
                if obj_node.data == 'identifier_expression' and len(obj_node.children) > 0:
                    if hasattr(obj_node.children[0], 'value'):
                        return obj_node.children[0].value
        return "item"

    def _find_parameter_violations(self, script_content: str) -> List[Dict]:
        """Find all violations of descriptive parameter naming in functional methods."""
        violations = []
        lines = script_content.split('\n')
        
        try:
            # Look for functional method patterns in the script content
            violations.extend(self._find_violations_by_pattern(lines))
            
        except Exception as e:
            print(f"Warning: Error in pattern-based parameter analysis: {e}")
        
        return violations

    def _find_violations_by_pattern(self, lines: List[str]) -> List[Dict]:
        """Find violations using regex patterns for functional methods."""
        violations = []
        
        for line_num, line in enumerate(lines, 1):
            # Pattern for single parameter functional methods: .method(param => ...)
            single_param_pattern = r'\.(' + '|'.join(self.functional_methods) + r')\s*\(\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=>'
            
            # Pattern for multi-parameter functional methods: .method((param1, param2) => ...)
            multi_param_pattern = r'\.(' + '|'.join(self.functional_methods) + r')\s*\(\s*\(\s*([^)]+)\s*\)\s*=>'
            
            # Check single parameter methods
            matches = re.finditer(single_param_pattern, line)
            for match in matches:
                method_name = match.group(1)
                param_name = match.group(2)
                
                # Check if parameter name is a problematic single letter
                if (len(param_name) == 1 and 
                    param_name.lower() not in self.allowed_letters and
                    param_name.isalpha()):
                    
                    context = self._extract_context(line, method_name)
                    suggested_name = self._suggest_parameter_name(method_name, context, 0)
                    
                    violations.append({
                        'method_name': method_name,
                        'param_name': param_name,
                        'suggested_name': suggested_name,
                        'line': line_num,
                        'column': match.start(2) + 1,
                        'context': context,
                        'param_index': 0  # Single parameter methods have index 0
                    })
            
            # Check multi-parameter methods (like reduce, sort)
            multi_matches = re.finditer(multi_param_pattern, line)
            for match in multi_matches:
                method_name = match.group(1)
                params_str = match.group(2).strip()
                
                # Parse individual parameters
                params = [p.strip() for p in params_str.split(',')]
                
                for i, param_name in enumerate(params):
                    # Check if parameter name is a problematic single letter
                    if (len(param_name) == 1 and 
                        param_name.lower() not in self.allowed_letters and
                        param_name.isalpha()):
                        
                        context = self._extract_context(line, method_name)
                        suggested_name = self._suggest_parameter_name(method_name, context, i)
                        
                        violations.append({
                            'method_name': method_name,
                            'param_name': param_name,
                            'suggested_name': suggested_name,
                            'line': line_num,
                            'column': match.start(2) + 1,  # Approximate position
                            'context': context,
                            'param_index': i
                        })
        
        return violations

    def _extract_context(self, line: str, method_name: str) -> str:
        """Extract context to help suggest better parameter names."""
        # Look for variable names or object properties before the method call
        # This helps suggest contextual parameter names
        
        # Pattern to find what's being called on: something.method(...)
        context_pattern = r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\.\s*' + re.escape(method_name)
        context_match = re.search(context_pattern, line)
        
        if context_match:
            return context_match.group(1)
        
        return "item"  # Default fallback

    def _suggest_parameter_name(self, method_name: str, context: str, param_index: int = 0) -> str:
        """Suggest a descriptive parameter name based on method, context, and parameter position."""
        
        # Special case for reduce - suggest based on parameter position (takes precedence over context)
        if method_name == 'reduce':
            if param_index == 0:
                return 'acc'  # First parameter is accumulator
            elif param_index == 1:
                return self._get_context_suggestion(context)  # Second parameter is current item
            else:
                return 'index'  # Third parameter is usually index
        
        # Special case for sort - typically uses 'a' and 'b'
        if method_name == 'sort':
            if param_index == 0:
                return 'a'
            elif param_index == 1:
                return 'b'
            else:
                return 'item'
        
        # For other methods, use context-based suggestion
        context_suggestion = self._get_context_suggestion(context)
        
        # Method-specific fallbacks if context doesn't provide good suggestion
        method_suggestions = {
            'map': 'item',
            'filter': 'item', 
            'find': 'item',
            'forEach': 'item'
        }
        
        # Use context suggestion if it's good, otherwise use method-specific fallback
        if context_suggestion != 'item':
            return context_suggestion
        else:
            return method_suggestions.get(method_name, 'item')

    def _get_context_suggestion(self, context: str) -> str:
        """Get context-based parameter suggestion."""
        context_suggestions = {
            'users': 'user',
            'workers': 'worker', 
            'employees': 'employee',
            'items': 'item',
            'tasks': 'task',
            'orders': 'order',
            'products': 'product',
            'departments': 'dept',
            'teams': 'team',
            'projects': 'project',
            'files': 'file',
            'documents': 'doc',
            'records': 'record',
            'entries': 'entry',
            'results': 'result',
            'values': 'value',
            'numbers': 'num',
            'points': 'point',
            'coordinates': 'coord',
            'positions': 'pos'
        }
        
        context_lower = context.lower()
        for plural, singular in context_suggestions.items():
            if plural in context_lower:
                return singular
        
        return 'item'  # Default fallback

    def _is_nested_functional_call(self, line: str, position: int) -> bool:
        """Check if this functional call is nested inside another."""
        # Simple heuristic: count functional method calls before this position
        line_before = line[:position]
        functional_calls = 0
        
        for method in self.functional_methods:
            functional_calls += line_before.count(f'.{method}(')
        
        return functional_calls > 0
