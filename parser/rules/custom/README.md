# Custom Rules Development Guide 🔮

*Create mystical validation rules for the Arcane Auditor*

This directory allows you to create custom validation rules for the Arcane Auditor without modifying the official codebase. This is perfect for:

- **Adding organization-specific rules**
- **Extending functionality** without waiting for official releases
- **Sharing custom rules** with your team or community
- **Avoiding conflicts** when updating the main tool

## 🏗️ Directory Structure

```
custom/
├── __init__.py                    # Package initialization
├── README.md                     # This documentation
├── examples/                     # Example implementations
│   ├── __init__.py
│   └── _example_custom_rule.py   # Sample custom rule (excluded from discovery)
└── user/                         # Your custom rules go here
    ├── __init__.py
    └── [your custom rule files]
```

> **Note**: Example files are prefixed with `_` and marked with `IS_EXAMPLE = True` to prevent them from being automatically discovered and run during analysis.

## 🏷️ Naming Conventions

### Rule Class Names

- **Official rules**: Use descriptive class names (e.g., `ScriptVarUsageRule`, `WidgetIdRequiredRule`)
- **Custom rules**: Use descriptive class names with `Custom` prefix (e.g., `CustomScriptMyRule`)

### Category Naming

- **Script rules**: `CustomScript[Description]Rule` (e.g., `CustomScriptCommentRule`)
- **Structure rules**: `CustomStructure[Description]Rule` (e.g., `CustomStructureValidationRule`)
- **Endpoint rules**: `CustomEndpoint[Description]Rule` (e.g., `CustomEndpointSecurityRule`)
- **PMD rules**: `CustomPMD[Description]Rule` (e.g., `CustomPMDOrganizationRule`)

## 📝 Creating a Custom Rule

### 1. Rule Structure (Unified Architecture)

Arcane Auditor now supports a **unified rule architecture** with specialized base classes:

#### For Script Rules (Recommended)
```python
from typing import Generator
from ...script.shared import ScriptRuleBase, ScriptDetector, Violation
from ....models import ProjectContext, PMDModel, ScriptModel

class CustomScriptMyRule(ScriptRuleBase):
    """Custom script rule using unified architecture."""
    
    DESCRIPTION = "Description of what this rule checks"
    SEVERITY = "WARNING"  # "ERROR", "WARNING", "INFO"
    
    def analyze(self, context: ProjectContext) -> Generator[Violation, None, None]:
        """Main analysis method using unified architecture."""
        # The base class handles PMD/POD/script iteration automatically
        yield from self._analyze_scripts(context)
    
    def _analyze_scripts(self, context: ProjectContext) -> Generator[Violation, None, None]:
        """Analyze scripts using the unified pattern."""
        # Your analysis logic here
        pass
```

#### For Structure Rules (Recommended)
```python
from typing import Generator
from ...structure.shared import StructureRuleBase
from ....models import ProjectContext, PMDModel, PodModel

class CustomStructureMyRule(StructureRuleBase):
    """Custom structure rule using unified architecture."""
    
    DESCRIPTION = "Description of what this rule checks"
    SEVERITY = "WARNING"
    
    def get_description(self) -> str:
        """Required by StructureRuleBase."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model."""
        # Your PMD analysis logic here
        pass
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model."""
        # Your POD analysis logic here
        pass
```


### Benefits of Unified Architecture

**Why use the unified architecture?**

- ✅ **Consistency**: All rules follow the same patterns and conventions
- ✅ **Reusability**: Common functionality is abstracted into base classes
- ✅ **Maintainability**: Easier to understand and modify rules
- ✅ **Testability**: Clear separation of concerns makes testing easier
- ✅ **Extensibility**: New rules can easily inherit from base classes
- ✅ **Performance**: Built-in optimizations and caching
- ✅ **Future-proof**: Architecture evolves with the platform

**When to use each approach:**

- **Use `ScriptRuleBase`** for script analysis rules (recommended)
- **Use `StructureRuleBase`** for PMD/POD structure validation (recommended)

### 2. Excluding Example Rules

If you create example rules for demonstration purposes, exclude them from automatic discovery:

