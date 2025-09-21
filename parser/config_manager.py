"""
Configuration Manager for Arcane Auditor

Provides layered configuration loading with update-safe user configurations.
Configurations are loaded in priority order:
1. Local configs (local_configs/) - Highest priority, personal overrides
2. User configs (user_configs/) - User/team customizations  
3. App configs (configs/) - Application defaults

This ensures user customizations survive application updates.
"""
from pathlib import Path
from typing import Dict, Optional
from .config import ArcaneAuditorConfig


class ConfigurationManager:
    """Manages layered configuration loading with update-safe user configurations."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            base_path: Base directory path. Defaults to current working directory.
        """
        self.base_path = base_path or Path.cwd()
        
        # Configuration directory paths in priority order (highest to lowest)
        self.config_paths = [
            self.base_path / "local_configs",   # Highest priority - personal overrides
            self.base_path / "user_configs",    # User/team customizations
            self.base_path / "configs"          # Lowest priority - app defaults
        ]
    
    def load_config(self, config_name: Optional[str] = None) -> ArcaneAuditorConfig:
        """Load configuration with layered priority system.
        
        Args:
            config_name: Configuration name (without .json extension) or full path.
                        If None, loads 'default' configuration.
        
        Returns:
            Merged ArcaneAuditorConfig with all applicable layers applied.
        """
        # Handle explicit file paths
        if config_name and ('/' in config_name or '\\' in config_name or config_name.endswith('.json')):
            config_path = Path(config_name)
            if config_path.exists():
                return ArcaneAuditorConfig.from_file(str(config_path))
            else:
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Use default if no name provided
        config_name = config_name or "default"
        
        # Find all applicable configuration files in priority order
        config_files = []
        for config_dir in self.config_paths:
            config_file = config_dir / f"{config_name}.json"
            if config_file.exists():
                config_files.append(config_file)
        
        if not config_files:
            # Fallback to default configuration
            default_config_file = self.base_path / "configs" / "default.json"
            if default_config_file.exists():
                return ArcaneAuditorConfig.from_file(str(default_config_file))
            else:
                # Ultimate fallback - use built-in defaults
                return ArcaneAuditorConfig()
        
        # Load and merge configurations (lowest priority first)
        merged_config = None
        for config_file in reversed(config_files):  # Start with lowest priority
            try:
                if merged_config is None:
                    # First configuration becomes the base
                    merged_config = ArcaneAuditorConfig.from_file(str(config_file))
                else:
                    # Merge higher priority configuration over base
                    overlay_config = ArcaneAuditorConfig.from_file(str(config_file))
                    merged_config = self._merge_configurations(merged_config, overlay_config)
            except Exception as e:
                print(f"Warning: Failed to load configuration {config_file}: {e}")
                continue
        
        return merged_config or ArcaneAuditorConfig()
    
    def _merge_configurations(self, base: ArcaneAuditorConfig, overlay: ArcaneAuditorConfig) -> ArcaneAuditorConfig:
        """Merge two configurations with overlay taking priority.
        
        Args:
            base: Base configuration (lower priority)
            overlay: Overlay configuration (higher priority)
            
        Returns:
            Merged configuration with overlay settings overriding base settings.
        """
        # Start with base configuration data
        merged_data = base.model_dump()
        overlay_data = overlay.model_dump()
        
        # Merge rules configuration
        if "rules" in overlay_data and overlay_data["rules"]:
            merged_rules = merged_data.get("rules", {})
            
            # Merge each rule configuration
            for rule_name, overlay_rule in overlay_data["rules"].items():
                if overlay_rule is None:
                    continue
                    
                base_rule = merged_rules.get(rule_name, {})
                
                # Merge rule settings
                merged_rule = {}
                
                # Start with base rule settings
                if base_rule:
                    merged_rule.update(base_rule)
                
                # Override with overlay rule settings
                if overlay_rule.get("enabled") is not None:
                    merged_rule["enabled"] = overlay_rule["enabled"]
                
                if overlay_rule.get("severity_override") is not None:
                    merged_rule["severity_override"] = overlay_rule["severity_override"]
                
                # Merge custom_settings (deep merge)
                base_custom = base_rule.get("custom_settings", {}) if base_rule else {}
                overlay_custom = overlay_rule.get("custom_settings", {})
                if overlay_custom:
                    merged_custom = base_custom.copy()
                    merged_custom.update(overlay_custom)
                    merged_rule["custom_settings"] = merged_custom
                elif base_custom:
                    merged_rule["custom_settings"] = base_custom
                
                merged_rules[rule_name] = merged_rule
            
            merged_data["rules"] = merged_rules
        
        # Merge other top-level settings
        for key, value in overlay_data.items():
            if key != "rules" and value is not None:
                merged_data[key] = value
        
        # Create merged configuration
        try:
            return ArcaneAuditorConfig(**merged_data)
        except Exception as e:
            print(f"Warning: Failed to create merged configuration: {e}")
            return base  # Return base configuration as fallback
    
    def list_available_configs(self) -> Dict[str, list]:
        """List all available configurations by directory.
        
        Returns:
            Dictionary mapping directory names to list of available config names.
        """
        available_configs = {}
        
        for config_dir in self.config_paths:
            if not config_dir.exists():
                continue
                
            dir_name = config_dir.name
            configs = []
            
            for config_file in config_dir.glob("*.json"):
                # Skip files in examples subdirectory for user_configs
                if config_dir.name == "user_configs" and "examples" in str(config_file):
                    continue
                configs.append(config_file.stem)
            
            if configs:
                available_configs[dir_name] = sorted(configs)
        
        return available_configs
    
    def validate_config_safety(self) -> Dict[str, str]:
        """Validate that user configurations are properly protected.
        
        Returns:
            Dictionary of safety status for each configuration directory.
        """
        safety_status = {}
        
        for config_dir in self.config_paths:
            if not config_dir.exists():
                safety_status[config_dir.name] = "Directory does not exist"
                continue
            
            gitignore_file = config_dir / ".gitignore"
            
            if config_dir.name == "configs":
                safety_status[config_dir.name] = "App-managed (will be updated)"
            elif gitignore_file.exists():
                safety_status[config_dir.name] = "Protected (update-safe)"
            else:
                safety_status[config_dir.name] = "Warning: No .gitignore protection"
        
        return safety_status


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def load_configuration(config_name: Optional[str] = None) -> ArcaneAuditorConfig:
    """Convenience function to load configuration using the global manager.
    
    Args:
        config_name: Configuration name or file path.
        
    Returns:
        Loaded and merged configuration.
    """
    return get_config_manager().load_config(config_name)
