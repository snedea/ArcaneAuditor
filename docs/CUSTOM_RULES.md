# Custom Rules Development Guide 🔮

*Create mystical validation rules for the Arcane Auditor*

This document pairs with the [Arcane Auditor Rules Grimoire](RULES.md), which defines the official rule set — this guide empowers you to forge your own.

This directory allows you to create custom validation rules for the Arcane Auditor without modifying the official codebase. This is perfect for:

- **Adding organization-specific rules**
- **Extending functionality** without waiting for official releases
- **Sharing custom rules** with your team or community
- **Avoiding conflicts** when updating the main tool

## 🏗️ Class Hierarchy

```
Rule (Abstract Base)
 ├── ScriptRuleBase (for script analysis)
 │     ├── Uses → ScriptDetector (for AST detection logic)
 │     │            └── CustomScriptMyDetector
 │     └── CustomScriptMyRule
 └── StructureRuleBase (for structure validation)
       └── CustomStructureMyRule
```

**Architecture Pattern:**

- **Rules** (ScriptRuleBase, StructureRuleBase): Orchestrate analysis, handle file iteration
- **Detectors** (ScriptDetector): Analyze AST and detect patterns
- **Separation**: Rules coordinate, Detectors detect

## 📊 When to Use Violation vs Finding

| Output Type         | Use When                      | Description                                                       |
| ------------------- | ----------------------------- | ----------------------------------------------------------------- |
| **Violation** | Raw script ASTs (detectors)   | Lower-level rule implementation working directly with parsed code |
| **Finding**   | Higher rule-level integration | Validation and reporting at the rule engine level                 |

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

#### For Script Rules (Two Valid Patterns)

**Pattern 1: Detector Pattern (Recommended for AST-based analysis)**

The detector pattern separates AST detection logic from rule orchestration and is recommended for most script analysis:

```python
from typing import Generator, List
from lark import Tree
from ...script.shared import ScriptRuleBase, ScriptDetector, Violation
from ...base import Finding

# Step 1: Create a Detector (handles AST parsing and detection logic)
class MyScriptDetector(ScriptDetector):
    """Detector for specific pattern in AST."""
  
    def detect(self, ast: Tree, field_name: str = "") -> List[Violation]:
        """Analyze AST and return violations."""
        violations = []
      
        # Traverse the AST to find patterns
        for node in ast.find_data('some_ast_node_type'):
            line_number = self.get_line_from_tree_node(node)
            violations.append(Violation(
                message=f"Found issue in {field_name}",
                line=line_number
            ))
      
        return violations

# Step 2: Create a Rule (orchestrates detector usage)
class CustomScriptMyRule(ScriptRuleBase):
    """Custom script rule using detector pattern."""
  
    DESCRIPTION = "Description of what this rule checks"
    SEVERITY = "ADVICE"  # "ACTION", "ADVICE"
    DETECTOR = MyScriptDetector  # Reference to your detector class
  
    def get_description(self) -> str:
        return self.DESCRIPTION
  
    # The base class automatically:
    # - Iterates through PMD/POD/Script files
    # - Parses script content into AST
    # - Calls your DETECTOR with the AST
    # - Converts Violations to Findings
```

**Why use the Detector pattern?**

- ✅ Separation of concerns (AST logic vs orchestration)
- ✅ Reusable detectors across multiple rules
- ✅ Comments automatically ignored by parser
- ✅ Consistent with most official script rules
- ✅ Easier to test (test detector and rule separately)

**Pattern 2: Custom Analysis Pattern (For complex logic)**

Some rules implement custom `analyze()` methods for complex logic that doesn't fit the detector pattern:

```python
class CustomScriptComplexRule(ScriptRuleBase):
    """Custom rule with complex analysis logic."""
  
    DESCRIPTION = "Complex analysis that doesn't fit detector pattern"
    SEVERITY = "ADVICE"
  
    def get_description(self) -> str:
        return self.DESCRIPTION
  
    def analyze(self, context) -> Generator[Finding, None, None]:
        """Custom analysis implementation."""
        # Your custom analysis logic here
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_custom(pmd_model, context)
  
    def _analyze_pmd_custom(self, pmd_model, context):
        """Custom PMD analysis logic."""
        # Complex analysis that doesn't fit detector pattern
        pass
```