```python
class MyExampleRule(ScriptRuleBase):
    """Example rule for demonstration purposes."""
    
    IS_EXAMPLE = True  # This flag excludes the rule from automatic discovery
    
    DESCRIPTION = "This is just an example"
    SEVERITY = "INFO"
    
    def analyze(self, context: ProjectContext) -> Generator[Violation, None, None]:
        return  # Example rule - no actual analysis
        yield  # Make it a generator
```

**Benefits of using `IS_EXAMPLE = True`:**
- ✅ Example rules won't run during normal analysis
- ✅ Keeps example code visible for reference
- ✅ Prevents confusion with production rules
- ✅ Allows sharing example code without side effects

### 3. Rule Categories

#### Script Rules (Comprehensive Analysis)

Script rules analyze scripts across **all supported file types** (PMD embedded scripts, standalone `.script` files, and more):

```python
class CustomScriptSecurityRule(ScriptRuleBase):
    """Example script rule using unified architecture."""
    
    DESCRIPTION = "Ensures scripts follow security best practices"
    SEVERITY = "ERROR"
    
    def analyze(self, context: ProjectContext) -> Generator[Violation, None, None]:
        # Use the unified architecture - base class handles iteration
        yield from self._analyze_scripts(context)
    
    def _analyze_scripts(self, context: ProjectContext) -> Generator[Violation, None, None]:
        """Analyze scripts using the unified architecture."""
        # The ScriptRuleBase automatically calls this method for each script
        # Your analysis logic here
        pass
    
    def _check_security(self, script_content: str, field_name: str, file_path: str, line_offset: int) -> Generator[Violation, None, None]:
        # Your security analysis logic here
        if "eval(" in script_content:  # Example security check
            yield Violation(
                rule=self,
                message="Use of eval() is dangerous and should be avoided",
                line=line_offset,
                column=1,
                file_path=file_path
            )
```

#### Structure Rules

For analyzing PMD structure/configuration:

```python
class CustomStructureRule(StructureRuleBase):
    """Example structure rule using unified architecture."""
    
    DESCRIPTION = "Validates PMD structure compliance"
    SEVERITY = "WARNING"
    
    def get_description(self) -> str:
        """Required by StructureRuleBase."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD structure."""
        # Analyze PMD structure (widgets, endpoints, etc.)
        if not pmd_model.presentation:
            yield Finding(
                rule=self,
                message="PMD must have a presentation section",
                line=1,
                column=1,
                file_path=pmd_model.file_path
            )
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't need structure validation for this rule."""
        yield  # Make it a generator
```

#### Endpoint Rules

For analyzing API endpoint configurations:

```python
class CustomEndpointRule(StructureRuleBase):
    """Example endpoint rule using unified architecture."""
    
    DESCRIPTION = "Validates endpoint security configuration"
    SEVERITY = "ERROR"
    
    def get_description(self) -> str:
        """Required by StructureRuleBase."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze endpoint configurations."""
        if pmd_model.endpoints:
            yield from self._analyze_endpoints(pmd_model)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't have endpoints."""
        yield  # Make it a generator
    
    def _analyze_endpoints(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        for endpoint in pmd_model.endpoints:
            if not endpoint.get('failOnStatusCodes'):
                yield Finding(
                    rule=self,
                    message=f"Endpoint '{endpoint.get('name')}' should define failOnStatusCodes for proper error handling",
                    line=1,  # You'd calculate actual line number
                    column=1,
                    file_path=pmd_model.file_path
                )
```

### 4. Creating Violations

```python
# Violation creation with automatic field population
violation = Violation(
    rule=self,  # Rule instance - automatically populates rule_id, severity, description
    message="Detailed description of the issue and how to fix it",
    line=42,  # Line where the issue occurs
    column=8,  # Column where the issue occurs (optional)
    file_path=pmd_model.file_path  # Full file path
)

# The Violation dataclass automatically sets:
# - violation.rule_id = self.__class__.__name__
# - violation.severity = self.SEVERITY  
# - violation.rule_description = self.DESCRIPTION

yield violation  # Yield instead of append
```

## 🔧 Available Utilities

### Script Parsing (Built-in with Caching)

