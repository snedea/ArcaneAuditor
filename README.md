# Extend Reviewer

A comprehensive code review tool for Workday Extend applications that validates PMD Script syntax, structure compliance, and coding best practices.

## 🎯 Overview

Extend Reviewer analyzes Workday Extend applications to catch quality violations that compilers can't detect but code reviewers should catch. It focuses on:

- **Script Quality**: PMD Script syntax, complexity, naming conventions
- **Structure Validation**: Widget configurations, endpoint compliance, required fields
- **Best Practices**: Coding standards, anti-patterns, maintainability

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd extend-reviewer

# Install dependencies
uv sync

# Run analysis on a PMD application (CLI)
uv run main.py review-app your-app.zip
```

### Web Interface (Recommended)

For a user-friendly web interface:

```bash
# One-time setup (requires Node.js)
python setup_web_interface.py

# Start the web server
python start_web_interface.py

# Open http://localhost:8000 in your browser
```

### Basic Usage

```bash
# Analyze a PMD application
uv run main.py review-app sample_extend_code/template_bad_nkhlsq.zip

# Use custom configuration
uv run main.py review-app your-app.zip --config custom-config.json
```

## 📁 Project Structure

```
extend-reviewer/
├── main.py                           # Main application entry point
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Project configuration
├── README.md                         # This file
├── RULE_BREAKDOWN.md                 # Detailed rule documentation
│
├── file_processing/                  # File processing pipeline
│   ├── config.py                     # Configuration models
│   ├── models.py                     # Data models
│   └── processor.py                  # Main processing logic
│
├── llm_integration/                  # LLM integration (future)
│   ├── client.py
│   └── prompts.py
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
│   │   │   │   ├── var_usage.py      # SCRIPT001 - Var Usage Rule
│   │   │   │   ├── variable_naming.py # SCRIPT008 - Variable Naming Rule
│   │   │   │   └── console_log.py    # SCRIPT005 - Console Log Rule
│   │   │   ├── complexity/           # Code complexity rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── nesting_level.py  # SCRIPT002 - Nesting Level Rule
│   │   │   │   ├── cyclomatic_complexity.py # SCRIPT003 - Complexity Rule
│   │   │   │   └── long_function.py  # SCRIPT007 - Long Function Rule
│   │   │   ├── unused_code/          # Dead code detection
│   │   │   │   ├── __init__.py
│   │   │   │   ├── unused_variables.py # SCRIPT004 - Unused Variables Rule
│   │   │   │   ├── unused_parameters.py # SCRIPT012 - Unused Parameters Rule
│   │   │   │   └── empty_functions.py # SCRIPT013 - Empty Functions Rule
│   │   │   └── logic/                # Logic/flow rules
│   │   │       ├── __init__.py
│   │   │       ├── magic_numbers.py  # SCRIPT006 - Magic Numbers Rule
│   │   │       ├── null_safety.py    # SCRIPT010 - Null Safety Rule
│   │   │       ├── verbose_boolean.py # SCRIPT011 - Verbose Boolean Rule
│   │   │       └── return_consistency.py # SCRIPT014 - Return Consistency Rule
│   │   │
│   │   ├── structure/                # Structure validation rules
│   │   │   ├── __init__.py
│   │   │   ├── widgets/              # Widget validation rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── widget_id_required.py # STRUCT001 - Widget ID Required Rule
│   │   │   │   └── widget_id_lower_camel_case.py # STYLE001 - Widget ID Lower Camel Case Rule
│   │   │   ├── endpoints/            # Endpoint validation rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── endpoint_name_lower_camel_case.py # STYLE002 - Endpoint Name Lower Camel Case Rule
│   │   │   │   ├── endpoint_on_send_self_data.py # SCRIPT009 - Endpoint On Send Self Data Rule
│   │   │   │   ├── endpoint_fail_on_status_codes.py # STRUCT004 - Endpoint Fail On Status Codes Rule
│   │   │   │   └── endpoint_url_base_url_type.py # STRUCT006 - Endpoint URL Base URL Type Rule
│   │   │   └── validation/           # General validation rules
│   │   │       ├── __init__.py
│   │   │       ├── footer_pod_required.py # STRUCT003 - Footer Pod Required Rule
│   │   │       └── string_boolean.py # STRUCT005 - String Boolean Rule
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
├── sample_extend_code/               # Sample PMD applications for testing
│   ├── appManifest.json
│   ├── model/
│   ├── presentation/
│   └── template_bad_nkhlsq.zip      # Sample with violations
```

## 🔧 Validation Rules

### Rule Categories

#### Script Rules (SCRIPT001-SCRIPT014)

**Core Rules** (`parser/rules/script/core/`)

- **SCRIPT001**: Var Usage Rule - Prefer `let`/`const` over `var`
- **SCRIPT005**: Console Log Rule - Avoid console statements in production
- **SCRIPT008**: Variable Naming Rule - Use lowerCamelCase convention

**Complexity Rules** (`parser/rules/script/complexity/`)

- **SCRIPT002**: Nesting Level Rule - Limit code nesting depth
- **SCRIPT003**: Cyclomatic Complexity Rule - Control function complexity
- **SCRIPT007**: Long Function Rule - Limit function length

**Unused Code Rules** (`parser/rules/script/unused_code/`)

- **SCRIPT004**: Unused Variables Rule - Remove unused variables
- **SCRIPT012**: Unused Parameters Rule - Remove unused function parameters
- **SCRIPT013**: Empty Functions Rule - Remove empty functions

**Logic Rules** (`parser/rules/script/logic/`)

- **SCRIPT006**: Magic Numbers Rule - Use named constants
- **SCRIPT010**: Null Safety Rule - Proper null checking
- **SCRIPT011**: Verbose Boolean Rule - Simplify boolean expressions
- **SCRIPT014**: Return Consistency Rule - Consistent return patterns

#### Structure Rules (STRUCT001-STRUCT006, STYLE001-STYLE002)

**Widget Rules** (`parser/rules/structure/widgets/`)

- **STRUCT001**: Widget ID Required Rule - All widgets need IDs
- **STYLE001**: Widget ID Lower Camel Case Rule - Widget IDs follow naming convention

**Endpoint Rules** (`parser/rules/structure/endpoints/`)

- **STYLE002**: Endpoint Name Lower Camel Case Rule - Endpoint names follow convention
- **SCRIPT009**: Endpoint On Send Self Data Rule - Avoid self.data anti-pattern
- **STRUCT004**: Endpoint Fail On Status Codes Rule - Proper error handling
- **STRUCT006**: Endpoint URL Base URL Type Rule - Consistent URL configuration

**Validation Rules** (`parser/rules/structure/validation/`)

- **STRUCT003**: Footer Pod Required Rule - Footer must use pod structure
- **STRUCT005**: String Boolean Rule - Use boolean values, not strings

#### Custom Rules (CUSTOM001-CUSTOM999)

**User Extensions** (`parser/rules/custom/user/`)

- **CUSTOM001+**: User-defined validation rules
- See `parser/rules/custom/README.md` for development guide

### Rule Discovery

The rules engine automatically discovers all validation rules using `pkgutil.walk_packages()`. Rules are organized by:

1. **Category**: Script vs Structure vs Custom
2. **Type**: Core, Complexity, Unused Code, Logic, Widgets, Endpoints, Validation
3. **ID Range**: SCRIPT001-SCRIPT999, STRUCT001-STRUCT999, STYLE001-STYLE999, CUSTOM001-CUSTOM999

## 🛠️ Development

### Adding New Rules

> **⚠️ Important**: To avoid merge conflicts when updating the official codebase, **always use the Custom Rules system** for user-defined validation rules. Only modify official rules if you are a core contributor to the project.

#### For Users: Custom Rules (Recommended)

**Use this approach for your own validation rules:**

1. Place new rules in `parser/rules/custom/user/`
2. Use CUSTOM### IDs (CUSTOM001, CUSTOM002, etc.)
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
uv run main.py review-app sample_extend_code/template_bad_nkhlsq.zip
```

### Configuration

Create custom configurations in JSON format:

```json
{
  "rules": {
    "CustomScriptCommentQualityRule": {
      "enabled": true,
      "severity": "WARNING",
      "min_comment_density": 0.15
    },
    "ScriptVarUsageRule": {
      "enabled": true,
      "severity": "ERROR"
    },
    "ScriptMagicNumberRule": {
      "enabled": false
    }
  }
}
```

## 📚 Documentation

- **RULE_BREAKDOWN.md**: Detailed rule descriptions with examples
- **parser/rules/custom/README.md**: Custom rules development guide

## 📄 License

[TBD]

---

**Extend Reviewer** - Making Workday Extend code reviews more effective and consistent! 🚀
