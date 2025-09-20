from typing import Generator, Set, Dict, List
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, PODModel, ScriptModel
import re


class ScriptDescriptiveParameterRule(Rule):
    """Validates that functional method parameters use descriptive names instead of single letters."""
    
    DESCRIPTION = "Ensures functional method parameters use descriptive names (except 'i', 'j', 'k' for indices)"
    SEVERITY = "INFO"
    
    # Functional methods that should have descriptive parameters
    FUNCTIONAL_METHODS = {
        'map', 'filter', 'find', 'forEach', 'reduce', 'sort'
    }
    
    # Allowed single-letter parameter names (traditional index variables)
    ALLOWED_SINGLE_LETTERS = {'i', 'j', 'k'}
    
    def __init__(self, config: Dict = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        # Allow configuration of which single letters are acceptable
        self.allowed_letters = set(self.config.get('allowed_single_letters', self.ALLOWED_SINGLE_LETTERS))
        # Allow configuration of additional functional methods to check
        additional_methods = self.config.get('additional_functional_methods', [])
        self.functional_methods = self.FUNCTIONAL_METHODS | set(additional_methods)
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze scripts for non-descriptive functional method parameters."""
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            script_fields = self.find_script_fields(pmd_model)
            for field_path, field_value, field_name, line_offset in script_fields:
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_parameter_names(field_value, field_name, pmd_model.file_path, line_offset)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)
    
    def _analyze_script_file(self, script_model: ScriptModel) -> Generator[Finding, None, None]:
        """Analyze standalone script files for descriptive parameter usage."""
        try:
            yield from self._check_parameter_names(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")
    
    def _check_parameter_names(self, script_content: str, field_name: str, file_path: str, line_offset: int) -> Generator[Finding, None, None]:
        """Check for non-descriptive parameter names in functional methods."""
        try:
            # Parse the script content using the built-in parser
            ast = self._parse_script_content(script_content)
            
            # Find all functional method calls with single-letter parameters
            violations = self._find_parameter_violations(ast, script_content)
            
            for violation in violations:
                # Calculate suggested parameter name based on context and parameter position
                param_index = violation.get('param_index', 0)
                suggested_name = self._suggest_parameter_name(violation['method_name'], violation['context'], param_index)
                
                
                yield Finding(
                    rule=self,
                    message=f"Parameter '{violation['param_name']}' in {violation['method_name']}() should be more descriptive. "
                           f"Consider using '{suggested_name}' instead. Single-letter parameters make nested functional "
                           f"methods harder to read and debug.",
                    line=line_offset + violation['line'] - 1,
                    column=violation['column'],
                    file_path=file_path
                )
        
        except Exception as e:
            print(f"Error analyzing parameter names in {file_path} ({field_name}): {e}")
    
    def _find_parameter_violations(self, ast, script_content: str) -> List[Dict]:
        """Find all violations of descriptive parameter naming in functional methods."""
        violations = []
        lines = script_content.split('\n')
        
        try:
            # Look for functional method patterns in the script content
            # This is a simplified pattern-based approach since full AST traversal is complex
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
                    
                    violations.append({
                        'method_name': method_name,
                        'param_name': param_name,
                        'line': line_num,
                        'column': match.start(2) + 1,
                        'context': self._extract_context(line, method_name),
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
                        
                        violations.append({
                            'method_name': method_name,
                            'param_name': param_name,
                            'line': line_num,
                            'column': match.start(2) + 1,  # Approximate position
                            'context': self._extract_context(line, method_name),
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
        
        return functional_calls > 1
    
    def _extract_full_chain(self, lines: List[str], start_line: int) -> str:
        """Extract the full method chain to better understand context."""
        # This could be enhanced to handle multi-line method chains
        # For now, just return the current line
        if start_line <= len(lines):
            return lines[start_line - 1].strip()
        return ""
