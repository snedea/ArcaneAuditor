![Arcane Auditor Logo](assets/arcane-auditor-logo.png)

*A mystical code review tool for Workday Extend applications.*

> ⚗️ **Validate. Visualize. Improve.** — PMD, Pod, and Script compliance with wizard-level precision.

![Version](https://img.shields.io/badge/version-0.5.0--beta.1-purple?style=for-the-badge)
[![Download](https://img.shields.io/badge/🚀-Download_Latest-orange?style=for-the-badge)](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases)

<a id="overview" />

## 🎯 Overview

Arcane Auditor channels ancient wisdom through **many comprehensive validation rules** to reveal hidden quality violations that compilers cannot detect but master code wizards should catch. This mystical tool analyzes:

- **📄 PMD Files**: Page definitions with embedded scripts, endpoints, and presentation layers
- **🧩 Pod Files**: Pod files with template widgets and endpoint configurations
- **📜 Script Files**: Standalone .script files with function libraries and utilities
- **📋 AMD Files**: Application manifest definitions
- **📋 SMD Files**: Security manifest definitions

**Key Features:**

- 🎯 **Exact (hopefully!) Line Numbers**: Hash-based mapping pinpoints violations
- 🧭 **Readable Violation Paths**: Uses widget IDs, labels, and types to indicate where an issue is found
- ✅ **Intelligent Detection**: Accurately tracks function usage, unused code, and code complexity
- 🛡️ **Update-Safe Configuration**: Layered config system protects your customizations
- 🎨 **Clear Messages**: Actionable violation messages with locations and fix suggestions
- 🧠 **Context Awareness**: Understands when analysis is partial due to missing files

> 🧙‍♂️ **Getting Started:** First, check the [Prerequisites](#prerequisites) to ensure you have everything installed, then follow the [Quick Start](#quick-start) guide to begin analyzing your code!

<a id="table-of-contents" />

## 🗂️ Table of Contents

- [📋 Prerequisites](#prerequisites)
- [🚀 Quick Start](#quick-start)
- [📦 Installation Options](#installation-options)
- [🌐 Web Interface](#web-interface)
- [🧠 Context Awareness](#context-awareness)
- [🛡️ Configuration System](#configuration-system)
- [🔧 Validation Rules](#validation-rules)
- [🛠️ Development](#development)
  - [🤝 Contributing](#contributing)
- [📚 Documentation](#documentation)
- [📄 License](#license)

<a id="web-interface-screenshots" />

## 🖼️ Web Interface Screenshots

### Dark Mode Interface

![Arcane Auditor Web Interface - Dark Mode](assets/results-dark.png)

### Light Mode Interface

![Arcane Auditor Web Interface - Light Mode](assets/results-light.png)

<details>
<summary>📸 More Screenshots (click to expand)</summary>

**Upload View:**
![Upload View](assets/upload-dark.png)

**Issues View:**
![Issues View](assets/issues-dark.png)

**Configuration View:**
![Configuration View](assets/config-dark.png)

**Details View:**
![Details View](assets/details-dark.png)

</details>

*The mystical web interface provides an intuitive way to upload and analyze your Workday Extend applications with real-time results and downloadable reports.*

<a id="prerequisites" />

## 📋 Prerequisites

### **Recommended: UV Package Manager** ⭐

**UV is the fastest and easiest way to get started!**

- UV is a fast, all-in-one Python package and project manager
- **UV automatically downloads and manages Python** - no separate Python installation needed!
- **10-100x faster** than pip for package installation
- **Install UV:**
  - **Windows:** `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - **macOS/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Alternative:** Visit [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/) for more installation options
- Verify installation: `uv --version`

> 💡 **Note:** UV will automatically download Python 3.12+ when you run `uv sync`. No separate Python installation required!

### **Alternative: Traditional pip**

If you cannot use UV or strongly prefer pip:

- **Python 3.12 or higher** - Must be pre-installed
  - Check: `python --version` or `python3 --version`
  - Download: [python.org](https://www.python.org/downloads/)

> ⚠️ **Note:** Using pip requires manual Python installation and dependency management. We **strongly recommend UV** for the best experience.

### **Optional:**

- **Git** - Only needed if cloning the repository (not required for released downloads)
  - Download: [git-scm.com](https://git-scm.com/downloads)

[⬆️ Back to Top](#table-of-contents)

---

<a id="quick-start" />

## 🚀 Quick Start

> 💡 **New user?** Make sure you've completed the [Prerequisites](#prerequisites) first!

### 🧙‍♂️ Quick Start (Web UI)

**Getting Started in 3 Minutes:**

1. **Download** the latest release from [GitHub Releases](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases)
2. **Extract** the archive to your desired location
3. **Install dependencies** (first time only):

   **With UV (recommended):**

   ```bash
   cd ArcaneAuditor
   uv sync
   ```

   **With pip (Python 3.12+ required):**

   ```bash
   cd ArcaneAuditor
   pip install -r requirements.txt
   ```
4. **Run** the web interface:

   ```bash
   # Windows
   start-web-service.bat

   # Linux/macOS
   ./start-web-service.sh
   ```

   *The script automatically opens your browser!*
5. **Open** [http://localhost:8080](http://localhost:8080) in your browser (if not auto-opened)
6. **Upload** your ZIP file or individual PMD/Pod/Script files
7. **Review** the analysis results and download Excel reports

---

### ⚔️ Quick Start (Command Line)

**With UV (recommended):**

```bash
# First time: install dependencies
cd ArcaneAuditor
uv sync

# Analyze a complete application archive
uv run main.py review-app myapp.zip

# Analyze individual files
uv run main.py review-app file1.pmd file2.pod file3.script

# Use specific configuration
uv run main.py review-app myapp.zip --config my-config.json
```

**With pip:**

```bash
# First time: install dependencies (Python 3.12+ required)
cd ArcaneAuditor
pip install -r requirements.txt

# Analyze files (use 'python' instead of 'uv run')
python main.py review-app myapp.zip
```

💡 **Want to contribute?** See [Development Setup](#development) for setting up a development environment.

[⬆️ Back to Top](#table-of-contents)

---

<a id="installation-options" />

## 📦 Installation Options

<a id="option-a-direct-download" />

### Option A: Direct Download (Recommended for Users)

**Best for:** Running Arcane Auditor without modifying the code

1. Download the latest release from [GitHub Releases](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases)
2. Extract the archive to your desired location
3. Open a terminal in the extracted directory
4. Install dependencies:
   ```bash
   uv sync
   ```
5. You're ready! See [Quick Start](#quick-start) for usage examples

<a id="option-b-clone-repository" />

### Option B: Clone Repository (Recommended for Contributors)

**Best for:** Contributing to Arcane Auditor or staying on the latest development version

```bash
# Clone the repository
git clone https://github.com/Developers-and-Dragons/ArcaneAuditor.git
cd ArcaneAuditor

# Install dependencies with UV (recommended)
uv sync

# Optional: Install development dependencies for testing
uv sync --dev

# Optional: Run tests to verify installation
uv run pytest
```

<a id="option-c-pip-installation" />

### Option C: Traditional pip Installation

**Best for:** Users who cannot use UV or work in restricted environments

> ⚠️ **Note:** We **strongly recommend UV** (Option A or B) for the best experience. UV is faster, easier, and handles Python installation automatically.

**Requirements:** Python 3.12+ must be pre-installed

```bash
# Download and extract the release, or clone the repository
git clone https://github.com/Developers-and-Dragons/ArcaneAuditor.git
cd ArcaneAuditor

# Install dependencies with pip
pip install -r requirements.txt

# Run the tool (without 'uv run' prefix)
python main.py review-app myapp.zip

# Or start the web interface
python web/server.py --port 8080
```

[⬆️ Back to Top](#table-of-contents)

<a id="web-interface" />

## 🌐 Arcane Auditor Web User Interface

*For most users, this is the easiest way to run Arcane Auditor.*

The web interface provides a modern, intuitive way to analyze your Workday Extend applications:

### **Features:**

- **📁 Drag & Drop Upload**: Easy file selection with support for ZIP archives and individual files
- **⚙️ Configuration Selection**: Choose from predefined analysis configurations
- **📊 Real-time Results**: Quick analysis with detailed violation reports
- **📥 Excel Export**: Download comprehensive reports with context information
- **🌙 Theme Support**: Dark and light mode themes

### **Starting the Web Server:**

Use the provided startup scripts for the easiest launch experience:

**Windows:**

```bash
# Start with defaults (auto-opens browser on http://127.0.0.1:8080)
start-web-service.bat

# Start on custom port
start-web-service.bat --port 3000

# Start without opening browser
start-web-service.bat --no-browser

# View all options
start-web-service.bat --help
```

**Linux/macOS:**

```bash
# Make script executable (first time only)
chmod +x start-web-service.sh

# Start with defaults (auto-opens browser on http://127.0.0.1:8080)
./start-web-service.sh

# Start on custom port
./start-web-service.sh --port 3000

# Start on all network interfaces
./start-web-service.sh --host 0.0.0.0

# Start without opening browser
./start-web-service.sh --no-browser

# View all options
./start-web-service.sh --help
```

> 💡 **Tip:** The startup scripts automatically use UV and open your browser - perfect for quick launches!
>
> 📖 **More details:** See [WEB_SERVICE_SCRIPTS.md](WEB_SERVICE_SCRIPTS.md) for advanced options and troubleshooting.

> 💡 **Tip:** The web interface provides intelligent [context awareness](#context-awareness) to help you understand when analysis is complete or partial.

<details>
<summary>🔗 API Endpoints (click to expand)</summary>

- `GET /` - Main interface
- `POST /upload` - File upload endpoint
- `GET /job/{job_id}` - Job status
- `GET /download/{job_id}/excel` - Download Excel report
- `GET /configurations` - Available configurations
- `GET /static/{file}` - Static assets (CSS, JS, images)

</details>

[⬆️ Back to Top](#table-of-contents)

<a id="context-awareness" />

## 🧠 Context Awareness

<details>
<summary>🧠 Context Awareness (click to expand)</summary>

Arcane Auditor provides **intelligent context awareness** to help you understand when analysis is complete or partial:

| Mode     | Description                | Example Command (UV)                     | Example Command (pip)                    |
| -------- | -------------------------- | ---------------------------------------- | ---------------------------------------- |
| Complete | Full set of files provided | `uv run main.py review-app myapp.zip`  | `python main.py review-app myapp.zip`  |
| Partial  | Missing AMD or SMD files   | `uv run main.py review-app mypage.pmd` | `python main.py review-app mypage.pmd` |

### **Complete Analysis** ✅

When you provide all relevant files (PMD, AMD, SMD), Arcane Auditor runs **all enabled validation rules** and provides comprehensive coverage.

### **Partial Analysis** ⚠️

When files are missing, Arcane Auditor:

- **Runs available rules** on provided files
- **Clearly indicates** which files are missing
- **Shows which rules** couldn't be executed
- **Provides guidance** on what to add for complete validation

### **Supported Analysis Modes**

**ZIP File Analysis:**

```bash
# With UV (recommended)
uv run main.py review-app myapp.zip

# With pip
python main.py review-app myapp.zip
```

**Individual File Analysis:**

```bash
# With UV - Single PMD file
uv run main.py review-app mypage.pmd

# With UV - Multiple files
uv run main.py review-app file1.pmd file2.pod file3.script

# With pip - Single PMD file
python main.py review-app mypage.pmd

# With pip - Multiple files
python main.py review-app file1.pmd file2.pod file3.script
```

> ⚠️ **Note:** You cannot currently mix ZIP files with additional individual files in a single command. Choose either ZIP analysis or individual file analysis.

### **Context Information Display**

The tool provides clear context information in all output formats:

**Console Output:**

```
📊 Analysis Context:
✅ Complete Analysis - All files provided
📁 Files Analyzed: 15
📄 Files Present: 15
⚠️ Files Missing: 0
🔧 Rules Executed: 45
```

**Excel Reports:**

- Dedicated "Context" sheet with analysis completeness
- Clear indication of missing files and their impact
- Guidance on achieving complete analysis

**Web Interface:**

- Context panel showing analysis status
- Visual indicators for complete vs. partial analysis
- Recommendations for improving analysis coverage

[⬆️ Back to Top](#table-of-contents)

</details>

<a id="configuration-system" />

## 🛡️ Update-Safe Configuration System

<details>
<summary>🛡️ Update-Safe Configuration System (click to expand)</summary>

Arcane Auditor uses a **layered configuration system** that protects your customizations during updates:

### **Built-in Configuration Presets:**

- **`development`** - Dev-friendly validation focusing on structure and standards

  - Disables rules that flag work-in-progress code (console logs, unused code, dead code)
  - Perfect for daily coding without noise
- **`production-ready`** - Comprehensive validation for pre-deployment

  - All rules enabled with strict settings
  - Catches all issues including cleanup items (console logs, unused code)

> ⚠️ **Important:** Only the built-in configurations in `config/presets/` are **NOT update-safe** and will be overwritten during updates. **Do not modify these files directly!** Instead, create your own configurations in `config/personal/` or `config/teams/` for your customizations.

> 📖 **Full details:** See [Configuration Guide](config/README.md) for presets, team configs, and personal overrides

### **Configuration Layers (Priority Order):**

1. **Command Line Arguments** (highest priority)
2. **Personal Configuration** (`config/personal/*.json`) - ✅ **Update-safe**
3. **Team Configuration** (`config/teams/*.json`) - ✅ **Update-safe**
4. **Built-in Presets** (`config/presets/*.json`) - ⚠️ **Not update-safe** (delivered configurations)

### **Configuration File Structure:**

```json
{
  "rules": {
    "ScriptComplexityRule": {
      "enabled": true,
      "severity_override": null,
      "custom_settings": {}
    },
    "ScriptLongFunctionRule": {
      "enabled": true,
      "severity_override": null,
      "custom_settings": {}
    },
    "ScriptConsoleLogRule": {
      "enabled": false,
      "severity_override": null,
      "custom_settings": {}
    },
    "ScriptLongBlockRule": {
      "enabled": true,
      "severity_override": "ADVICE",
      "custom_settings": {
        "max_lines": 50
      }
    }
  },
  "file_processing": {
    "max_file_size": 52428800,
    "encoding": "utf-8",
    "log_level": "INFO"
  },
  "output": {
    "format": "text",
    "include_rule_details": true,
    "sort_by_severity": true
  },
  "fail_on_error": false,
  "fail_on_warning": false
}
```

### **Creating Custom Configurations:**

> ✅ **Best Practice:** Always create your custom configurations in one of these update-safe locations:
>
> - `config/personal/` directory (for personal customizations)
> - `config/teams/` directory (for team-wide configurations)
> - A custom file outside the project (for project-specific configs)
> - Use `--config` flag with a custom config file

**Option 1: Generate a custom config file (recommended for project-specific settings):**

**With UV (recommended):**

```bash
# Generate default configuration
uv run main.py generate-config > config/personal/my-config.json

# Use custom configuration
uv run main.py review-app myapp.zip --config my-config.json
```

**With pip:**

```bash
# Generate default configuration
python main.py generate-config > config/personal/my-config.json

# Use custom configuration
python main.py review-app myapp.zip --config my-config.json
```

**Option 2: Create a personal or team override (recommended for persistent preferences):**

1. Create a file in `config/personal/` for personal settings, or `config/teams/` for team-wide settings
2. Add only the settings you want to override
3. The tool will automatically use it (these configs are loaded automatically)

**Example personal config** (`config/personal/my-settings.json`):

```json
{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": false
    },
    "ScriptUnusedFunctionRule": {
      "enabled": false
    }
  }
}
```

**Example team config** (`config/teams/my-team.json`):

```json
{
  "rules": {
    "ScriptLongBlockRule": {
      "enabled": true,
      "severity_override": "ACTION",
      "custom_settings": {
        "max_lines": 75
      }
    },
    "ScriptDeadCodeRule": {
      "enabled": true
    }
  },
  "fail_on_warning": true
}
```

### **Configuration Inheritance:**

- **User config** inherits from **default config**
- **Project config** inherits from **user config**
- **Command line** overrides all config files
- **Missing settings** fall back to defaults

This ensures your customizations persist through updates while allowing flexibility for different projects.

[⬆️ Back to Top](#table-of-contents)

</details>

<a id="validation-rules" />

## 🔧 Validation Rules

### Categories

- 🧠 [Script Quality Rules](parser/rules/RULE_BREAKDOWN.md#-script-rules)
- 🏗️ [Structure Validation Rules](parser/rules/RULE_BREAKDOWN.md#-structure-rules)
- ⚙️ [Custom Rule Development](parser/rules/custom/README.md)

<details>
<summary>🔧 Script Quality Rules (click to expand)</summary>

### **Script Syntax & Structure**

- **Valid JavaScript Syntax**: Ensures all script code follows proper JavaScript syntax
- **Function Declaration Validation**: Validates function declarations and their parameters
- **Variable Declaration**: Checks for proper variable declarations and scope
- **Control Flow Validation**: Validates if/else, loops, and other control structures

### **Code Complexity & Quality**

- **Cyclomatic Complexity**: Measures code complexity (default threshold: 10)
- **Function Length**: Limits function length (default: 50 lines)
- **Nested Depth**: Prevents excessive nesting (default: 4 levels)
- **Code Duplication**: Detects repeated code patterns

### **Naming Conventions**

- **Function Naming**: Enforces camelCase for function names
- **Variable Naming**: Ensures consistent variable naming
- **Constant Naming**: Validates constant naming conventions
- **Parameter Naming**: Checks parameter naming consistency

### **Unused Code Detection**

- **Unused Functions**: Identifies functions that are never called in embedded PMD/Pod scripts
- **Unused Variables**: Finds variables that are declared but never used
- **Dead Code**: Validates export patterns in standalone `.script` files (checks all declared variables)
- **Unused Parameters**: Identifies function parameters that aren't used

[⬆️ Back to Top](#table-of-contents)

</details>

<details>
<summary>🔧 Structure Validation Rules (click to expand)</summary>

### **Widget Configuration**

- **Required Fields**: Ensures all required widget fields are present
- **Field Validation**: Validates field types and constraints
- **Widget Hierarchy**: Checks proper widget nesting and relationships
- **Component Validation**: Validates component configurations

### **PMD File Structure**

- **Page Definition**: Validates page structure and metadata
- **Endpoint Configuration**: Checks endpoint definitions and parameters
- **Presentation Layer**: Validates UI component configurations
- **Data Binding**: Ensures proper data binding configurations

### **Pod File Validation**

- **Template Structure**: Validates pod template structure
- **Widget Definitions**: Checks widget definitions and properties
- **Endpoint Integration**: Validates endpoint connections
- **Data Flow**: Ensures proper data flow between components

### **Best Practices**

- **Hardcoded Values**: Detects hardcoded values that should be configurable
- **Security Practices**: Validates security-related configurations
- **Performance Optimization**: Checks for performance-related issues
- **Accessibility**: Validates accessibility compliance

[⬆️ Back to Top](#table-of-contents)

</details>

<details>
<summary>🔧 Custom Rule Development (click to expand)</summary>

### **Creating Custom Rules**

Arcane Auditor supports custom rule development through **automatic discovery**. Simply create your rule in `parser/rules/custom/user/` and it will be automatically discovered and loaded!

**Example custom rule** (`parser/rules/custom/user/my_custom_rule.py`):

```python
from parser.rules.base import Rule, Finding
from parser.models import ProjectContext
from typing import Generator

class MyCustomScriptRule(Rule):
    """Custom validation rule for my organization."""
    
    ID = "CUSTOM001"
    DESCRIPTION = "Checks for organization-specific patterns"
    SEVERITY = "ADVICE"
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze all PMD files in the project."""
        for pmd_model in context.pmd_models:
            # Your custom validation logic here
            if self._check_condition(pmd_model):
                yield Finding(
                    rule_id=self.ID,
                    message="Custom validation issue found",
                    file_path=pmd_model.file_path,
                    line=1,
                    severity=self.SEVERITY,
                    details="Additional context here"
                )
    
    def _check_condition(self, pmd_model):
        # Your logic here
        return False
```

### **How Rule Discovery Works**

Rules are **automatically discovered** by the `RulesEngine`:

1. All subclasses of `Rule` in the `parser/rules/` package are found automatically
2. Rules in `parser/rules/custom/user/` are included in discovery
3. Only **enabled** rules (in your config) are loaded and executed
4. No manual registration needed!

### **Rule Configuration**

Enable or configure your custom rules in your configuration file:

```json
{
  "rules": {
    "MyCustomScriptRule": {
      "enabled": true,
      "severity_override": "ACTION",
      "custom_settings": {
        "threshold": 5
      }
    }
  }
}
```

> 📖 **Full documentation:** See [Custom Rules Guide](parser/rules/custom/README.md) for complete examples and best practices.

[⬆️ Back to Top](#table-of-contents)

</details>

<a id="development" />

## 🛠️ Development

<details>
<summary>🛠️ Development Setup (click to expand)</summary>

### **Setup Development Environment**

> 💡 **Before starting:** Make sure you've completed the [Prerequisites](#prerequisites) section, including installing UV and Git.

**Quick Development Setup:**

```bash
# Clone repository
git clone https://github.com/Developers-and-Dragons/ArcaneAuditor.git
cd ArcaneAuditor

# Install dependencies (including development dependencies)
uv sync --dev

# Run tests to verify installation
uv run pytest
```

**What's included with `--dev`:**

- All production dependencies
- Testing frameworks (pytest)
- Code quality tools
- Development utilities

### **Project Structure**

**Project Structure Overview**

```
arcane_auditor/   → Core validation engine
web/              → Web interface (FastAPI + frontend)
tests/            → Automated test suite
config/           → Presets, team, and personal configs
docs/             → Detailed documentation and rule breakdowns
```

> 🧩 **New contributor?** See [Project Structure](docs/project-structure.md) for an overview of core directories and their roles.

<details>
<summary>📁 Detailed Project Structure (click to expand)</summary>

```
ArcaneAuditor/
├── main.py                  # CLI entry point
├── parser/                  # File parsing and rules
│   ├── __init__.py
│   ├── app_parser.py       # Application file parser
│   ├── pmd_script_parser.py # PMD script parser
│   ├── models.py           # Data models
│   ├── config.py           # Configuration models
│   ├── config_manager.py   # Configuration loader
│   ├── rules_engine.py     # Rules discovery and execution
│   └── rules/              # Validation rules
│       ├── base.py         # Base rule classes
│       ├── script/         # Script validation rules
│       ├── structure/      # Structure validation rules
│       └── custom/         # Custom rule support
│           ├── examples/   # Example custom rules
│           └── user/       # Your custom rules
├── file_processing/         # File handling
│   ├── processor.py        # File processor
│   ├── context_tracker.py  # Context awareness
│   └── models.py           # Processing models
├── output/                  # Output formatting
│   └── formatter.py        # Console/Excel output
├── web/                     # Web interface
│   ├── server.py           # FastAPI server
│   └── frontend/           # Frontend assets
│       ├── index.html      # Main HTML
│       ├── style.css       # Styling
│       └── script.js       # JavaScript
├── config/                  # Configuration files
│   ├── presets/            # Built-in presets (not update-safe)
│   ├── teams/              # Team configs (update-safe)
│   └── personal/           # Personal configs (update-safe)
├── tests/                   # Test suite
│   ├── test_rules_engine.py
│   ├── test_app_parser.py
│   └── [many test files]
├── samples/                 # Sample files
│   ├── templates/          # Template files
│   └── archives/           # Sample archives
├── assets/                  # Static assets
│   └── [screenshots]
├── start-web-service.bat   # Windows startup script
├── start-web-service.sh    # Linux/macOS startup script
├── pyproject.toml          # Project configuration
├── requirements.txt        # Pip dependencies
├── README.md               # This file
└── LICENSE                 # License
```

</details>

### **Running Tests**

**With UV (recommended):**

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_app_parser.py
```

**With pip:**

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_app_parser.py
```

<a id="contributing" />

### **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `uv run pytest` (or `pytest` if using pip)
6. Commit your changes: `git commit -m "Add feature"`
7. Push to your fork: `git push origin feature-name`
8. Create a Pull Request

> 💡 **Tip:** We recommend using UV for development - it's faster and ensures consistent Python environments across all contributors.

### **Code Style**

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Include unit tests for new features
- Use meaningful commit messages

[⬆️ Back to Top](#table-of-contents)

</details>

[⬆️ Back to Top](#table-of-contents)

<a id="documentation" />

## 📚 Documentation

- **[Rule Documentation](parser/rules/RULE_BREAKDOWN.md)** - Detailed rule descriptions and examples
- **[Custom Rules Guide](parser/rules/custom/README.md)** - Custom rule development guide
- **[Configuration Guide](config/README.md)** - Configuration options and examples

<a id="license" />

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

⭐ **If Arcane Auditor helps you, star the repo and share the magic!**

*May the Weave guide your code to perfection!* ✨