```python
# Parse script content into AST using Lark grammar with context-level caching
try:
    ast = self.get_cached_ast(script_content)
    if ast is None:
        return  # Skip if parsing failed
    # AST is now available for analysis
except Exception as e:
    print(f"Failed to parse script: {e}")
```

**Benefits of the new caching system:**
- ✅ **Performance**: ASTs are cached at the context level, avoiding redundant parsing
- ✅ **Memory efficient**: Only unique script content is parsed and cached
- ✅ **Automatic**: Caching happens transparently - no manual cache management needed
- ✅ **Backward compatible**: Falls back to direct parsing if context is not available

### Script Field Discovery

```python
# Find all script-containing fields in a PMD file
script_fields = self.find_script_fields(pmd_model)

# Returns tuples of (field_path, field_value, field_name, line_offset)
for field_path, field_value, field_name, line_offset in script_fields:
    # field_path: "onLoad" or "endPoints.0.onSend"
    # field_value: The actual script content
    # field_name: Human readable name
    # line_offset: Starting line number in the original file
    pass
```

### Line Number Utilities

```python
from ...line_number_utils import LineNumberUtils

# Find line number of a specific field
line_number = LineNumberUtils.find_field_line_number(pmd_model, field_name, search_value)

# Calculate line offset within script content
actual_line = line_offset + relative_line_in_script
```

### Common Validations

```python
from ...common_validations import (
    validate_lower_camel_case,
    validate_identifier,
    validate_no_reserved_words
)

# Validate naming conventions
if not validate_lower_camel_case(variable_name):
    yield Finding(
        rule=self,
        message=f"Variable '{variable_name}' should use lowerCamelCase naming",
        line=line_number,
        column=1,
        file_path=file_path
    )
```

## 📋 Best Practices

### 1. Error Handling

Always wrap parsing and analysis in try-catch blocks:

```python
def _analyze_script_file(self, script_model: ScriptModel) -> Generator[Finding, None, None]:
    """Analyze standalone script files."""
    try:
        yield from self._check_script_content(script_model.source, script_model.file_path, 1)
    except Exception as e:
        print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")

def _check_script_content(self, script_content: str, file_path: str, line_offset: int) -> Generator[Finding, None, None]:
    """Check script content with proper error handling."""
    try:
        ast = self.get_cached_ast(script_content)
        if ast is None:
            return  # Skip if parsing failed
        # Your analysis logic here
    except Exception as e:
        print(f"Error parsing script in {file_path}: {e}")
        return  # Exit gracefully
```

### 2. Comprehensive Script Analysis Pattern

Always implement analysis for all script-containing file types:

```python
def analyze(self, context: ProjectContext) -> Generator[Violation, None, None]:
    """Standard comprehensive analysis pattern using unified architecture."""
    # Use the unified architecture - base class handles iteration
    yield from self._analyze_scripts(context)
```

### 3. Performance

- Use generators (`yield`) instead of building large lists
- Avoid parsing the same content multiple times
- Cache expensive computations when possible
- Use efficient data structures for large files

### 4. Configuration Support

Support rule configuration through custom_settings:

```python
class CustomScriptComplexityRule(ScriptRuleBase):
    """Configurable complexity rule using unified architecture."""
    
    def __init__(self, config: dict = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        self.max_complexity = self.config.get('max_complexity', 10)
    
    DESCRIPTION = "Validates script complexity doesn't exceed threshold"
    SEVERITY = "WARNING"
    
    def analyze(self, context: ProjectContext) -> Generator[Violation, None, None]:
        # Use the unified architecture - base class handles iteration
        yield from self._analyze_scripts(context)
    
    def _analyze_scripts(self, context: ProjectContext) -> Generator[Violation, None, None]:
        """Analyze scripts using the unified architecture."""
        # Use self.max_complexity in your analysis
        pass
```

### 5. Documentation

- Include clear rule descriptions
- Provide helpful error messages with solutions
- Add examples in your rule's docstring
- Document any configuration options

### 6. Testing

- Test your rules with various PMD files
- Include edge cases (empty files, malformed content)
- Test both PMD embedded and standalone script analysis
- Verify rule class names don't conflict with existing rules

## 🚀 Getting Started

### Quick Start Steps

