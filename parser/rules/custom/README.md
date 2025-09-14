# Custom Rules Development Guide

This directory allows you to create custom validation rules for the Extend Reviewer without modifying the official codebase. This is perfect for:

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

### Rule IDs
- **Official rules**: Use descriptive class names (e.g., `ScriptVarUsageRule`, `WidgetIdRequiredRule`)
- **Custom rules**: Use descriptive class names with `Custom` prefix (e.g., `CustomScriptMyRule`)

### Class Names
- **Script rules**: `CustomScript[Description]Rule` (e.g., `CustomScriptNamingRule`)
- **Structure rules**: `CustomStructure[Description]Rule` (e.g., `CustomStructureValidationRule`)

## 📝 Creating a Custom Rule

### 1. Basic Structure

```python
from ...base import Rule, Finding
from ..models import ProjectContext, PMDModel
from typing import List

class CustomScriptMyRule(Rule):
    def __init__(self):
        super().__init__()
        self.ID = "RULE000"  # Base class default
        self.SEVERITY = "WARNING"   # ERROR, WARNING, INFO
        self.DESCRIPTION = "Description of what this rule checks"
    
    def analyze(self, context: ProjectContext) -> List[Finding]:
        """Main analysis method - required by all rules."""
        findings = []
        
        for pmd_file in context.pmds.values():
            # Your analysis logic here
            pass
        
        return findings
```

### 2. Excluding Example Rules

If you create example rules for demonstration purposes, you can exclude them from automatic discovery:

```python
class MyExampleRule(Rule):
    """Example rule for demonstration purposes."""
    
    IS_EXAMPLE = True  # This flag excludes the rule from automatic discovery
    
    def __init__(self):
        super().__init__()
        self.ID = "RULE000"  # Base class default
        self.SEVERITY = "INFO"
        self.DESCRIPTION = "This is just an example"
    
    def analyze(self, context: ProjectContext) -> List[Finding]:
        return []  # Example rule - no actual analysis
```

**Benefits of using `IS_EXAMPLE = True`:**
- ✅ Example rules won't run during normal analysis
- ✅ Keeps example code visible for reference
- ✅ Prevents confusion with production rules
- ✅ Allows sharing example code without side effects

### 3. Rule Types

#### Script Rules
For analyzing PMD Script content:

```python
def analyze(self, context: ProjectContext) -> List[Finding]:
    findings = []
    
    for pmd_file in context.pmds.values():
        if pmd_file.script:
            # Parse script content
            script_ast = self._parse_script_content(pmd_file.script)
            
            # Analyze the AST
            findings.extend(self._analyze_script_ast(script_ast, pmd_file))
    
    return findings
```

#### Structure Rules
For analyzing PMD structure/configuration:

```python
def analyze(self, context: ProjectContext) -> List[Finding]:
    findings = []
    
    for pmd_file in context.pmds.values():
        # Analyze PMD structure (widgets, endpoints, etc.)
        findings.extend(self._analyze_pmd_structure(pmd_file))
    
    return findings
```

### 3. Creating Findings

```python
finding = Finding(
    rule=self,  # Pass the rule instance
    message="Detailed description of the issue and how to fix it",
    line=42,  # Line where the issue occurs
    column=8,  # Column where the issue occurs
    file_path=pmd_file.file_path
)
findings.append(finding)
```

## 🔧 Available Utilities

### Script Parsing
```python
# Parse script content into AST
script_ast = self._parse_script_content(pmd_file.script_content)

# Strip PMD wrapper syntax
clean_script = self._strip_pmd_wrappers(pmd_file.script_content)

# Find script fields in PMD
script_fields = self.find_script_fields(pmd_file)
```

### Line Number Calculation
```python
from ...line_number_utils import LineNumberUtils

line_number = LineNumberUtils.get_line_number(
    pmd_file.script_content, 
    violation_position
)
```

### Common Validations
```python
from ...common_validations import validate_lower_camel_case

if not validate_lower_camel_case(variable_name):
    # Handle naming violation
    pass
```

## 📋 Best Practices

### 1. Error Handling
Always wrap parsing and analysis in try-catch blocks:

```python
try:
    script_ast = self._parse_script_content(pmd_file.script_content)
    # Your analysis here
except Exception as e:
    print(f"Error analyzing {pmd_file.file_path}: {e}")
    # Return empty findings list or log the error
```

### 2. Performance
- Avoid parsing the same content multiple times
- Cache expensive computations when possible
- Use efficient data structures for large files

### 3. Documentation
- Include clear rule descriptions
- Provide helpful error messages
- Add examples in your rule's docstring

### 4. Testing
- Test your rules with various PMD files
- Include edge cases (empty files, malformed content)
- Verify rule IDs don't conflict with existing rules

## 🚀 Getting Started

1. **Copy the example**: Start with `examples/example_custom_rule.py`
2. **Modify the rule**: Change the rule ID, logic, and description
3. **Place in user/**: Move your rule to `user/` directory
4. **Test**: Run the tool to see your rule in action
5. **Share**: Commit your custom rules to version control

## 🔍 Debugging

### Check Rule Discovery
Your rules should appear in the discovery output:
```
Discovered rule: CustomScriptMyRule
```

### Test with Sample Files
```bash
uv run main.py review-app sample_extend_code/template_bad_nkhlsq.zip
```

### Common Issues
- **Rule not discovered**: Check `__init__.py` files exist
- **Import errors**: Verify import paths are correct
- **Parse errors**: Add try-catch blocks around parsing
- **ID conflicts**: Ensure unique class names

## 📚 Examples

See `examples/example_custom_rule.py` for a complete implementation showing:
- Rule structure and initialization
- Script content parsing
- AST analysis
- Finding generation
- Error handling

## 🤝 Contributing Back

If you create useful custom rules, consider:
- Sharing them with the community
- Proposing them as official rules
- Contributing to the main codebase

---

**Happy rule development! 🎉**
