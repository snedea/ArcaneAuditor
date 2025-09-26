# User Configurations Directory 🛡️

*Update-safe configurations for teams and projects*

## 🎯 Purpose

This directory is **protected from application updates** and is the recommended location for:
- **Team configurations** - Shared across your development team
- **Project-specific rules** - Customized for specific applications
- **Organizational standards** - Company-wide coding standards
- **Web interface integration** - Configurations automatically appear in the web UI

## 🔒 Update Safety

✅ **Safe:** Files in this directory will **never** be overwritten during Arcane Auditor updates  
✅ **Persistent:** Your customizations survive app updates  
✅ **Shareable:** Can be committed to your project's version control  

## 📁 Directory Structure

```
user_configs/
├── README.md              # This file
├── examples/              # Example configurations to copy/modify
│   ├── team-standard.json # Example team configuration
│   └── beginner-friendly.json # Example beginner configuration
├── my-team-config.json    # Your team's configuration
└── project-specific.json  # Project-specific rules
```

## 🚀 Quick Start

### 1. Copy an Example Configuration
```bash
# Copy an example to start with
cp user_configs/examples/team-standard.json user_configs/my-config.json
```

### 2. Customize Your Configuration
Edit `user_configs/my-config.json` to match your team's needs:

```json
{
  "rules": {
    "ScriptComplexityRule": {
      "enabled": true,
      "severity_override": "SEVERE",
      "custom_settings": {
        "max_complexity": 8
      }
    },
    "PMDSectionOrderingRule": {
      "enabled": true,
      "custom_settings": {
        "section_order": ["id", "presentation", "endPoints", "script"],
        "enforce_order": true
      }
    }
  }
}
```

### 3. Use Your Configuration

#### Web Interface
1. Go to the Arcane Auditor web interface
2. Look for your configuration in the **Team Configurations** section
3. Select your configuration and upload your ZIP file

#### Command Line
```bash
# Use your custom configuration
uv run main.py review-app myapp.zip --config my-config

# Or specify the full path
uv run main.py review-app myapp.zip --config user_configs/my-config.json
```

## 🎯 Configuration Examples

### Team Standard Configuration
Perfect for enforcing team-wide coding standards:
```json
{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": true,
      "severity_override": "SEVERE"
    },
    "ScriptNullSafetyRule": {
      "enabled": true,
      "severity_override": "SEVERE"
    },
    "PMDSectionOrderingRule": {
      "enabled": true,
      "severity_override": "WARNING",
      "custom_settings": {
        "section_order": ["id", "securityDomains", "endPoints", "presentation", "onLoad", "onSubmit", "outboundData", "include", "script"],
        "enforce_order": true
      }
    }
  }
}
```

### Beginner-Friendly Configuration
Focuses on essential rules for new developers:
```json
{
  "rules": {
    "ScriptNullSafetyRule": {
      "enabled": true,
      "severity_override": "SEVERE"
    },
    "ScriptConsoleLogRule": {
      "enabled": true,
      "severity_override": "WARNING"
    },
    "ScriptEmptyFunctionRule": {
      "enabled": true,
      "severity_override": "INFO"
    },
    "WidgetIdRequiredRule": {
      "enabled": true,
      "severity_override": "SEVERE"
    }
  }
}
```

## 🔧 Advanced Usage

### Configuration Layering
Configurations are loaded in priority order:
1. **Local configs** (`local_configs/`) - Highest priority
2. **User configs** (`user_configs/`) - Your customizations
3. **App configs** (`configs/`) - Default settings

### Partial Configurations
You only need to specify rules you want to override:
```json
{
  "rules": {
    "ScriptLongFunctionRule": {
      "custom_settings": {
        "max_lines": 75
      }
    }
  }
}
```

## 📚 Best Practices

### ✅ Do:
- Create descriptive configuration names
- Document your team's configuration choices
- Start with an example configuration
- Test configurations before sharing with team
- Commit user configurations to your project repository

### ❌ Don't:
- Edit files in `configs/` directory (they get overwritten)
- Create overly complex configurations
- Disable critical safety rules without team discussion

## 🆘 Need Help?

- Check `examples/` directory for configuration templates
- See `configs/README.md` for complete rule documentation
- Review `RULE_BREAKDOWN.md` for detailed rule explanations

Your configurations in this directory are **completely safe** from application updates! 🛡️✨