**When to use each pattern:**

- **Use Detector Pattern**: For AST-based analysis, syntax checking, code quality rules
- **Use Custom Analysis**: For complex business logic, cross-file analysis, or when detector pattern doesn't fit

#### For Structure Rules (Recommended)

```python
from typing import Generator
from ...structure.shared import StructureRuleBase
from ....models import ProjectContext, PMDModel, PodModel

class CustomStructureMyRule(StructureRuleBase):
    """Custom structure rule using unified architecture."""
  
    DESCRIPTION = "Description of what this rule checks"
    SEVERITY = "ADVICE"
  
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
    SEVERITY = "ADVICE"
  
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
    SEVERITY = "ACTION"
  
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
                message="Use of eval() is dangerous and should be avoided",
                line=line_offset
            )
```

#### Structure Rules

For analyzing PMD structure/configuration:

```python
class CustomStructureRule(StructureRuleBase):
    """Example structure rule using unified architecture."""
  
    DESCRIPTION = "Validates PMD structure compliance"
    SEVERITY = "ADVICE"
  
    def get_description(self) -> str:
        """Required by StructureRuleBase."""
        return self.DESCRIPTION
  
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD structure."""
        # Analyze PMD structure (widgets, endpoints, etc.)
        if not pmd_model.presentation:
            # Use unified line calculation method for consistency
            line_number = self.get_section_line_number(pmd_model, 'presentation')
            yield Finding(
                rule=self,
                message="PMD must have a presentation section",
                line=line_number,
                file_path=pmd_model.file_path
            )
  
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't need structure validation for this rule."""
        yield  # Make it a generator
```

### Unified Line Calculation Methods

**StructureRuleBase** now provides unified line calculation methods for consistent and reliable line number detection:

#### Field Line Numbers

```python
# Get line number for a specific field with a specific value
line_number = self.get_field_line_number(model, 'name', 'myEndpoint')
line_number = self.get_field_line_number(model, 'id', 'myWidget')
```

#### Section Line Numbers

```python
# Get line number for a specific section
line_number = self.get_section_line_number(model, 'footer')
line_number = self.get_section_line_number(model, 'presentation')
```

#### Field After Entity Line Numbers

```python
# Get line number for a field that appears after a specific entity
line_number = self.get_field_after_entity_line_number(model, 'name', 'myEndpoint', 'url')
line_number = self.get_field_after_entity_line_number(model, 'name', 'myEndpoint', 'failOnStatusCodes')
```

#### Pattern Search Line Numbers

```python
# Find line number where a pattern appears in source content
line_number = self.find_pattern_line_number(model, 'hardcoded_value', case_sensitive=False)
line_number = self.find_pattern_line_number(model, 'data:image/', case_sensitive=True)
```

#### Text Position Line Numbers

```python
# Get line number from a text position (character offset)
line_number = self.get_line_from_text_position(text, match.start())
```

#### Widget Path Helpers

```python
# Extract nearest container from widget path for context-aware line numbers
# Works with any nested structure: cellTemplate, primaryLayout, sections, items, etc.
container = self.extract_nearest_container_from_path("body.children.1.columns.0.cellTemplate")
# Returns: "cellTemplate"

# Find where a specific container field appears in source
context_line = self.find_context_line(lines, "cellTemplate", start_line, end_line)
# Returns: line index where "cellTemplate" field is found

# Usage example:
if container:
    context_line = self.find_context_line(lines, container, search_start, search_end)
    if context_line >= 0:
        # Narrow search to area near the container
        search_start = context_line
        search_end = context_line + 20
```

**Benefits:**

- ✅ **Consistent**: All structure rules use the same reliable methods
- ✅ **Maintainable**: Single source of truth for line calculation logic
- ✅ **DRY**: Eliminates code duplication across rules
- ✅ **Reliable**: Handles edge cases and errors gracefully
- ✅ **Generic**: Works with any container field (no hardcoded field names)

#### Widget Traversal Methods

**StructureRuleBase** provides methods to traverse widget structures in PMD and POD files:

```python
# Traverse all widgets in a PMD presentation structure
for widget, path, index in self.traverse_presentation_structure(section_data, section_name):
    # widget: The widget dictionary
    # path: Technical path like "body.children.1.columns.0.cellTemplate"
    # index: Array index if widget is in a list
  
    widget_type = widget.get('type')
    widget_id = widget.get('id')
    # Analyze the widget...

# Find all widgets in a POD template
widgets = self.find_pod_widgets(pod_model)
for widget_path, widget_data in widgets:
    # widget_path: Path to the widget
    # widget_data: The widget dictionary
    # Analyze the widget...
```

**Supported Container Fields:**
The traversal automatically handles these containers: `children`, `primaryLayout`, `secondaryLayout`, `sections`, `items`, `navigationTasks`, `cellTemplate`, `columns`

**Example: Checking All Widgets**

```python
def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
    if not pmd_model.presentation:
        return
  
    # Traverse all presentation sections
    presentation_dict = pmd_model.presentation.__dict__
    for section_name, section_data in presentation_dict.items():
        if isinstance(section_data, dict):
            for widget, path, index in self.traverse_presentation_structure(section_data, section_name):
                # Check each widget (including nested ones in cellTemplate, columns, etc.)
                if widget.get('type') == 'grid':
                    yield from self._check_grid_widget(widget, pmd_model, path)
```

#### Endpoint Rules

For analyzing API endpoint configurations:

```python
class CustomEndpointRule(StructureRuleBase):
    """Example endpoint rule using unified architecture."""
  
    DESCRIPTION = "Validates endpoint security configuration"
    SEVERITY = "ACTION"
  
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
                    file_path=pmd_model.file_path
                )
```

### 4. Creating Violations and Findings

```python
# For Script Detectors: Create Violations (internal format)
violation = Violation(
    message="Detailed description of the issue and how to fix it",
    line=42,  # Line number (hash-based, exact positioning)
    metadata={'variable_name': 'myVar'}  # Optional metadata
)

# For Rules: Create Findings (external format)
finding = Finding(
    rule=self,  # Automatically populates rule_id, severity, description
    message="Detailed description of the issue and how to fix it",
    line=42,  # Line number from hash-based lookup (exact, no off-by-one errors)
    file_path=file_path
)

yield finding  # Always yield, never return
```

**Line Number Accuracy:**

- Line numbers use hash-based mapping for exact accuracy
- No off-by-one errors
- `line_offset` from `find_script_fields()` is already calculated correctly
- Handles multiline scripts, string concatenations, and nested structures

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

**Caching System Benefits:**

- ✅ **Performance**: ASTs are cached at the context level, avoiding redundant parsing
- ✅ **Memory efficient**: Only unique script content is parsed and cached
- ✅ **Automatic**: Caching happens transparently - no manual cache management needed
- ✅ **Backward compatible**: Falls back to direct parsing if context is not available

### ScriptDetector Helper Methods

**ScriptDetector** base class provides helper methods for AST analysis:

```python
class MyScriptDetector(ScriptDetector):
    def detect(self, ast: Tree, field_name: str = "") -> List[Violation]:
        violations = []
      
        # Get line number from AST node
        line_number = self.get_line_from_tree_node(node)
      
        # Get function context for a node (which function contains this node)
        function_name = self.get_function_context_for_node(node, ast)
      
        # Extract variable name from various node types
        var_name = self._extract_variable_from_node(node)
      
        # Your detection logic...
        return violations
```

**Available Helper Methods:**

- `get_line_from_tree_node(node)`: Get line number from any AST node
- `get_function_context_for_node(node, ast)`: Find which function contains a node
- `_extract_variable_from_node(node)`: Extract variable name from identifier nodes

