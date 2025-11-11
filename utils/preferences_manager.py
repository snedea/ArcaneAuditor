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
    "schema_version": 1,
    "ui": {
        "theme": "dark",
        "file_sort_mode": "alphabetical",
        "finding_sort_mode": "severity"
    },
    "updates": {
        "enabled": False,
        "first_run_completed": False
    },
    "selected_config": None
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

    # If any UI preferences exist from an earlier draft, normalise them.
    ui_prefs = migrated.get("ui", {})
    if isinstance(ui_prefs, dict):
        if ui_prefs.get("theme") == "system":
            ui_prefs["theme"] = "dark"
        # Promote legacy sort_mode into new fields
        if "sort_mode" in ui_prefs and "file_sort_mode" not in ui_prefs:
            legacy_sort = ui_prefs.get("sort_mode", "default")
            ui_prefs["file_sort_mode"] = "alphabetical" if legacy_sort == "default" else legacy_sort
        if "finding_sort_mode" not in ui_prefs:
            # Default to severity unless an explicit legacy value was provided elsewhere
            ui_prefs.setdefault("finding_sort_mode", "severity")
        # Clean up legacy sort_mode
        ui_prefs.pop("sort_mode", None)
        migrated["ui"] = ui_prefs
 
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


def get_selected_config() -> Optional[str]:
    """Return the last selected configuration identifier, if any."""
    prefs = load_preferences()
    return prefs.get("selected_config")


def set_selected_config(config_id: Optional[str]) -> bool:
    """Persist the selected configuration identifier."""
    prefs = load_preferences()
    prefs["selected_config"] = config_id
    return save_preferences(prefs)

