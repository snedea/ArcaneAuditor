"""
Configuration loading service for Arcane Auditor.

Provides backend logic for discovering and processing configuration files.
"""

from pathlib import Path

from utils.arcane_paths import get_config_dirs
from utils.preferences_manager import get_new_rule_default_enabled
from utils.config_normalizer import get_production_rules, normalize_config_rules
from parser.rules_engine import RulesEngine
from parser.config import ArcaneAuditorConfig


def get_dynamic_config_info():
    """Dynamically discover configuration information from all config directories."""
    config_info = {}
    
    # Instantiate RulesEngine once at the top to get runtime rule names
    config = ArcaneAuditorConfig()
    engine = RulesEngine(config)
    runtime_rule_names = [rule.__class__.__name__ for rule in engine.rules]
    
    # Search in priority order: personal, teams, presets
    dirs = get_config_dirs()
    config_dirs = [
        Path(dirs["personal"]), 
        Path(dirs["teams"]), 
        Path(dirs["presets"])
    ]

    default_enabled = get_new_rule_default_enabled()
    production_rules = get_production_rules()
    
    for config_dir in config_dirs:
        if not config_dir.exists():
            continue
            
        # Search for JSON files in the directory (not subdirectories)
        for config_file in config_dir.glob("*.json"):
            config_name = config_file.stem
        
            try:
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                normalized_rules = normalize_config_rules(
                    config_data.get('rules', {}),
                    default_enabled=default_enabled,
                    runtime_rule_names=runtime_rule_names,
                    production_rules=production_rules,
                )

                # Count enabled rules
                enabled_rules = 0
                for rule_config in normalized_rules.values():
                    # Check if rule is explicitly enabled (defaults to True if not present)
                    is_enabled = rule_config.get('enabled', True)
                    if is_enabled:
                        enabled_rules += 1
                
                # Determine performance level based on rule count
                if enabled_rules <= 10:
                    performance = "Fast"
                elif enabled_rules <= 25:
                    performance = "Balanced"
                else:
                    performance = "Thorough"
                
                # Determine config type based on directory
                if config_dir.name == "personal":
                    config_type = "Personal"
                    description = f"Personal configuration with {enabled_rules} rules enabled"
                elif config_dir.name == "teams":
                    config_type = "Team"
                    description = f"Team configuration with {enabled_rules} rules enabled"
                elif config_dir.name == "presets":
                    config_type = "Built-in"
                    description = f"Built-in configuration with {enabled_rules} rules enabled"
                
                # Create unique key by combining config name with directory type
                # This allows showing all versions (personal, team, built-in) in the UI
                config_key = f"{config_name}_{config_dir.name}"
                config_info[config_key] = {
                    "name": config_name.replace('_', ' ').title(),
                    "description": description,
                    "rules_count": enabled_rules,
                    "total_rules": len(normalized_rules),
                    "performance": performance,
                    "type": config_type,
                    "path": str(config_file),
                    "id": config_key,  # Unique identifier combining name and source
                    "source": config_dir.name,  # Track which directory it came from
                    "rules": normalized_rules,  # Include normalized rules data
                }
                
            except Exception as e:
                print(f"Warning: Failed to load config {config_name}: {e}")
    
    return config_info

