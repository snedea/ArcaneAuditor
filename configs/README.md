# Extend Reviewer Configuration Files

This directory contains pre-configured rule sets for the Extend Reviewer tool. Choose the configuration that best fits your needs:

## Available Configurations

### 🚀 **default.json** (Recommended)
- **All 25 rules enabled** with their default settings
- Best for teams that want comprehensive code quality analysis
- Good starting point for most users

### ⚡ **minimal.json** (Quick Start)
- **Only 6 critical rules enabled**:
  - `ScriptNullSafetyRule` - Prevents null reference exceptions
  - `ScriptConsoleLogRule` - Removes console.log from production code
  - `ScriptEmptyFunctionRule` - Detects empty function bodies
  - `ScriptFunctionReturnConsistencyRule` - Ensures consistent return patterns
  - `EndpointFailOnStatusCodesRule` - Proper error handling
  - `WidgetIdRequiredRule` - Required widget IDs for debugging
- Perfect for quick analysis or when you want to focus on critical issues only

### 🎯 **comprehensive.json** (Production Ready)
- **All 25 rules enabled** with optimized severity levels
- **ERROR severity** for critical issues (console.log, null safety, etc.)
- **INFO severity** for preferences (string booleans, footer pods)
- Best for production code reviews and CI/CD pipelines

## How to Use

### Web Interface
1. Go to the Extend Reviewer web interface
2. Upload your ZIP file
3. Select a configuration from the dropdown (optional - defaults to `default.json`)

### Command Line
```bash
# Use default configuration (all rules)
uv run python main.py analyze myapp.zip

# Use minimal configuration
uv run python main.py analyze myapp.zip --config minimal

# Use comprehensive configuration
uv run python main.py analyze myapp.zip --config comprehensive
```

### Custom Configuration
You can create your own configuration by:
1. Copying one of the existing files
2. Modifying rule settings as needed
3. Saving it with a descriptive name

## Rule Categories

### Script Complexity & Structure (4 rules)
- Cyclomatic complexity limits
- Function parameter counting
- Function length limits
- Nesting level limits

### Script Code Quality (7 rules)
- Console log detection
- Variable usage patterns
- Naming conventions
- Functional method usage
- Magic number detection
- Null safety checks
- Return consistency
- String concatenation patterns
- Boolean expression optimization

### Script Unused Code (4 rules)
- Empty function detection
- Unused function detection
- Unused parameter detection
- Unused variable detection

### Endpoint Structure (4 rules)
- Status code handling
- Naming conventions
- Self.data usage
- URL base type validation

### Widget Structure (2 rules)
- Required ID fields
- Naming conventions

### General Structure (2 rules)
- Footer pod requirements
- String boolean detection

## Customizing Rules

Each rule can be configured with:
- `enabled`: true/false to enable/disable the rule
- `severity_override`: "INFO", "WARNING", or "ERROR" to override default severity
- `custom_settings`: Rule-specific configuration options

Example:
```json
{
  "ScriptLongFunctionRule": {
    "enabled": true,
    "severity_override": "WARNING",
    "custom_settings": {
      "max_lines": 30
    }
  }
}
```