### Script Field Discovery

```python
# Find all script-containing fields in a PMD file
script_fields = self.find_script_fields(pmd_model, context)

# Returns tuples of (field_path, field_value, display_name, line_offset)
for field_path, field_value, display_name, line_offset in script_fields:
    # field_path: "onLoad" or "endPoints.0.onSend" (technical path)
    # field_value: The actual script content
    # display_name: Human-readable path with widget identifiers
    #   - Uses id -> label -> type -> name priority
    #   - Example: "presentation->tabs->id: sectionOverview->children->label: Timing->children->id: startDateWidget->onChange"
    # line_offset: Starting line number in the original file (hash-based, exact)
    pass
```

**Readable Widget Paths:**

- Widget paths use identifiers instead of array indices
- Priority order: `id` → `label` → `type` → `name` → `[index]`
- Makes violation messages much easier to navigate
- Example:
  - Technical path: `presentation->tabs[0]->children[2]->children[0]->onChange`
  - Readable path: `presentation->tabs->id: sectionOverview->children->label: Timing->children->id: startDateWidget->onChange`

### Line Number Utilities (Hash-Based)

**Line numbers use hash-based mapping for exact accuracy:**

```python
# Get exact line number for script content using hash-based mapping
# The PMDModel now has built-in hash-based line tracking
line_offset = pmd_model.get_script_start_line(script_value)

# Calculate actual line in file (AST line 1 = first line after <%)
# Hash-based mapping handles:
# - Multiline scripts
# - String concatenations
# - Nested structures
# - Duplicate script content
actual_line = line_offset + relative_line_in_ast - 1

# No more off-by-one errors!
# No more fuzzy matching fallbacks (except for edge cases)
```

**Benefits of hash-based line mapping:**

- ✅ Exact line numbers (no approximations)
- ✅ Handles multiline scripts correctly
- ✅ No off-by-one errors
- ✅ Tracks duplicate scripts separately
- ✅ Works with both PMD and POD files

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

### 4. Custom Settings

Enable users to configure your rule through the UI by defining `AVAILABLE_SETTINGS`. This creates a schema-driven form in the configuration interface.

**Schema Format:**

```python
AVAILABLE_SETTINGS = {
    'setting_name': {
        'type': 'int' | 'float' | 'bool' | 'string' | 'list',
        'default': <default_value>,
        'description': 'Human-readable description of what this setting does'
    }
}
```

**Example:**

```python
class CustomScriptComplexityRule(ScriptRuleBase):
    """Configurable complexity rule with custom settings."""
  
    DESCRIPTION = "Validates script complexity doesn't exceed threshold"
    SEVERITY = "ADVICE"
  
    # Define custom settings schema
    AVAILABLE_SETTINGS = {
        'max_complexity': {
            'type': 'int',
            'default': 10,
            'description': 'Maximum cyclomatic complexity allowed'
        },
        'skip_comments': {
            'type': 'bool',
            'default': False,
            'description': 'Skip comment lines when calculating complexity'
        }
    }
  
    def __init__(self, config: dict = None):
        """Initialize with optional configuration."""
        super().__init__()
        self.config = config or {}
        # Settings are automatically applied via apply_settings()
        # Access them in your analysis logic
        self.max_complexity = 10  # Default, will be overridden by config
  
    def apply_settings(self, settings: dict):
        """Apply custom settings from configuration."""
        if 'max_complexity' in settings:
            self.max_complexity = settings['max_complexity']
        if 'skip_comments' in settings:
            self.skip_comments = settings['skip_comments']
  
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        # Use self.max_complexity in your analysis
        yield from self._analyze_scripts(context)
```

**Setting Types:**

- `'int'`: Integer values (e.g., `max_lines: 50`)
- `'float'`: Decimal values (e.g., `threshold: 0.15`)
- `'bool'`: Boolean true/false (e.g., `enabled: true`)
- `'string'`: Text values (e.g., `pattern: "test"`)
- `'list'`: Array of values (e.g., `allowed_names: ["a", "b"]`)

