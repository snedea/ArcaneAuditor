![Arcane Auditor Logo](assets/arcane-auditor-logo.png)

*A mystical code review tool for Workday Extend applications that validates PMD, Pod, and Script syntax, structure compliance, and coding best practices.*

## 🎯 Overview

Arcane Auditor channels ancient wisdom through **30 comprehensive validation rules** to reveal hidden quality violations that compilers cannot detect but master code wizards should catch. This mystical tool analyzes:

- **📄 PMD Files**: Page definitions with embedded scripts, endpoints, and presentation layers
- **🧩 Pod Files**: Pod files with template widgets and endpoint configurations  
- **📜 Script Files**: Standalone .script files with function libraries and utilities

**Rule Categories:**
- **Script Quality (20 Rules)**: Script syntax, complexity, naming conventions, unused code detection
- **Endpoint Validation (4 Rules)**: API endpoint compliance, error handling, naming conventions
- **Structure Validation (4 Rules)**: Widget configurations, required fields, component validation
- **PMD Organization (2 Rules)**: File structure, section ordering, and security domain validation

## 🛡️ Update-Safe Configuration System

Arcane Auditor features a **layered configuration system** that protects your customizations during app updates:

- **🔒 App Configs** (`configs/`) - Base configurations (updated with app)
- **🛡️ User Configs** (`user_configs/`) - Team/project settings (update-safe)
- **🏠 Local Configs** (`local_configs/`) - Personal overrides (highest priority)

```bash
# List all available configurations and safety status
uv run main.py list-configs

# Use team configuration (searches all directories)
uv run main.py review-app myapp.zip --config team-standard

# Use explicit path
uv run main.py review-app myapp.zip --config user_configs/my-config.json
```

Your customizations in `user_configs/` and `local_configs/` are **completely protected** from app updates! 🛡️

## 🚀 Quick Start

### Installation

```bash
# Clone the repository (SSH)
git clone git@github.com:Developers-and-Dragons/ArcaneAuditor.git arcane-auditor
# Or using HTTPS
# git clone https://github.com/Developers-and-Dragons/ArcaneAuditor.git arcane-auditor

cd arcane-auditor

# Install dependencies
uv sync

# Run analysis on a Workday Extend application (CLI)
# Supports PMD, Pod, and Script files
uv run main.py review-app your-app.zip
```

### Web Interface (Recommended)

For a user-friendly mystical web interface:

```bash
# One-time setup (requires Node.js)
python web/setup_web_interface.py

# Start the web server
python web/start_web_interface.py

# Open http://localhost:8000 in your browser to access the Arcane Auditor
```

### Basic Usage

```bash
# Analyze a PMD application with arcane wisdom
uv run main.py review-app samples/archives/template_bad_nkhlsq.zip

# Use custom magical configuration (supports layered loading)
uv run main.py review-app your-app.zip --config team-standard

# List available configurations
uv run main.py list-configs
```

## 📁 Project Structure

