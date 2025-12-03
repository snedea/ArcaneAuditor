"""Script function parameter count rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .function_parameter_count_detector import FunctionParameterCountDetector


class ScriptFunctionParameterCountRule(ScriptRuleBase):
    """Rule to check for functions with too many parameters."""

    DESCRIPTION = "Functions should not have too many parameters (max 4 by default)"
    SEVERITY = "ADVICE"
    DETECTOR = FunctionParameterCountDetector
    AVAILABLE_SETTINGS = {
        'max_parameters': {'type': 'int', 'default': 4, 'description': 'Maximum number of parameters allowed'}
    }
    
    DOCUMENTATION = {
        'why': '''Functions with more than 4 parameters can lead to bugs when arguments are passed in the wrong order. Refactoring to use parameter objects or breaking into smaller functions makes your code clearer and less error-prone.''',
        'catches': [
            'Functions with more than 4 parameters',
            'Functions that likely need parameter objects or refactoring'
        ],
        'examples': '''**Example violations:**

```javascript
function createUser(name, email, phone, address, age, department) { // ❌ 6 parameters
    // ... function body
}
```

**Fix:**

```javascript
// Break into smaller functions
function createUser(personalInfo, contactInfo, workInfo) { // ✅ 3 logical groups
    // ... function body
}
```''',
        'recommendation': 'Refactor functions with more than 4 parameters to use parameter objects or break them into smaller, focused functions. This reduces the chance of passing arguments in the wrong order and makes the code clearer.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