**How It Works:**

1. Define `AVAILABLE_SETTINGS` in your rule class
2. The UI automatically generates a form based on the schema
3. Users configure settings in the configuration interface
4. Settings are passed to your rule via `apply_settings()` method
5. Use the settings in your analysis logic

**Note:** If your rule doesn't support custom configuration, set `AVAILABLE_SETTINGS = {}` (empty dict).

### 5. Grimoire Documentation

Add rich documentation to your rule that appears in the Grimoire (rules documentation UI). This helps users understand why the rule exists, what it catches, and how to fix violations.

**Schema Format:**

```python
DOCUMENTATION = {
    'why': 'Explanation of why this rule matters and its importance',
    'catches': [
        'List item 1 describing what the rule detects',
        'List item 2 with another example',
        'List item 3 with additional context'
    ],
    'examples': '''Markdown-formatted code examples showing violations and fixes:

```javascript
// ❌ Bad example
const bad = example;

// ✅ Good example  
const good = example;
```''',
    'recommendation': 'Advice on how to fix violations or best practices to follow'
}
```

**Example:**

```python
class CustomScriptCommentRule(ScriptRuleBase):
    """Rule with full Grimoire documentation."""
  
    DESCRIPTION = "Functions should have adequate comments"
    SEVERITY = "ADVICE"
  
    DOCUMENTATION = {
        'why': '''Well-commented code is easier to understand and maintain. Comments explain the "why" behind code, making it self-documenting and reducing cognitive load for future maintainers.''',
        'catches': [
            'Functions with low comment density',
            'Long functions without explanatory comments',
            'Functions that require reading implementation to understand purpose'
        ],
        'examples': '''**Example violations:**

```javascript
// ❌ Function without comments
const processPayment = function(amount) {
    const rate = getRate();
    return amount * rate;
};
```

**Fix:**

```javascript
// ✅ Well-commented function
// Process payment with currency conversion
const processPayment = function(amount) {
    // Get current exchange rate
    const rate = getRate();
    // Convert and return
    return amount * rate;
};
```''',
        'recommendation': 'Add comments to explain the purpose and logic flow of functions, especially for complex operations. Comments should explain "why" rather than "what".'
    }
```

**Markdown Support:**

