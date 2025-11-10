"""
Unified Preferences Manager

Manages all user preferences (update settings, configuration state, UI defaults, etc.)
from a single schema-versioned JSON file in the user data directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .arcane_paths import user_root

# Default preferences schema
DEFAULT_PREFS = {
    "schema_version": 2,
    "ui": {
        "theme": "system",
        "sort_mode": "default"
    },
    "updates": {
        "enabled": False,
        "first_run_completed": False
    },
    "configs": {}
}

# Preferences file path
PREFERENCES_DIR = Path(user_root()) / ".user_preferences"
PREFERENCES_FILE = PREFERENCES_DIR / "preferences.json"
PREFERENCES_TMP = PREFERENCES_DIR / "preferences.json.tmp"


def _ensure_preferences_dir():
    """Ensure the preferences directory exists."""
    PREFERENCES_DIR.mkdir(parents=True, exist_ok=True)


def load_preferences() -> Dict[str, Any]:
    """
    Load preferences from disk, fallback to defaults on error.
    
    Returns:
        Dict containing user preferences or defaults if file doesn't exist or is corrupted
    """
    _ensure_preferences_dir()
    
    if not PREFERENCES_FILE.exists():
        return DEFAULT_PREFS.copy()
    
    try:
        with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
        
        # Migrate preferences if schema version is outdated
        prefs = migrate_preferences(prefs)
        return prefs
    except (json.JSONDecodeError, IOError, OSError) as e:
        # If file is corrupted or unreadable, return defaults
        print(f"Warning: Could not load preferences ({e}), using defaults")
        return DEFAULT_PREFS.copy()


def save_preferences(prefs: Dict[str, Any]) -> bool:
    """
    Save preferences using atomic write pattern (via .tmp + replace).
    Handles write errors gracefully.
    
    Args:
        prefs: Preferences dictionary to save
        
    Returns:
        True if save succeeded, False otherwise
    """
    _ensure_preferences_dir()
    
    try:
        # Ensure schema_version is present
        if "schema_version" not in prefs:
            prefs["schema_version"] = DEFAULT_PREFS["schema_version"]
        
        # Write to temporary file first
        with open(PREFERENCES_TMP, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        
        # Atomic replace: rename temp file to actual file
        # This prevents partial writes if crash occurs mid-save
        PREFERENCES_TMP.replace(PREFERENCES_FILE)
        return True
    except (IOError, OSError) as e:
        print(f"Error saving preferences: {e}")
        # Clean up temp file if it exists
        if PREFERENCES_TMP.exists():
            try:
                PREFERENCES_TMP.unlink()
            except OSError:
                pass
        return False


def migrate_preferences(prefs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate preferences to current schema version.
    Adds missing keys or upgrades schema version.
    
    Args:
        prefs: Existing preferences dictionary
        
    Returns:
        Migrated preferences dictionary
    """
    schema_version = prefs.get("schema_version", 1)
    migrated = prefs.copy()
    
    # Always ensure we have the latest schema version
    migrated["schema_version"] = DEFAULT_PREFS["schema_version"]
    
    # Migrate from schema v1 to v2 (if needed)
    if schema_version < 2:
        # Ensure all default keys exist
        if "ui" not in migrated:
            migrated["ui"] = DEFAULT_PREFS["ui"].copy()
        if "updates" not in migrated:
            migrated["updates"] = DEFAULT_PREFS["updates"].copy()
        if "configs" not in migrated:
            migrated["configs"] = DEFAULT_PREFS["configs"].copy()
        
        # Migrate old update_preferences.json structure if it exists
        # (for backward compatibility with old update_preferences.py if it existed)
        old_update_file = PREFERENCES_DIR / "update_preferences.json"
        if old_update_file.exists():
            try:
                with open(old_update_file, 'r', encoding='utf-8') as f:
                    old_updates = json.load(f)
                # Merge old update preferences into new structure
                if "updates" in old_updates:
                    migrated["updates"].update(old_updates["updates"])
                elif "update_check_enabled" in old_updates:
                    migrated["updates"]["enabled"] = old_updates.get("update_check_enabled", False)
                    migrated["updates"]["first_run_completed"] = old_updates.get("first_run_completed", False)
            except (json.JSONDecodeError, IOError):
                pass  # Ignore errors reading old file
    
    # Ensure all default keys exist (defensive programming)
    for key, default_value in DEFAULT_PREFS.items():
        if key not in migrated:
            migrated[key] = default_value.copy() if isinstance(default_value, dict) else default_value
        elif isinstance(default_value, dict) and isinstance(migrated[key], dict):
            # Ensure nested dicts have all required keys
            for nested_key, nested_default in default_value.items():
                if nested_key not in migrated[key]:
                    migrated[key][nested_key] = nested_default
    
    return migrated


# Domain helper functions

def get_update_prefs() -> Dict[str, Any]:
    """Get update preferences."""
    prefs = load_preferences()
    return prefs.get("updates", DEFAULT_PREFS["updates"].copy())


def set_update_prefs(updates: Dict[str, Any]) -> bool:
    """Set update preferences."""
    prefs = load_preferences()
    prefs["updates"] = updates
    return save_preferences(prefs)


def get_ui_prefs() -> Dict[str, Any]:
    """Get UI preferences."""
    prefs = load_preferences()
    return prefs.get("ui", DEFAULT_PREFS["ui"].copy())


def set_ui_prefs(ui: Dict[str, Any]) -> bool:
    """Set UI preferences."""
    prefs = load_preferences()
    prefs["ui"] = ui
    return save_preferences(prefs)


def get_config_prefs() -> Dict[str, Any]:
    """Get config preferences."""
    prefs = load_preferences()
    return prefs.get("configs", DEFAULT_PREFS["configs"].copy())


def set_config_prefs(configs: Dict[str, Any]) -> bool:
    """Set config preferences."""
    prefs = load_preferences()
    prefs["configs"] = configs
    return save_preferences(prefs)

