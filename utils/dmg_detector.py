"""
Utility to detect if the application is running from a DMG on macOS.
"""

import os
import sys
import subprocess
from pathlib import Path

# -----------------------------------------------------------------------------
# Location resolution (works inside PyInstaller bundle)
# -----------------------------------------------------------------------------

def _get_app_root() -> Path:
    """
    Return the .app bundle root when frozen, otherwise script directory.
    Example bundle path:
      /Applications/ArcaneAuditor.app/Contents/MacOS/ArcaneAuditor
    """
    exe = Path(sys.executable).resolve()

    # Walk up to .app if bundled
    parents = list(exe.parents)
    for idx, p in enumerate(parents):
        if p.name == "Contents" and idx + 1 < len(parents) and parents[idx + 1].suffix == ".app":
            return parents[idx + 1]  # the .app dir

    # Not bundled — return working dir
    return Path.cwd()


# -----------------------------------------------------------------------------
# DMG detection logic
# -----------------------------------------------------------------------------

def is_running_from_dmg() -> bool:
    """
    Returns True if app is running directly from a DMG volume.
    Handles APFS sealed system false positives.
    """

    # Not macOS? Never a DMG.
    if sys.platform != "darwin":
        return False

    # Developer override
    if os.getenv("AA_DEV_NO_DMG"):
        return False

    app_root = _get_app_root()
    root_path = str(app_root)

    # Must be under /Volumes to even be considered a DMG
    if not root_path.startswith("/Volumes/"):
        return False

    # Ask macOS what mounts this path
    try:
        df_output = subprocess.check_output(["/bin/df", root_path], text=True).lower()
        # DMG mounts show /dev/disk* AND usually include 'read-only'
        if "disk" in df_output and "read-only" in df_output:
            return True
    except Exception:
        pass

    return False


# -----------------------------------------------------------------------------
# UI / Exit
# -----------------------------------------------------------------------------

def _show_osx_alert(title: str, message: str) -> None:
    """Display a blocking macOS dialog via osascript."""
    try:
        subprocess.run([
            "/usr/bin/osascript", "-e",
            f'display alert "{title}" message "{message}" as critical buttons {{"OK"}}'
        ])
    except Exception:
        pass


def show_dmg_warning_and_exit() -> None:
    """Notify the user and quit."""
    title = "Arcane Auditor"
    message = (
        "Arcane Auditor cannot run directly from a DMG.\n\n"
        "Please drag it to your Applications folder or a personal folder, and run it from there."
    )

    _show_osx_alert(title, message)
    sys.exit(1)


# -----------------------------------------------------------------------------
# Entry helper
# -----------------------------------------------------------------------------

def check_and_exit_if_dmg() -> bool:
    """
    Call at program start.
    Returns True if running from DMG and exits after showing warning.
    Returns False otherwise.
    """
    if is_running_from_dmg():
        show_dmg_warning_and_exit()
        return True
    
    return False
