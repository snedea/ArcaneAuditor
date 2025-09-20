# Custom Rules Development Guide 🧙‍♂️

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

### 1. Modern Rule Structure (Generator-Based)

**Current Architecture (2025):**
```python
from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, ScriptModel

class CustomScriptMyRule(Rule):
    """Custom rule description."""
    
    DESCRIPTION = "Description of what this rule checks"
    SEVERITY = "WARNING"  # "ERROR", "WARNING", "INFO"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Main analysis method - yields findings as they're discovered."""
        
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_scripts(pmd_model)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model)
    
    def _analyze_pmd_scripts(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze script content within PMD files."""
        script_fields = self.find_script_fields(pmd_model)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and len(field_value.strip()) > 0:
                yield from self._check_script_content(field_value, field_name, pmd_model.file_path, line_offset)
    
    def _analyze_script_file(self, script_model: ScriptModel) -> Generator[Finding, None, None]:
        """Analyze standalone script files."""
        try:
            yield from self._check_script_content(script_model.source, "script", script_model.file_path, 1)
        except Exception as e:
            print(f"Warning: Failed to analyze script file {script_model.file_path}: {e}")
    
    def _check_script_content(self, script_content: str, field_name: str, file_path: str, line_offset: int) -> Generator[Finding, None, None]:
        """Your analysis logic here."""
        try:
            # Parse script using built-in parser
            ast = self._parse_script_content(script_content)
            
            # Your analysis logic here
            if self._has_violation(ast):
                yield Finding(
                    rule=self,
                    message="Description of the issue and how to fix it",
                    line=line_offset + violation_line,
                    column=1,
                    file_path=file_path
                )
        except Exception as e:
            print(f"Error parsing script in {file_path}: {e}")
```

### 2. Key Architectural Changes

**⚠️ Important Updates from Previous Versions:**

1. **Generator-Based:** Rules now use `Generator[Finding, None, None]` instead of `List[Finding]`
2. **Dual Script Analysis:** Modern rules analyze both PMD embedded scripts AND standalone `.script` files
3. **Automatic Field Discovery:** Use `self.find_script_fields()` for PMD script field detection
4. **Built-in Parsing:** Use `self._parse_script_content()` for AST parsing
5. **Error Handling:** Always wrap parsing in try-catch blocks

### 3. Excluding Example Rules

If you create example rules for demonstration purposes, exclude them from automatic discovery:

```python
class MyExampleRule(Rule):
    """Example rule for demonstration purposes."""
    
    IS_EXAMPLE = True  # This flag excludes the rule from automatic discovery
    
    DESCRIPTION = "This is just an example"
    SEVERITY = "INFO"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        return  # Example rule - no actual analysis
        yield  # Make it a generator
```

**Benefits of using `IS_EXAMPLE = True`:**
- ✅ Example rules won't run during normal analysis
- ✅ Keeps example code visible for reference
- ✅ Prevents confusion with production rules
- ✅ Allows sharing example code without side effects

### 4. Rule Categories

#### Script Rules (Dual Analysis)

Modern script rules analyze **both** PMD embedded scripts and standalone `.script` files:

```python
class CustomScriptSecurityRule(Rule):
    """Example script rule with dual analysis."""
    
    DESCRIPTION = "Ensures scripts follow security best practices"
    SEVERITY = "ERROR"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        # Analyze PMD embedded scripts (onLoad, script, onSubmit, etc.)
        for pmd_model in context.pmds.values():
            script_fields = self.find_script_fields(pmd_model)
            for field_path, field_value, field_name, line_offset in script_fields:
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_security(field_value, pmd_model.file_path, line_offset)
        
        # Analyze standalone script files (util.script, helper.script, etc.)
        for script_model in context.scripts.values():
            yield from self._check_security(script_model.source, script_model.file_path, 1)
    
    def _check_security(self, script_content: str, file_path: str, line_offset: int) -> Generator[Finding, None, None]:
        # Your security analysis logic here
        if "eval(" in script_content:  # Example security check
            yield Finding(
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
class CustomStructureRule(Rule):
    """Example structure rule."""
    
    DESCRIPTION = "Validates PMD structure compliance"
    SEVERITY = "WARNING"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_structure(pmd_model)
    
    def _analyze_pmd_structure(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        # Analyze PMD structure (widgets, endpoints, etc.)
        if not pmd_model.presentation:
            yield Finding(
                rule=self,
                message="PMD must have a presentation section",
                line=1,
                column=1,
                file_path=pmd_model.file_path
            )
```

#### Endpoint Rules

For analyzing API endpoint configurations:

```python
class CustomEndpointRule(Rule):
    """Example endpoint rule."""
    
    DESCRIPTION = "Validates endpoint security configuration"
    SEVERITY = "ERROR"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        for pmd_model in context.pmds.values():
            if pmd_model.endpoints:
                yield from self._analyze_endpoints(pmd_model)
    
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

### 5. Creating Findings (Modern Pattern)

```python
# Modern Finding creation with automatic field population
finding = Finding(
    rule=self,  # Rule instance - automatically populates rule_id, severity, description
    message="Detailed description of the issue and how to fix it",
    line=42,  # Line where the issue occurs
    column=8,  # Column where the issue occurs (optional)
    file_path=pmd_model.file_path  # Full file path
)

# The Finding dataclass automatically sets:
# - finding.rule_id = self.__class__.__name__
# - finding.severity = self.SEVERITY  
# - finding.rule_description = self.DESCRIPTION

yield finding  # Yield instead of append
```

## 🔧 Available Utilities

### Script Parsing (Built-in)

```python
# Parse script content into AST using Lark grammar
try:
    ast = self._parse_script_content(script_content)
    # AST is now available for analysis
except Exception as e:
    print(f"Failed to parse script: {e}")
```

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

### 1. Modern Error Handling

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
        ast = self._parse_script_content(script_content)
        # Your analysis logic here
    except Exception as e:
        print(f"Error parsing script in {file_path}: {e}")
        return  # Exit gracefully
```

### 2. Dual Script Analysis Pattern

Always implement both PMD and standalone script analysis:

```python
def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
    """Standard dual analysis pattern."""
    # PMD embedded scripts
    for pmd_model in context.pmds.values():
        yield from self._analyze_pmd_scripts(pmd_model)
    
    # Standalone script files  
    for script_model in context.scripts.values():
        yield from self._analyze_script_file(script_model)
```

### 3. Performance

- Use generators (`yield`) instead of building large lists
- Avoid parsing the same content multiple times
- Cache expensive computations when possible
- Use efficient data structures for large files

### 4. Configuration Support

Support rule configuration through custom_settings:

```python
class CustomScriptComplexityRule(Rule):
    """Configurable complexity rule."""
    
    def __init__(self, config: dict = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        self.max_complexity = self.config.get('max_complexity', 10)
    
    DESCRIPTION = "Validates script complexity doesn't exceed threshold"
    SEVERITY = "WARNING"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
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
2. **Update the structure**: Use the modern generator-based pattern
3. **Implement dual analysis**: Support both PMD and standalone scripts
4. **Add your logic**: Implement your specific validation
5. **Place in user/**: Move your rule to `user/` directory
6. **Test**: Run the tool to see your rule in action
7. **Configure**: Add rule to your configuration files

### Example: Creating a Custom Comment Rule

```python
# user/my_comment_rule.py
from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel, ScriptModel

class CustomScriptCommentRule(Rule):
    """Ensures functions have adequate comments."""
    
    DESCRIPTION = "Functions should have comments for maintainability"
    SEVERITY = "INFO"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        # Analyze PMD embedded scripts
        for pmd_model in context.pmds.values():
            script_fields = self.find_script_fields(pmd_model)
            for field_path, field_value, field_name, line_offset in script_fields:
                if field_value and len(field_value.strip()) > 0:
                    yield from self._check_comments(field_value, pmd_model.file_path, line_offset)
        
        # Analyze standalone script files
        for script_model in context.scripts.values():
            yield from self._check_comments(script_model.source, script_model.file_path, 1)
    
    def _check_comments(self, script_content: str, file_path: str, line_offset: int) -> Generator[Finding, None, None]:
        """Check for adequate comments in script content."""
        try:
            lines = script_content.split('\n')
            function_lines = [i for i, line in enumerate(lines) if 'function' in line]
            
            for func_line in function_lines:
                # Simple check: look for comment within 3 lines before function
                has_comment = any('//' in lines[max(0, func_line-i)] or '/*' in lines[max(0, func_line-i)] 
                                for i in range(1, 4) if func_line-i >= 0)
                
                if not has_comment:
                    yield Finding(
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
- **Parse errors**: Add try-catch blocks around `_parse_script_content()`
- **Generator errors**: Make sure to use `yield` instead of `return` for findings
- **Missing script analysis**: Ensure you implement both PMD and standalone script analysis
- **Class name conflicts**: Ensure unique class names with `Custom` prefix

## 📚 Examples

### Complete Working Example

See `examples/_example_custom_rule.py` for a complete implementation showing:

- Modern generator-based rule structure
- Dual script analysis (PMD + standalone)
- Proper error handling
- AST parsing and analysis
- Finding generation with automatic field population

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


**Happy mystical rule development! 🧙‍♂️✨**

*The Arcane Auditor's power grows with each custom rule you create!*