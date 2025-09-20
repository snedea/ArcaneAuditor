# Arcane Auditor Configuration System Design 🧙‍♂️

## 🎯 Problem Statement

Current configuration system has update safety issues:
- Config files in `configs/` are part of the application
- User customizations get overwritten during app updates
- No separation between app-provided and user-created configurations

## 🏗️ Proposed Solution: Layered Configuration System

### Directory Structure
```
arcane-auditor/
├── configs/                    # 🔒 App-managed (never touch after install)
│   ├── default.json           # Base configuration
│   ├── minimal.json           # Minimal rule set
│   ├── comprehensive.json     # All rules with strict settings
│   └── README.md              # Documentation
│
├── user_configs/              # 🛡️ User-managed (update-safe)
│   ├── .gitignore             # Exclude from git
│   ├── README.md              # User guidance
│   └── examples/              # Example configurations
│       ├── team-standard.json # Example team config
│       └── beginner-friendly.json # Example beginner config
│
└── local_configs/             # 🏠 Local overrides (update-safe)
    ├── .gitignore             # Exclude from git
    └── README.md              # Local config guidance
```

### Configuration Loading Priority (Highest to Lowest)
1. **Local Config** (`local_configs/my-config.json`) - Highest priority
2. **User Config** (`user_configs/my-config.json`) - User customizations
3. **App Config** (`configs/default.json`) - App defaults

### Configuration Types

#### 1. 🔒 **App-Managed Configs** (`configs/`)
- **Never modified after initial install**
- Provides stable base configurations
- Updated only through app releases
- Users should **never** edit these directly

#### 2. 🛡️ **User Configs** (`user_configs/`)
- **User-created configurations**
- Protected from app updates
- Can extend or override app configs
- Ideal for team standards, project-specific rules

#### 3. 🏠 **Local Configs** (`local_configs/`)
- **Developer-specific overrides**
- Highest priority (overrides everything)
- Perfect for personal preferences
- Never committed to version control

## 🔧 Implementation Strategy

### Phase 1: Directory Structure
```bash
# Create user-safe directories
mkdir user_configs
mkdir user_configs/examples
mkdir local_configs

# Add .gitignore files to protect user customizations
echo "# User configurations - protected from updates" > user_configs/.gitignore
echo "*.json" >> user_configs/.gitignore
echo "!examples/" >> user_configs/.gitignore

echo "# Local configurations - personal settings" > local_configs/.gitignore
echo "*" >> local_configs/.gitignore
echo "!.gitignore" >> local_configs/.gitignore
echo "!README.md" >> local_configs/.gitignore
```

### Phase 2: Configuration Loading Logic
```python
class ConfigurationManager:
    def load_config(self, config_name: str = None) -> ExtendReviewerConfig:
        # Priority order: local > user > app
        config_sources = [
            f"local_configs/{config_name}.json",      # Highest priority
            f"user_configs/{config_name}.json",       # User customizations
            f"configs/{config_name or 'default'}.json" # App defaults
        ]
        
        base_config = None
        for config_path in reversed(config_sources):  # Start with lowest priority
            if Path(config_path).exists():
                if base_config is None:
                    base_config = ExtendReviewerConfig.from_file(config_path)
                else:
                    # Merge configurations (higher priority overrides lower)
                    overlay_config = ExtendReviewerConfig.from_file(config_path)
                    base_config = self.merge_configs(base_config, overlay_config)
        
        return base_config or ExtendReviewerConfig()  # Fallback to defaults
```

### Phase 3: Configuration Merging
```python
def merge_configs(self, base: ExtendReviewerConfig, overlay: ExtendReviewerConfig) -> ExtendReviewerConfig:
    """Merge two configurations, with overlay taking priority."""
    # Deep merge logic:
    # - Rule-level: overlay rules override base rules completely
    # - Setting-level: overlay settings override base settings
    # - Custom settings: deep merge dictionaries
    
    merged_rules = {}
    
    # Start with base rules
    for rule_name, rule_config in base.rules.__dict__.items():
        merged_rules[rule_name] = rule_config
    
    # Override with overlay rules
    for rule_name, rule_config in overlay.rules.__dict__.items():
        if rule_config.enabled or rule_config.severity_override or rule_config.custom_settings:
            merged_rules[rule_name] = rule_config
    
    # Create new merged configuration
    return ExtendReviewerConfig(rules=RulesConfig(**merged_rules))
```

## 🎯 Usage Examples

### Example 1: Team Configuration
```json
// user_configs/team-standard.json
{
  "rules": {
    "ScriptComplexityRule": {
      "enabled": true,
      "severity_override": "ERROR",
      "custom_settings": {
        "max_complexity": 8  // Stricter than default 10
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

### Example 2: Personal Override
```json
// local_configs/my-preferences.json
{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": false  // Disable for local development
    },
    "ScriptLongFunctionRule": {
      "custom_settings": {
        "max_lines": 100  // More lenient for prototyping
      }
    }
  }
}
```

### Example 3: Command Line Usage
```bash
# Use team configuration
uv run main.py review-app myapp.zip --config team-standard

# Use personal configuration (looks in all directories)
uv run main.py review-app myapp.zip --config my-preferences

# Explicit path for user config
uv run main.py review-app myapp.zip --config user_configs/team-standard.json
```

## 🛡️ Update Safety Guarantees

### During App Updates:
✅ **Safe:** `user_configs/` - Never touched  
✅ **Safe:** `local_configs/` - Never touched  
⚠️ **Updated:** `configs/` - App-managed, may receive updates  

### User Benefits:
- 🔒 **No lost customizations** during updates
- 🎯 **Team configurations** survive app updates
- 🏠 **Personal preferences** remain intact
- 📚 **New app features** automatically available through base configs
- 🔄 **Easy migration** from old system

## 🚀 Migration Strategy

### For Existing Users:
1. **Backup existing custom configs**
2. **Move to `user_configs/`** directory
3. **Update references** in scripts/documentation
4. **Test configuration loading** with new system

### Backward Compatibility:
- Still support direct file paths: `--config configs/default.json`
- Warn users about update-unsafe locations
- Provide migration helper script

## 📚 Documentation Updates

### User Guidance:
- **Never edit `configs/`** - these get overwritten
- **Use `user_configs/`** for team/project configurations
- **Use `local_configs/`** for personal preferences
- **Configuration layering** explanation with examples

This design ensures user customizations are **completely protected** from app updates while maintaining all current functionality! 🎯✨