```
arcane-auditor/
├── main.py                           # Main application entry point
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Project configuration
├── README.md                         # This file
├── LICENSE                           # MIT License
├── docs/                             # Documentation
│   ├── RULE_BREAKDOWN.md             # Detailed rule documentation
│   └── WEB_README.md                 # Web interface documentation
│
├── file_processing/                  # File processing pipeline
│   ├── config.py                     # Configuration models
│   ├── models.py                     # Data models
│   └── processor.py                  # Main processing logic
│
├── parser/                           # PMD parsing and validation
│   ├── app_parser.py                 # Main application parser
│   ├── config.py                     # Parser configuration
│   ├── models.py                     # Parser data models
│   ├── pmd_script_parser.py          # PMD Script parser
│   ├── pmd_script_grammar.lark       # PMD Script grammar definition
│   ├── pmd_preprocessor.py           # PMD file preprocessing
│   │
│   ├── rules/                        # Validation rules engine
│   │   ├── __init__.py               # Rules package
│   │   ├── base.py                   # Base Rule class and utilities
│   │   ├── base_validation.py        # Enhanced validation base class
│   │   ├── common_validations.py     # Shared validation functions
│   │   ├── line_number_utils.py      # Line number calculation utilities
│   │   ├── rules_engine.py           # Rules discovery and execution
│   │   │
│   │   ├── script/                   # Script validation rules
│   │   │   ├── __init__.py
│   │   │   ├── core/                 # Basic syntax/style rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── var_usage.py      # ScriptVarUsageRule
│   │   │   │   ├── variable_naming.py # ScriptVariableNamingRule
│   │   │   │   └── console_log.py    # ScriptConsoleLogRule
│   │   │   ├── complexity/           # Code complexity rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── nesting_level.py  # ScriptNestingLevelRule
│   │   │   │   ├── cyclomatic_complexity.py # ScriptComplexityRule
│   │   │   │   └── long_function.py  # ScriptLongFunctionRule
│   │   │   ├── unused_code/          # Dead code detection
│   │   │   │   ├── __init__.py
│   │   │   │   ├── unused_variables.py # ScriptUnusedVariableRule
│   │   │   │   ├── unused_parameters.py # ScriptUnusedFunctionParametersRule
│   │   │   │   └── empty_functions.py # ScriptEmptyFunctionRule
│   │   │   └── logic/                # Logic/flow rules
│   │   │       ├── __init__.py
│   │   │       ├── magic_numbers.py  # ScriptMagicNumberRule
│   │   │       ├── null_safety.py    # ScriptNullSafetyRule
│   │   │       ├── verbose_boolean.py # ScriptVerboseBooleanCheckRule
│   │   │       ├── return_consistency.py # ScriptFunctionReturnConsistencyRule
│   │   │       └── string_concat.py  # ScriptStringConcatRule
│   │   │
│   │   ├── structure/                # Structure validation rules
│   │   │   ├── __init__.py
│   │   │   ├── widgets/              # Widget validation rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── widget_id_required.py # WidgetIdRequiredRule
│   │   │   │   └── widget_id_lower_camel_case.py # WidgetIdLowerCamelCaseRule
│   │   │   ├── endpoints/            # Endpoint validation rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── endpoint_name_lower_camel_case.py # EndpointNameLowerCamelCaseRule
│   │   │   │   ├── endpoint_on_send_self_data.py # EndpointOnSendSelfDataRule
│   │   │   │   ├── endpoint_fail_on_status_codes.py # EndpointFailOnStatusCodesRule
│   │   │   │   └── endpoint_url_base_url_type.py # EndpointUrlBaseUrlTypeRule
│   │   │   └── validation/           # General validation rules
│   │   │       ├── __init__.py
│   │   │       ├── footer_pod_required.py # FooterPodRequiredRule
│   │   │       └── string_boolean.py # StringBooleanRule
│   │   │
│   │   └── custom/                   # 🆕 User custom rules
│   │       ├── __init__.py           # Custom rules package
│   │       ├── README.md             # Custom rules development guide
│   │       ├── examples/             # Example implementations
│   │       │   ├── __init__.py
│   │       │   └── example_custom_rule.py # Sample custom rule
│   │       └── user/                 # User's actual custom rules
│   │           └── __init__.py
│   │
│
├── tests/                            # Unit tests
│   ├── test_app_parser.py
│   ├── test_file_processor.py
│   ├── test_finding.py
│   ├── test_pmd_script_rules_integration.py
│   ├── test_pmd_script_rules.py
│   ├── test_pmd_structure_rules_integration.py
│   ├── test_pmd_structure_rules.py
│   └── test_rules_engine.py
│
├── samples/                          # Sample PMD applications (gitignored)
│   ├── appManifest.json
│   ├── model/
│   ├── presentation/
│   └── template_bad_nkhlsq.zip      # Sample with violations
```

## 🔧 Validation Rules

### Rule Categories

#### Script Rules

**Core Rules** (`parser/rules/script/core/`)

- **ScriptVarUsageRule**: Var Usage Rule - Prefer `let`/`const` over `var`
- **ScriptFileVarUsageRule**: File Var Usage Rule - Script file variable usage patterns
- **ScriptConsoleLogRule**: Console Log Rule - Avoid console statements in production
- **ScriptVariableNamingRule**: Variable Naming Rule - Use lowerCamelCase convention

**Complexity Rules** (`parser/rules/script/complexity/`)

- **ScriptNestingLevelRule**: Nesting Level Rule - Limit code nesting depth
- **ScriptComplexityRule**: Cyclomatic Complexity Rule - Control function complexity
- **ScriptLongFunctionRule**: Long Function Rule - Limit function length
- **ScriptFunctionParameterCountRule**: Function Parameter Count Rule - Limit function parameters

**Unused Code Rules** (`parser/rules/script/unused_code/`)

- **ScriptUnusedVariableRule**: Unused Variables Rule - Remove unused variables
- **ScriptUnusedFunctionParametersRule**: Unused Parameters Rule - Remove unused function parameters
- **ScriptUnusedFunctionRule**: Unused Functions Rule - Remove unused functions
- **ScriptUnusedScriptIncludesRule**: Unused Script Includes Rule - Remove unused script imports
- **ScriptEmptyFunctionRule**: Empty Functions Rule - Remove empty functions

