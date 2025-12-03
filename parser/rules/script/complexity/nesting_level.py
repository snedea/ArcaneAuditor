"""Script nesting level rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .nesting_level_detector import NestingLevelDetector


class ScriptNestingLevelRule(ScriptRuleBase):
    """Rule to check for excessive nesting levels."""

    DESCRIPTION = "Ensures scripts don't have excessive nesting levels (max 4 levels)"
    SEVERITY = "ADVICE"
    DETECTOR = NestingLevelDetector
    AVAILABLE_SETTINGS = {
        'max_nesting': {'type': 'int', 'default': 4, 'description': 'Maximum nesting level allowed'}
    }
    
    DOCUMENTATION = {
        'why': '''Deep nesting (more than 4 levels of if/for/while statements) makes code exponentially harder to read, test, and debug. Each nesting level adds cognitive load, making it difficult to track which conditions are active and increasing the likelihood of logic errors. Flattening nested code through early returns or extracted functions dramatically improves maintainability.''',
        'catches': [
            'Overly nested code structures (if statements, loops, functions)',
            'Code that\'s difficult to read and maintain due to deep nesting'
        ],
        'examples': '''**Example violations:**

```javascript
function processData(data) {
    if (!empty data) { // Level 1
        if (data.isValid) { // Level 2
            if (data.hasContent) { // Level 3
                if (data.content.size() > 0) { // Level 4
                    if (data.content[0].isActive) { // Level 5 ❌ Too deep!
                        return data.content[0];
                    }
                }
            }
        }
    }
}
```

**Fix:**

```javascript
function processData(data) {
    if (empty data.content || !data.isValid || !data.hasContent) {
        return null;
    }

    return data.content[0].isActive ? data.content[0] : null;
}
```''',
        'recommendation': 'Flatten nested code by using early returns, extracting functions, or combining conditions. Keep nesting levels to 4 or fewer to improve readability and maintainability.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
