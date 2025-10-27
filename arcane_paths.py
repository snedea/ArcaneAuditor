"""
Arcane Auditor Environment Path Resolver

This module centralizes all path resolution logic for Arcane Auditor.
It ensures consistent handling of:
    • Delivered assets (rules, presets)
    • Editable user assets (custom rules, team/personal configs)
    • Generated assets (outputs, logs)
across Windows, macOS, and Linux environments.

The same functions work seamlessly in:
    • Source (developer) mode
    • Frozen (PyInstaller) mode
"""

import os
import sys
import platform
import shutil
from pathlib import Path

def is_frozen() -> bool:
    """Return True if running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False)

def ensure_sample_rule_config():
    """
    Seeds user config directories with a .sample copy of production-ready.json
    if running in a frozen build and the folders are empty.
    """
    if not is_frozen():
        return  # Only seed in packaged mode

    dirs = get_config_dirs()
    preset_src = resource_path(os.path.join("config", "rules", "presets", "production-ready.json"))

    for target_dir in (dirs["teams"], dirs["personal"]):
        target_path = Path(target_dir)
        if target_path.is_dir() and not any(f.endswith(".json") for f in os.listdir(target_path)):
            dst = target_path / f"{target_path.name}.json.sample"
            shutil.copy2(preset_src, dst)
            print(f"Refreshed sample config: {dst}")
        else:
            print(f"{target_dir} is not a directory or is not empty")


def is_developer_mode() -> bool:
    """
    Return True if running from source (not frozen).
    
    Returns:
        bool: True if in developer mode, False if frozen/packaged
    """
    return not is_frozen()


def resource_path(rel: str) -> str:
    """
    Resolve a resource path whether running from source or PyInstaller bundle.
    
    Returns:
        str: Normalized absolute path to the resource
    """
    if is_frozen():
        return os.path.normpath(os.path.join(sys._MEIPASS, rel))
    return os.path.normpath(os.path.join(os.path.dirname(__file__), rel))


def user_root() -> str:
    """
    Return the per-user writable data directory for Arcane Auditor.

    Windows → %AppData%\\ArcaneAuditor
    macOS   → ~/Library/Application Support/ArcaneAuditor
    Linux   → ~/.config/ArcaneAuditor
    
    Returns:
        str: Normalized absolute path to the user data directory
    """
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:  # Linux, WSL, etc.
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))

    path = os.path.normpath(os.path.join(base, "ArcaneAuditor"))
    os.makedirs(path, exist_ok=True)
    return path



def get_rule_dirs():
    """
    Return the list of rule directories to search (in priority order).

    Includes built-in delivered rule folders and the per-user
    custom/user folder (created automatically if missing).
    
    In developer mode: uses local parser/rules/custom/user directory
    In frozen mode: uses AppData/ArcaneAuditor/parser/rules/custom/user directory
    
    Returns:
        list: List of rule directory paths in priority order
    """
    builtin_script = resource_path(os.path.join("parser", "rules", "script"))
    builtin_structure = resource_path(os.path.join("parser", "rules", "structure"))
    
    # Use local custom rules directory in developer mode, AppData in frozen mode
    if is_developer_mode():
        user_rules = os.path.join(os.path.dirname(__file__), "parser", "rules", "custom", "user")
    else:
        user_rules = os.path.join(user_root(), "parser", "rules", "custom", "user")
    
    os.makedirs(user_rules, exist_ok=True)
    return [builtin_script, builtin_structure, user_rules]



def get_config_dirs():
    """
    Return a dict of configuration directories.

    In developer mode (running from source):
        config/presets, config/teams, config/personal (local)

    In frozen mode (packaged executable):
        presets in bundle, teams/personal in user-writable AppData location
        
    Returns:
        dict: Dictionary with 'presets', 'teams', and 'personal' directory paths
    """
    root = user_root()
    local_base = os.path.join(os.path.dirname(__file__), "config")

    # Developer mode: prefer local repo structure
    if is_developer_mode():
        rules_base = os.path.join(local_base, "rules")
        teams_dir = os.path.join(rules_base, "teams")
        personal_dir = os.path.join(rules_base, "personal")

        return {
            "presets": os.path.join(rules_base, "presets"),
            "teams": teams_dir,
            "personal": personal_dir,
        }

    # Frozen mode: presets bundled, user configs external
    builtin_presets = resource_path(os.path.join("config","rules","presets"))
    teams_dir = os.path.join(root, "config", "rules", "teams")
    personal_dir = os.path.join(root, "config", "rules", "personal")

    os.makedirs(teams_dir, exist_ok=True)
    os.makedirs(personal_dir, exist_ok=True)

    return {
        "presets": builtin_presets,
        "teams": teams_dir,
        "personal": personal_dir,
    }



def get_output_dir() -> str:
    """
    Return the per-user output directory for generated reports/logs.
    
    Returns:
        str: Normalized absolute path to the output directory
    """
    out_dir = os.path.join(user_root(), "output")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir
