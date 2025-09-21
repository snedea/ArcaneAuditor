# Local Configurations Directory 🏠

*Personal developer settings and overrides*

## 🎯 Purpose

This directory is for **personal developer configurations** that:
- Override team or project settings for local development
- Store personal preferences and workflow customizations
- Provide temporary rule adjustments for debugging/prototyping
- **Never get committed** to version control

## 🔒 Privacy & Safety

✅ **Private:** Files here are never committed to git  
✅ **Safe:** Protected from application updates  
✅ **Personal:** Your individual development preferences  
✅ **Temporary:** Perfect for quick rule adjustments  

## 🚀 Common Use Cases

### Development Mode Overrides
```json
{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": false
    },
    "ScriptLongFunctionRule": {
      "custom_settings": {
        "max_lines": 200
      }
    }
  }
}
```

### Debugging Configuration
```json
{
  "rules": {
    "ScriptComplexityRule": {
      "enabled": false
    },
    "ScriptNestingLevelRule": {
      "enabled": false
    }
  }
}
```

### Personal Preferences
```json
{
  "rules": {
    "PMDSectionOrderingRule": {
      "enabled": false
    },
    "ScriptVariableNamingRule": {
      "severity_override": "INFO"
    }
  }
}
```

## 📁 Usage Examples

### Create Personal Override
```bash
# Create your personal configuration
echo '{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": false,
      "custom_settings": {}
    }
  }
}' > local_configs/dev-mode.json
```

### Use Personal Configuration
```bash
# Use your personal config (highest priority)
uv run main.py review-app myapp.zip --config dev-mode

# Or full path
uv run main.py review-app myapp.zip --config local_configs/dev-mode.json
```

## 🎯 Configuration Priority

When you specify a configuration name, the system searches in order:
1. **`local_configs/name.json`** ← **Highest Priority** (Your personal settings)
2. `user_configs/name.json` ← Team/project settings
3. `configs/name.json` ← App default settings

This means your local configurations **always win**! 🏆

## 📚 Best Practices

### ✅ Do:
- Use descriptive names for your configurations
- Create temporary configs for specific debugging sessions
- Override only the rules you need to change
- Document complex personal configurations

### ❌ Don't:
- Commit files in this directory to version control
- Create permanent configurations here (use `user_configs/` instead)
- Share local configurations with teammates
- Disable critical safety rules permanently

## 🛠️ Quick Configuration Templates

### Minimal Validation (Prototyping)
```json
{
  "rules": {
    "ScriptConsoleLogRule": { "enabled": false },
    "ScriptComplexityRule": { "enabled": false },
    "ScriptLongFunctionRule": { "enabled": false },
    "ScriptNestingLevelRule": { "enabled": false }
  }
}
```

### Focus on Critical Issues Only
```json
{
  "rules": {
    "ScriptNullSafetyRule": { "enabled": true, "severity_override": "SEVERE" },
    "ScriptEmptyFunctionRule": { "enabled": true },
    "WidgetIdRequiredRule": { "enabled": true, "severity_override": "SEVERE" }
  }
}
```

## 🔄 Temporary Configurations

Perfect for temporary rule adjustments:
```bash
# Create a quick debugging config
echo '{"rules":{"ScriptConsoleLogRule":{"enabled":false}}}' > local_configs/debug.json

# Use it
uv run main.py review-app myapp.zip --config debug

# Remove when done
rm local_configs/debug.json
```

Your personal configurations are **completely private** and will never interfere with team settings! 🏠✨
