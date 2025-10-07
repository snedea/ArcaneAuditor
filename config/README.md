# Arcane Auditor Configuration Guide 📜

This directory contains all configuration files for the Arcane Auditor in a consolidated structure.

## 📁 Directory Structure

```
config/
├── README.md              # This guide
├── presets/               # Built-in configurations (app defaults)
│   ├── development.json   # Development-friendly validation
│   └── production-ready.json # Pre-deployment validation
├── teams/                 # Team/project configurations
│   └── [your-team-configs.json]
└── personal/              # Personal overrides (gitignored)
    └── README.md         # Personal configuration guide
```

## 🎯 Configuration Types

### Presets (config/presets/)

Built-in configurations that come with the application:

- **development.json** - Development-friendly validation with relaxed settings

  - Console log detection disabled (allows debugging output)
  - Complexity rules relaxed (allows longer functions during prototyping)
  - Critical safety rules enabled (null safety, empty functions, etc.)
  - **Use case**: Daily development, debugging, prototyping
- **production-ready.json** - Pre-deployment validation with strict settings

  - All rules enabled with strict settings
  - Console log detection enabled (ensures no debug output)
  - Strict complexity limits (enforces clean, maintainable code)
  - **Use case**: Pre-deployment validation, CI/CD pipelines, production code reviews

### Team Configurations (config/teams/)

Team and project-specific configurations:

- Shared across your development team
- Committed to version control
- Customized for specific projects or organizational standards
- **Protected from app updates** - your customizations survive app releases

### Personal Configurations (config/personal/)

Personal developer overrides:

- Never committed to version control
- Highest priority (overrides team and preset configs)
- Perfect for debugging and personal preferences
- **Completely private** - only visible to you

## 🚀 Usage

### Command Line

```bash
# Use development configuration (recommended for daily development)
uv run main.py review-app myapp.zip --config development

# Use production-ready configuration (pre-deployment validation)
uv run main.py review-app myapp.zip --config production-ready

# Use a team configuration
uv run main.py review-app myapp.zip --config my-team-config

# Use a personal configuration
uv run main.py review-app myapp.zip --config my-local-config
```

### Web Interface

Configurations are automatically discovered and available in the web interface under:

- **Built-in Configurations** (presets)
- **Team Configurations** (teams)
- **Personal Configurations** (personal)

## 📊 Configuration Priority

When you specify a configuration name, the system searches in this order:

1. `config/personal/name.json` ← **Highest Priority** (Personal overrides)
2. `config/teams/name.json` ← Team/project settings
3. `config/presets/name.json` ← App defaults

## 🛠️ Creating Custom Configurations

### Team Configuration

```bash
# Copy a preset as starting point
cp config/presets/development.json config/teams/my-team-config.json

# Edit the configuration to match your team's standards
# ... customize rules as needed ...

# Use it
uv run main.py review-app myapp.zip --config my-team-config
```

### Personal Configuration

```bash
# Create personal override
echo '{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": false
    }
  }
}' > config/personal/debug-mode.json

# Use it
uv run main.py review-app myapp.zip --config debug-mode
```

## 🔒 App Update Safety

- **Presets** (`config/presets/`) - App-managed, updated with releases
- **Teams** (`config/teams/`) - Protected by `.gitignore`, never overwritten
- **Personal** (`config/personal/`) - Completely ignored by git, always preserved

Your team and personal configurations will **never be overwritten** during app updates!

## 📚 Additional Resources

- [Rule Documentation](../parser/rules/RULE_BREAKDOWN.md) - Detailed rule descriptions
- [Custom Rules Guide](../parser/rules/custom/README.md) - Creating custom validation rules
- [Web Interface](../web/README.md) - Web-based analysis interface
