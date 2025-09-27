# Unified Rule Architecture

## Overview

This document describes the new unified architecture for script analysis rules that provides consistency, reusability, testability, and maintainability across all 32 rules.

## Architecture Components

### 1. Shared Violation Handling

**File**: `parser/rules/script/shared/violation.py`

```python
@dataclass
class Violation:
    """Represents a code violation with consistent structure."""
    message: str
    line: int
    column: int = 1
    metadata: Optional[Dict[str, Any]] = None
```

All rules now use this unified `Violation` dataclass instead of ad-hoc dictionaries or direct `Finding` creation.

### 2. Detector Pattern

**File**: `parser/rules/script/shared/detector.py`

```python
class ScriptDetector(ABC):
    """Base class for script analysis detectors."""
    
    @abstractmethod
    def detect(self, ast: Any) -> List[Violation]:
        """Analyze AST and return list of violations."""
        pass
```

Each rule has a dedicated detector class that:
- Only analyzes AST and returns violations
- Is policy-agnostic (focuses on facts, not suggestions)
- Can be tested in isolation
- Is reusable across different rule contexts

### 3. Standard Rule Scaffolding

**File**: `parser/rules/script/shared/rule_base.py`

```python
class ScriptRuleBase(Rule, ABC):
    """Base class for script analysis rules with unified structure."""
    
    # Subclasses must define these
    DETECTOR: type[ScriptDetector]
    
    @abstractmethod
    def get_description(self) -> str:
        """Get rule description - must be implemented by subclasses."""
        pass
```

Every rule follows this pattern:
1. Inherits from `ScriptRuleBase`
2. Defines a `DETECTOR` class attribute
3. Implements `get_description()`
4. Gets all PMD/POD/script analysis logic for free

### 4. Common AST Utilities

**File**: `parser/rules/script/shared/ast_utils.py`

Provides shared utilities:
- `get_line_number()` - Extract line numbers with offset
- `extract_expression_text()` - Get text from expression nodes
- `find_member_access_chains()` - Find property access chains
- `find_data_nodes()` - Find nodes of specific types
- `has_control_flow_structures()` - Check for control flow
- `is_script_expression_with_returns()` - Distinguish script expressions from functions
- `CONTROL_FLOW_NODES` - Constant set for efficient membership checking

## Migration Guide

### Step 1: Create Detector Class

**Before** (mixed detection and policy):
```python
class ScriptMagicNumberRule(Rule):
    def _check_magic_numbers(self, script_content, field_name, file_path, line_offset=1):
        # Direct AST analysis mixed with policy decisions
        ast = self._parse_script_content(script_content)
        if not ast:
            return
        
        for node in ast.find_data('literal'):
            if self._is_magic_number(node):
                yield Finding(
                    rule=self,
                    message=f"Magic number found: {node.children[0].value}",
                    line=node.meta.line + line_offset - 1,
                    column=1,
                    file_path=file_path
                )
```

**After** (separated detection and policy):
```python
class MagicNumberDetector(ScriptDetector):
    def detect(self, ast: Any) -> List[Violation]:
        violations = []
        for node in ast.find_data('literal'):
            if self._is_magic_number(node):
                violations.append(Violation(
                    message=f"Magic number found: {node.children[0].value}",
                    line=get_line_number(node, self.line_offset)
                ))
        return violations

class ScriptMagicNumberRule(ScriptRuleBase):
    DESCRIPTION = "Avoid magic numbers - use named constants instead"
    SEVERITY = "warning"
    DETECTOR = MagicNumberDetector
    
    def get_description(self) -> str:
        return self.DESCRIPTION
```

### Step 2: Update Imports

```python
# Old imports
from ...base import Rule, Finding
from ....models import PMDModel, PodModel

# New imports
from ...script.shared import ScriptRuleBase
from .magic_number_detector import MagicNumberDetector
```

### Step 3: Remove Boilerplate

The new architecture eliminates:
- Manual PMD/POD/script file iteration
- Script field extraction logic
- AST parsing and error handling
- Violation-to-Finding conversion
- Line offset calculations

### Step 4: Test Detector in Isolation

```python
def test_magic_number_detector():
    detector = MagicNumberDetector()
    ast = parse_script("const x = 42;")
    violations = detector.detect(ast)
    
    assert len(violations) == 1
    assert violations[0].message == "Magic number found: 42"
    assert violations[0].line == 1
```

## Benefits

### 1. Consistency
- All rules follow the same structure
- Uniform violation handling
- Standardized error messages and line numbers

### 2. Reusability
- Shared AST utilities eliminate duplication
- Detectors can be reused across rules
- Common patterns are centralized

### 3. Testability
- Detectors can be tested in isolation
- No need to mock PMD/POD parsing
- Focused unit tests for detection logic

### 4. Maintainability
- Adding new rules requires minimal boilerplate
- Changes to common logic benefit all rules
- Clear separation of concerns

### 5. Performance
- Efficient AST traversal with memoization
- Set-based control flow detection
- Reduced redundant parsing

## Example: Complete Rule Migration

### Before (ScriptFunctionReturnConsistencyRule)
- 386 lines of mixed concerns
- Manual AST traversal
- Policy decisions mixed with detection
- Complex visitor pattern
- Inconsistent violation handling

### After (Unified Architecture)
- **Rule**: 16 lines - just configuration
- **Detector**: 200 lines - focused on detection
- **Shared utilities**: Reusable across all rules
- **Clear separation**: Policy vs. facts
- **Consistent structure**: Matches all other rules

## Implementation Status

✅ **Completed**:
- Shared violation and detector base classes
- Common AST utility module
- Standard rule scaffolding base class
- All 32 script rules refactored to unified architecture:
  - ScriptFunctionReturnConsistencyRule
  - ScriptNullSafetyRule
  - ScriptUnusedVariableRule
  - ScriptUnusedFunctionParametersRule
  - ScriptUnusedFunctionRule
  - ScriptUnusedScriptIncludesRule
  - All other existing script rules (already using unified architecture)

🔄 **Next Steps**:
- Update documentation and examples
- Add comprehensive test suite for shared utilities
- Performance optimization and monitoring

## File Structure

```
parser/rules/script/
├── shared/
│   ├── __init__.py          # Exports all shared components
│   ├── violation.py         # Violation dataclass
│   ├── detector.py          # ScriptDetector base class
│   ├── ast_utils.py         # Common AST utilities
│   └── rule_base.py         # ScriptRuleBase class
├── logic/
│   ├── return_consistency.py           # Refactored rule (16 lines)
│   └── return_consistency_detector.py  # Detector (200 lines)
└── [other rule categories]/
    ├── [rule_name].py       # Rule class (minimal)
    └── [rule_name]_detector.py  # Detector class
```

This architecture provides a solid foundation for maintaining and extending the script analysis rules while ensuring consistency and quality across the entire codebase.
