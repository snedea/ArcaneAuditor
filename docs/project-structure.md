# Project Structure Guide 📁

> 📚 For developers and contributors — understand the Arcane Auditor's inner workings.

This document provides a detailed overview of the Arcane Auditor project structure for contributors and developers.

## 🏗️ High-Level Architecture

The repository is organized to separate the validation core, web interface, testing framework, and supporting configuration files.

```
ArcaneAuditor/
├── arcane_auditor/           # Core validation engine
├── web/                      # Web interface (FastAPI + frontend)
├── tests/                    # Automated test suite
├── config/                   # Configuration management
├── docs/                     # Documentation
├── samples/                  # Sample files and templates
├── assets/                   # Static assets (logos, screenshots)
└── release_notes/            # Version history
```

## 📦 Core Components

### `arcane_auditor/` - Main Package
The heart of the validation engine containing all core functionality.

See also: [Rule Documentation](../parser/rules/RULE_BREAKDOWN.md)

```
arcane_auditor/
├── __init__.py              # Package initialization
├── main.py                  # CLI entry point and command handling
├── rules/                   # Validation rule implementations
│   ├── __init__.py
│   ├── base.py              # Base rule classes and interfaces
│   ├── script.py            # Script validation rules
│   └── structure.py         # Structure validation rules
├── parser/                  # File parsing and analysis
│   ├── __init__.py
│   ├── pmd_parser.py        # PMD file parser
│   ├── pod_parser.py        # Pod file parser
│   └── script_parser.py     # Script file parser
├── output/                  # Output formatting and generation
│   ├── __init__.py
│   ├── formatter.py         # Console, JSON, Excel formatters
│   └── excel.py             # Excel report generation
└── config/                  # Configuration management
    ├── __init__.py
    ├── loader.py             # Configuration loading and merging
    └── validator.py          # Configuration validation
```

### `web/` - Web Interface
Modern web interface built with FastAPI and vanilla JavaScript.

```
web/
├── server.py                # FastAPI server and API endpoints
└── frontend/                # Frontend assets
    ├── index.html           # Main HTML template
    ├── style.css            # Styling and themes
    └── script.js            # JavaScript functionality
```

### `tests/` - Test Suite
Comprehensive test coverage for all components with 50+ test files.

```
tests/
├── __init__.py
├── test_rules_engine.py           # Core rules engine tests
├── test_script_*.py               # Script validation rule tests (20+ files)
│   ├── test_script_complexity_rule.py
│   ├── test_script_console_log_rule.py
│   ├── test_script_dead_code.py
│   ├── test_script_long_function_rule.py
│   ├── test_script_null_safety_rule.py
│   ├── test_script_unused_variable_rule.py
│   └── ... (additional script rule tests)
├── test_endpoint_*.py             # Endpoint validation tests
│   ├── test_endpoint_base_url_type_rule.py
│   ├── test_endpoint_fail_on_status_codes_rule.py
│   ├── test_endpoint_name_lower_camel_case_rule.py
│   └── test_endpoint_on_send_self_data.py
├── test_widget_*.py               # Widget validation tests
│   ├── test_widget_id_lower_camel_case_rule.py
│   ├── test_widget_id_required_rule.py
│   └── test_widget_traversal.py
├── test_context_*.py              # Context awareness tests
│   ├── test_context_formatting.py
│   ├── test_context_integration.py
│   └── test_context_tracker.py
├── test_structure_*.py            # Structure validation tests
├── test_app_parser.py             # Application parser tests
├── test_file_processor.py         # File processing tests
├── test_finding.py                # Finding model tests
└── test_*.py                      # Additional integration tests
```

### `config/` - Configuration System
Layered configuration system with presets, team, and personal configs.

```
config/
├── README.md                # Configuration guide
├── presets/                 # Built-in configurations
│   ├── development.json     # Development-friendly settings
│   └── production-ready.json # Pre-deployment validation
├── teams/                   # Team/project configurations
│   └── [team-configs.json]
└── personal/                # Personal overrides (gitignored)
    └── README.md            # Personal configuration guide
```

### `docs/` - Documentation
Detailed documentation for rules, APIs, and project structure.

```
docs/
├── rules.md                 # Rule documentation and examples
├── api.md                   # API reference
└── project-structure.md     # This file
```

### `samples/` - Sample Files
Example files and templates for testing and demonstration.

```
samples/
├── templates/               # Template files
│   ├── presentation/        # PMD templates
│   └── model/              # Business object templates
├── archives/               # Sample application archives
│   └── capitalProjectPlanning/
└── working/                # Working examples
```

### `assets/` - Static Assets
Images, logos, and screenshots for documentation and web interface.

```
assets/
├── arcane-auditor-logo.png  # Main logo
├── config-dark.png          # Configuration screenshot (dark)
├── config-light.png         # Configuration screenshot (light)
├── details-dark.png         # Details view screenshot (dark)
├── details-light.png        # Details view screenshot (light)
├── issues-dark.png          # Issues view screenshot (dark)
├── issues-light.png         # Issues view screenshot (light)
├── results-dark.png         # Results view screenshot (dark)
├── results-light.png        # Results view screenshot (light)
├── upload-dark.png          # Upload view screenshot (dark)
└── upload-light.png         # Upload view screenshot (light)
```

## 🔄 Data Flow

1. **Input** → Files uploaded via CLI or web interface
2. **Parsing** → Files parsed by appropriate parsers (PMD, Pod, Script)
3. **Validation** → Rules engine applies validation rules
4. **Output** → Results formatted and exported (console, JSON, Excel)

## 🛠️ Development Workflow

1. **Core Changes**: Modify `arcane_auditor/` for validation logic
2. **Web Interface**: Update `web/` for UI/UX improvements
3. **Tests**: Add tests in `tests/` for new functionality
4. **Configuration**: Update `config/` for new rule settings
5. **Documentation**: Update `docs/` for new features

## 📋 Key Files

- **`main.py`**: CLI entry point and command handling
- **`web/server.py`**: FastAPI server and API endpoints
- **`parser/rules_engine.py`**: Core validation engine
- **`output/formatter.py`**: Output formatting logic
- **`config/README.md`**: Configuration system guide
- **`tests/test_rules_engine.py`**: Validates rule application logic

## 🎯 Contributing Guidelines

When contributing to Arcane Auditor:

1. **Follow the existing structure** - maintain consistency with current organization
2. **Add tests** - ensure new functionality is properly tested
3. **Update documentation** - keep docs in sync with code changes
4. **Use meaningful names** - follow existing naming conventions
5. **Consider configuration** - make new rules configurable when appropriate

---

*For more information, see the main [README](../README.md) or [Configuration Guide](../config/README.md).*