**Logic Rules** (`parser/rules/script/logic/`)

- **ScriptMagicNumberRule**: Magic Numbers Rule - Use named constants
- **ScriptNullSafetyRule**: Null Safety Rule - Proper null checking
- **ScriptDescriptiveParameterRule**: Descriptive Parameters Rule - Use descriptive parameter names
- **ScriptFunctionalMethodUsageRule**: Functional Method Usage Rule - Prefer functional programming methods
- **ScriptVerboseBooleanCheckRule**: Verbose Boolean Rule - Simplify boolean expressions
- **ScriptFunctionReturnConsistencyRule**: Return Consistency Rule - Consistent return patterns
- **ScriptStringConcatRule**: String Concatenation Rule - Use template literals instead of string concatenation

#### Structure Rules

**Widget Rules** (`parser/rules/structure/widgets/`)

- **WidgetIdRequiredRule**: Widget ID Required Rule - All widgets need IDs
- **WidgetIdLowerCamelCaseRule**: Widget ID Lower Camel Case Rule - Widget IDs follow naming convention

**Endpoint Rules** (`parser/rules/structure/endpoints/`)

- **EndpointNameLowerCamelCaseRule**: Endpoint Name Lower Camel Case Rule - Endpoint names follow convention
- **EndpointOnSendSelfDataRule**: Endpoint On Send Self Data Rule - Avoid self.data anti-pattern
- **EndpointFailOnStatusCodesRule**: Endpoint Fail On Status Codes Rule - Proper error handling
- **EndpointBaseUrlTypeRule**: Endpoint Base URL Type Rule - Consistent URL configuration

**Validation Rules** (`parser/rules/structure/validation/`)

- **FooterPodRequiredRule**: Footer Pod Required Rule - Footer must use pod structure
- **StringBooleanRule**: String Boolean Rule - Use boolean values, not strings

#### PMD Rules

**Organization Rules** (`parser/rules/structure/validation/`)

- **PMDSectionOrderingRule**: PMD Section Ordering Rule - Consistent file structure and section ordering
- **PMDSecurityDomainRule**: PMD Security Domain Rule - Ensure security domains are defined (with smart exclusions)

#### Custom Rules

**User Extensions** (`parser/rules/custom/user/`)

- **Custom[Description]Rule**: User-defined validation rules
- See `parser/rules/custom/README.md` for development guide

### Rule Discovery

The rules engine automatically discovers all validation rules using `pkgutil.walk_packages()`. Rules are organized by:

1. **Category**: Script vs Structure vs Custom
2. **Type**: Core, Complexity, Unused Code, Logic, Widgets, Endpoints, Validation
3. **Naming**: Descriptive class names (e.g., `ScriptVarUsageRule`, `WidgetIdRequiredRule`)

## 🛠️ Development

### Adding New Rules

> **⚠️ Important**: To avoid merge conflicts when updating the official codebase, **always use the Custom Rules system** for user-defined validation rules. Only modify official rules if you are a core contributor to the project.

#### For Users: Custom Rules (Recommended)

**Use this approach for your own validation rules:**

1. Place new rules in `parser/rules/custom/user/`
2. Use descriptive class names (e.g., `CustomScriptMyRule`)
3. Follow patterns in `parser/rules/custom/examples/`
4. See `parser/rules/custom/README.md` for detailed guide

**Benefits:**

- ✅ No merge conflicts when updating the official codebase
- ✅ Rules persist through official updates
- ✅ Easy to share and version control your custom rules
- ✅ Automatic discovery by the rules engine

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/test_all_script_rules.py
uv run pytest tests/test_all_structure_rules.py
uv run pytest tests/test_rules_engine.py

# Test with sample data
uv run main.py review-app samples/archives/template_bad_nkhlsq.zip
```

### Configuration

Create custom configurations in JSON format:

```json
{
  "rules": {
    "CustomScriptCommentQualityRule": {
      "enabled": true,
      "severity_override": "WARNING",
      "custom_settings": {
        "min_comment_density": 0.15
      }
    },
    "ScriptVarUsageRule": {
      "enabled": true,
      "severity_override": "SEVERE",
      "custom_settings": {}
    },
    "ScriptMagicNumberRule": {
      "enabled": false,
      "severity_override": null,
      "custom_settings": {}
    }
  }
}
```

## 📚 Documentation

- **docs/RULE_BREAKDOWN.md**: Detailed rule descriptions with examples
- **docs/WEB_README.md**: Web interface documentation
- **parser/rules/custom/README.md**: Custom rules development guide

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**TL;DR:** You can use, modify, and distribute this code freely, just keep the copyright notice🔮
