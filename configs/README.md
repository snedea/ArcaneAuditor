# Arcane Auditor Configuration Scrolls 📜

This directory contains pre-configured spell sets for the Arcane Auditor. Choose the configuration that best fits your needs:

## Available Configurations

### 🚀 **default.json** (Recommended)

- **All 34 rules enabled** with their default settings
- Includes comprehensive analysis for PMD, Pod, and standalone .script files
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

- **All 34 rules enabled** with optimized severity levels
- **ACTION severity** for must fix findings (console.log, null safety, etc.)
- **ADVICE severity** for preferences and style improvements (string booleans, footer pods)
- Best for production code reviews and CI/CD pipelines

## How to Use

### Web Interface

1. Go to the Arcane Auditor mystical web interface
2. **Select a configuration** from the available options:
   - **Built-in Configurations**: Default, Minimal, Comprehensive
   - **Team Configurations**: Custom team/project configurations (if available)
   - **Personal Configurations**: Personal developer overrides (if available)
3. Upload your ZIP file
4. Run analysis with your selected configuration

### Command Line

```bash
# Use default configuration (all rules)
uv run main.py review-app myapp.zip

# Use minimal configuration
uv run main.py review-app myapp.zip --config minimal

# Use comprehensive configuration
uv run main.py review-app myapp.zip --config comprehensive
```

### Custom Configuration

You can create your own configuration by:

1. **For Team/Project Configurations** (Recommended):
   - Copy an example from `user_configs/examples/`
   - Modify rule settings as needed
   - Save it in the `user_configs/` directory
   - Commit to your project repository

2. **For Personal Overrides**:
   - Create configurations in the `local_configs/` directory
   - These are never committed and override team settings

3. **For Complete Custom Configurations**:
   - Create anywhere on the filesystem
   - Use full path when specifying the configuration

## Rule Categories (34 Total Rules)

### Script Rules (21 rules)

**Applies to PMD embedded scripts, Pod endpoint/widget scripts, AND standalone .script files:**

#### Script Complexity & Structure (4 rules)

- Cyclomatic complexity limits (`ScriptComplexityRule`)
- Function parameter counting (`ScriptFunctionParameterCountRule`)
- Function length limits (`ScriptLongFunctionRule`)
- Nesting level limits (`ScriptNestingLevelRule`)

#### Script Code Quality (11 rules)

- Console log detection (`ScriptConsoleLogRule`)
- Variable usage patterns (`ScriptVarUsageRule`, `ScriptDeadCodeRule`)
- Naming conventions (`ScriptVariableNamingRule`, `ScriptFunctionParameterNamingRule`)
- Array method usage (`ScriptArrayMethodUsageRule`)
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

**Applies to PMD endpoints and Pod seed endpoints:**

- Status code handling (`EndpointFailOnStatusCodesRule`)
- Naming conventions (`EndpointNameLowerCamelCaseRule`)
- Self.data usage (`EndpointOnSendSelfDataRule`) - *PMD outbound only*
- URL base type validation (`EndpointBaseUrlTypeRule`)

### Structure Rules (5 rules)

**Applies to PMD presentation widgets and Pod template widgets:**

- Required widget ID fields (`WidgetIdRequiredRule`)
- Widget naming conventions (`WidgetIdLowerCamelCaseRule`)
- Footer pod requirements (`FooterPodRequiredRule`) - *PMD footer only*
- String boolean detection (`StringBooleanRule`)
- Embedded images detection (`EmbeddedImagesRule`) - *Detects base64 encoded images*

### PMD Rules (4 rules)

**Applies to PMD file structure and security:**

- **Configurable section ordering** (`PMDSectionOrderingRule`) - Enforces consistent PMD file structure
- **Security domain validation** (`PMDSecurityDomainRule`) - Ensures PMD pages have required security domains
- **Hardcoded application ID detection** (`HardcodedApplicationIdRule`) - Detects hardcoded applicationId values
- **Hardcoded WID detection** (`HardcodedWidRule`) - Detects hardcoded Workday ID values

## Customizing Rules

Each rule can be configured with:

- `enabled`: true/false to enable/disable the rule
- `severity_override`: "ADVICE" or "ACTION" to override default severity
- `custom_settings`: Rule-specific configuration options

### Basic Configuration Example

```json
{
  "ScriptLongFunctionRule": {
    "enabled": true,
    "severity_override": "ACTION",
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
    "severity_override": "ACTION",
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
