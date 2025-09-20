# Arcane Auditor Configuration Scrolls 📜

*Mystical configurations for the Developers and Dragons initiative*

This directory contains pre-configured spell sets for the Arcane Auditor. Choose the configuration that best fits your needs:

## Available Configurations

### 🚀 **default.json** (Recommended)
- **All 29 rules enabled** with their default settings
- Includes comprehensive analysis for both PMD embedded scripts AND standalone .script files
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
- **Note:** PMDSectionOrderingRule is disabled (style preference)

### 🎯 **comprehensive.json** (Production Ready)
- **All 29 rules enabled** with optimized severity levels
- **ERROR severity** for critical issues (console.log, null safety, etc.)
- **WARNING severity** for structure issues (PMD section ordering)
- **INFO severity** for preferences (string booleans, footer pods)
- Best for production code reviews and CI/CD pipelines

## How to Use

### Web Interface
1. Go to the Arcane Auditor mystical web interface
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

## Rule Categories (29 Total Rules)

### Script Rules (20 rules)
**Applies to both PMD embedded scripts AND standalone .script files:**

#### Script Complexity & Structure (4 rules)
- Cyclomatic complexity limits (`ScriptComplexityRule`)
- Function parameter counting (`ScriptFunctionParameterCountRule`)
- Function length limits (`ScriptLongFunctionRule`)
- Nesting level limits (`ScriptNestingLevelRule`)

#### Script Code Quality (10 rules)
- Console log detection (`ScriptConsoleLogRule`)
- Variable usage patterns (`ScriptVarUsageRule`, `ScriptFileVarUsageRule`)
- Naming conventions (`ScriptVariableNamingRule`)
- Functional method usage (`ScriptFunctionalMethodUsageRule`)
- Magic number detection (`ScriptMagicNumberRule`)
- Null safety checks (`ScriptNullSafetyRule`)
- Return consistency (`ScriptFunctionReturnConsistencyRule`)
- String concatenation patterns (`ScriptStringConcatRule`)
- Boolean expression optimization (`ScriptVerboseBooleanCheckRule`)
- Descriptive parameter names (`ScriptDescriptiveParameterRule`)

#### Script Unused Code (6 rules)
- Empty function detection (`ScriptEmptyFunctionRule`)
- Unused function detection (`ScriptUnusedFunctionRule`)
- Unused parameter detection (`ScriptUnusedFunctionParametersRule`)
- Unused variable detection (`ScriptUnusedVariableRule`)
- Unused script includes detection (`ScriptUnusedScriptIncludesRule`)

### Endpoint Rules (4 rules)
- Status code handling (`EndpointFailOnStatusCodesRule`)
- Naming conventions (`EndpointNameLowerCamelCaseRule`)
- Self.data usage (`EndpointOnSendSelfDataRule`)
- URL base type validation (`EndpointUrlBaseUrlTypeRule`)

### Structure Rules (4 rules)
- Required widget ID fields (`WidgetIdRequiredRule`)
- Widget naming conventions (`WidgetIdLowerCamelCaseRule`)
- Footer pod requirements (`FooterPodRequiredRule`)
- String boolean detection (`StringBooleanRule`)

### PMD Rules (1 rule)
- **Configurable section ordering** (`PMDSectionOrderingRule`) - Enforces consistent PMD file structure

## Customizing Rules

Each rule can be configured with:
- `enabled`: true/false to enable/disable the rule
- `severity_override`: "INFO", "WARNING", or "ERROR" to override default severity
- `custom_settings`: Rule-specific configuration options

### Basic Configuration Example
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

### Advanced Configuration: PMD Section Ordering
The `PMDSectionOrderingRule` supports custom section ordering:

```json
{
  "PMDSectionOrderingRule": {
    "enabled": true,
    "severity_override": "WARNING",
    "custom_settings": {
      "section_order": [
        "id",
        "securityDomains", 
        "endPoints",
        "presentation",
        "onLoad",
        "onSubmit",
        "outboundData",
        "include",
        "script"
      ]
    }
  }
}
```

**Customization Options:**
- `section_order`: Array defining the preferred order of PMD sections

### Dual Script Analysis
Script rules automatically analyze both:
- **PMD embedded scripts** (in `script`, `onLoad`, `onSubmit` fields)
- **Standalone .script files** (like `util.script`, `helper.script`)

No additional configuration needed - comprehensive analysis is automatic!