1. **Copy the example**: Start with `examples/_example_custom_rule.py`
2. **Update the structure**: Use the generator-based pattern
3. **Implement comprehensive analysis**: Support all script-containing file types
4. **Add your logic**: Implement your specific validation
5. **Place in user/**: Move your rule to `user/` directory
6. **Test**: Run the tool to see your rule in action
7. **Configure**: Add rule to your configuration files

### Example: Creating a Custom Comment Rule

```python
# user/my_comment_rule.py
from typing import Generator
from ...script.shared import ScriptRuleBase, Violation
from ....models import ProjectContext

class CustomScriptCommentRule(ScriptRuleBase):
    """Ensures functions have adequate comments using unified architecture."""
    
    DESCRIPTION = "Functions should have comments for maintainability"
    SEVERITY = "INFO"
    
    def analyze(self, context: ProjectContext) -> Generator[Violation, None, None]:
        # Use the unified architecture - base class handles iteration
        yield from self._analyze_scripts(context)
    
    def _analyze_scripts(self, context: ProjectContext) -> Generator[Violation, None, None]:
        """Analyze scripts using the unified architecture."""
        # The ScriptRuleBase automatically calls this method for each script
        # Your analysis logic here
        pass
    
    def _check_comments(self, script_content: str, field_name: str, file_path: str, line_offset: int) -> Generator[Violation, None, None]:
        """Check for adequate comments in script content."""
        try:
            lines = script_content.split('\n')
            function_lines = [i for i, line in enumerate(lines) if 'function' in line]
            
            for func_line in function_lines:
                # Simple check: look for comment within 3 lines before function
                has_comment = any('//' in lines[max(0, func_line-i)] or '/*' in lines[max(0, func_line-i)] 
                                for i in range(1, 4) if func_line-i >= 0)
                
                if not has_comment:
                    yield Violation(
                        rule=self,
                        message="Function should have a comment explaining its purpose",
                        line=line_offset + func_line,
                        column=1,
                        file_path=file_path
                    )
        except Exception as e:
            print(f"Error analyzing comments in {file_path}: {e}")
```

## 🔍 Debugging

### Check Rule Discovery

Your rules should appear in the discovery output:

```bash
uv run main.py review-app samples/archives/template_bad_nkhlsq.zip

# Look for:
# Discovered rule: CustomScriptCommentRule
```

### List All Rules

```bash
uv run main.py list-rules

# Your custom rule should appear in the output
```

### Test with Sample Files

```bash
# Test with provided samples
uv run main.py review-app samples/archives/template_bad_nkhlsq.zip

# Test with specific configuration
uv run main.py review-app samples/archives/template_bad_nkhlsq.zip --config user_configs/my-config.json
```

### Common Issues

- **Rule not discovered**: Check `__init__.py` files exist in all directories
- **Import errors**: Verify import paths are correct (use relative imports)
- **Parse errors**: Add try-catch blocks around script parsing
- **Generator errors**: Make sure to use `yield` instead of `return` for violations
- **Missing script analysis**: Use the unified architecture with `ScriptRuleBase` for automatic script analysis
- **Class name conflicts**: Ensure unique class names with `Custom` prefix

## 📚 Examples

### Complete Working Example

See `examples/_example_custom_rule.py` for a complete implementation showing:

- Unified rule architecture with ScriptRuleBase
- Generator-based rule structure
- Comprehensive script analysis (all supported file types)
- Proper error handling
- AST parsing and analysis
- Violation generation with automatic field population

### Configuration Integration

Add your custom rule to configuration files:

```json
// user_configs/my-config.json
{
  "rules": {
    "CustomScriptCommentRule": {
      "enabled": true,
      "severity_override": "WARNING",
      "custom_settings": {
        "min_comment_ratio": 0.2
      }
    }
  }
}
```

## 🤝 Contributing Back

If you create useful custom rules, consider:

- **Sharing with the community** - Post in discussions or issues
- **Proposing as official rules** - Submit pull requests
- **Contributing to the main codebase** - Help improve the platform
- **Creating rule templates** - Help other developers get started


**Happy mystical rule development! 🔮✨**

*The Arcane Auditor's power grows with each custom rule you create!*