- The `examples` field supports full markdown formatting
- Use code blocks with language tags (e.g., ` ```javascript `)
- Use `**bold**` for emphasis
- Use `❌` and `✅` emojis to mark bad/good examples

**Best Practices:**

- **why**: Explain the business/technical reason the rule exists
- **catches**: Be specific about what patterns trigger violations
- **examples**: Show real-world violations and clear fixes
- **recommendation**: Provide actionable advice, not just descriptions

**Note:** If your rule doesn't have documentation yet, set `DOCUMENTATION = {}` (empty dict). The UI will show "No documentation available" until you add it.

### 6. Documentation Best Practices

- Include clear rule descriptions in `DESCRIPTION`
- Provide helpful error messages with solutions in violation messages
- Add comprehensive `DOCUMENTATION` for the Grimoire
- Document all configuration options in `AVAILABLE_SETTINGS` descriptions

### 6. Testing

- Test your rules with various PMD files
- Include edge cases (empty files, malformed content)
- Test both PMD embedded and standalone script analysis
- Verify rule class names don't conflict with existing rules

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
from ...script.shared import ScriptRuleBase
from ...common import Violation
from ...base import Finding
from ....models import ProjectContext

class CustomScriptCommentRule(ScriptRuleBase):
    """Ensures functions have adequate comments using unified architecture."""
  
    DESCRIPTION = "Functions should have comments for maintainability"
    SEVERITY = "ADVICE"
  
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        Unified analysis pattern with key features:
        - Hash-based line numbers (exact, no off-by-one errors)
        - Context-based AST caching (performance)
        - Readable widget paths (id -> label -> type priority)
        - Clean violation reporting (line numbers only)
        """
        # Iterate through all PMD files and their script fields
        for pmd_model in context.pmds.values():
            script_fields = self.find_script_fields(pmd_model, context)
  
            for field_path, field_value, display_name, line_offset in script_fields:
                # line_offset is hash-based (exact positioning)
                # display_name includes readable widget identifiers
                yield from self._check_comments(
                    field_value, 
                    display_name, 
                    pmd_model.file_path, 
                    line_offset,
                    context
                )
  
    def _check_comments(self, script_content: str, field_name: str, file_path: str, 
                        line_offset: int, context: ProjectContext) -> Generator[Finding, None, None]:
        """Check for adequate comments in script content."""
        try:
            # Use context-based AST caching for performance
            ast = self.get_cached_ast(script_content, context)
            if ast is None:
                return
  
            lines = script_content.split('\n')
            function_lines = [i for i, line in enumerate(lines) if 'function' in line]
  
            for func_line in function_lines:
                # Simple check: look for comment within 3 lines before function
                has_comment = any('//' in lines[max(0, func_line-i)] or '/*' in lines[max(0, func_line-i)] 
                                for i in range(1, 4) if func_line-i >= 0)
  
                if not has_comment:
                    # Create Finding (not Violation - that's for detectors)
                    yield Finding(
                        rule=self,  # Auto-populates rule_id, severity
                        message=f"Function at {field_name} should have a comment explaining its purpose",
                        line=line_offset + func_line,  # Hash-based line numbers are exact
                        file_path=file_path
                    )
        except Exception as e:
            print(f"Error analyzing comments in {file_path}: {e}")
```

**This example demonstrates:**

- ✅ Hash-based line numbers (no off-by-one errors)
- ✅ Context-based AST caching (better performance)
- ✅ Readable widget paths in field_name (easier navigation)
- ✅ Clean violation reporting (line numbers only)
- ✅ Proper architecture (Finding for rules, Violation for detectors)

## 🧠 Context Awareness Integration

### Registering Skipped Checks

When your custom rule depends on files that might not be present, you can register skipped checks to inform users about partial analysis:

```python
from file_processing.context_tracker import SkippedCheck

class CustomStructureMyRule(StructureRuleBase):
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        # Check if required context is available
        if not context.amds:
            # Register a skipped check to inform the user
            context.register_skipped_check(
                SkippedCheck(
                    rule=self.__class__.__name__,
                    reason="Requires AMD file",
                    skipped_checks=["app_id_detection"]
                )
            )
            return  # Skip analysis if context is missing
      
        # Proceed with analysis using available context
        for amd_model in context.amds.values():
            # Your analysis logic here
            pass
```

### Context-Aware Rule Patterns

#### Pattern 1: Graceful Degradation

```python
def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
    # Check for required context
    if not context.smds:
        context.register_skipped_check(
            SkippedCheck(
                rule=self.__class__.__name__,
                reason="Requires SMD file",
                skipped_checks=["security_domain_validation"]
            )
        )
        # Run partial analysis with available data
        yield from self._analyze_without_smd(pmd_model, context)
    else:
        # Run complete analysis
        yield from self._analyze_with_smd(pmd_model, context)
```

#### Pattern 2: Conservative Defaults

```python
def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
    # Use conservative defaults when context is missing
    if not context.amds:
        context.register_skipped_check(
            SkippedCheck(
                rule=self.__class__.__name__,
                reason="Requires AMD file",
                skipped_checks=["app_id_validation"]
            )
        )
        # Assume safe defaults and skip validation
        return
  
    # Proceed with full validation
    app_id = context.application_id
    # Your validation logic here
```

### Context Information Available

The `ProjectContext` provides access to:

- **`context.pmds`**: Dictionary of PMD models
- **`context.pods`**: Dictionary of POD models
- **`context.amds`**: Dictionary of AMD models
- **`context.smds`**: Dictionary of SMD models
- **`context.scripts`**: Dictionary of SCRIPT models
- **`context.application_id`**: Extracted application ID (if AMD present)
- **`context.register_skipped_check()`**: Method to register skipped checks

### Best Practices

1. **Always check for required context** before performing analysis
2. **Register skipped checks** when context is missing
3. **Provide meaningful reasons** for skipped checks
4. **Use conservative defaults** when context is unavailable
5. **Test with partial contexts** to ensure graceful degradation

## 📚 Examples

### Complete Working Example - Script Rule with Detector

Here's a complete real-world example using the detector pattern:

```python
# user/custom_console_detection.py
from typing import List
from lark import Tree
from ...script.shared import ScriptRuleBase, ScriptDetector, Violation
from ...base import Finding

# Step 1: Create Detector (AST detection logic)
class ConsoleUsageDetector(ScriptDetector):
    """Detects console.log, console.error, etc. in scripts."""
  
    def detect(self, ast: Tree, field_name: str = "") -> List[Violation]:
        """Find console usage in AST."""
        violations = []
      
        # Find all member expressions (like console.log)
        for member_expr in ast.find_data('member_dot_expression'):
            if self._is_console_call(member_expr):
                line_number = self.get_line_from_tree_node(member_expr)
                function_context = self.get_function_context_for_node(member_expr, ast)
              
                message = f"Console statement found in {field_name}"
                if function_context:
                    message += f" (function: {function_context})"
              
                violations.append(Violation(
                    message=message,
                    line=line_number
                ))
      
        return violations
  
    def _is_console_call(self, node: Tree) -> bool:
        """Check if node is console.* call."""
        if len(node.children) >= 2:
            obj = node.children[0]
            # Check if object is 'console'
            if (hasattr(obj, 'data') and obj.data == 'identifier_expression' and
                len(obj.children) > 0 and obj.children[0].value == 'console'):
                return True
        return False

# Step 2: Create Rule (orchestration)
class CustomScriptConsoleRule(ScriptRuleBase):
    """Detects console usage in scripts."""
  
    DESCRIPTION = "Detects console.log and console.error usage"
    SEVERITY = "ADVICE"
    DETECTOR = ConsoleUsageDetector
  
    def get_description(self) -> str:
        return self.DESCRIPTION
  
    # That's it! ScriptRuleBase handles:
    # - Iterating PMD/POD/Script files
    # - Parsing scripts into AST
    # - Calling detector
    # - Converting Violations to Findings
```

### Complete Working Example - Structure Rule

```python
# user/custom_widget_validation.py
from typing import Generator
from ...structure.shared import StructureRuleBase
from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext

class CustomWidgetLabelRule(StructureRuleBase):
    """Ensures all widgets have labels for accessibility."""
  
    DESCRIPTION = "Ensures widgets have labels for accessibility"
    SEVERITY = "ADVICE"
  
    def get_description(self) -> str:
        return self.DESCRIPTION
  
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        if not pmd_model.presentation:
            return
      
        # Traverse all widgets using helper method
        presentation_dict = pmd_model.presentation.__dict__
        for section_name, section_data in presentation_dict.items():
            if isinstance(section_data, dict):
                for widget, path, index in self.traverse_presentation_structure(section_data, section_name):
                    yield from self._check_widget_label(widget, pmd_model, path)
  
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        # Similar logic for POD files
        yield
  
    def _check_widget_label(self, widget, pmd_model, widget_path):
        """Check if widget has a label."""
        if not isinstance(widget, dict):
            return
      
        widget_type = widget.get('type')
        if widget_type in ['text', 'richText'] and 'label' not in widget:
            # Use path helpers for accurate line numbers
            container = self.extract_nearest_container_from_path(widget_path)
          
            # Get line number...
            line_number = 1  # Calculate using helper methods
          
            yield self._create_finding(
                message=f"Widget of type '{widget_type}' should have a label for accessibility",
                file_path=pmd_model.file_path,
                line=line_number
            )
```

### Also See

See `examples/_example_custom_rule.py` for additional examples showing:

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
      "severity_override": "ACTION",
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
