"""
Detect and warn if Arcane Auditor is running from a DMG on macOS.

This version strikes a balance between simplicity and reliability:
- Checks if the app resides under /Volumes (case-insensitive)
- Uses statvfs() to verify the volume is actually read-only
- Avoids brittle parsing of 'mount' or 'df' output
- Uses only Python stdlib and osascript (no PyObjC)
"""

import os
import sys
import subprocess
from pathlib import Path


# -----------------------------------------------------------------------------
# Core Detection
# -----------------------------------------------------------------------------

def is_running_from_dmg() -> bool:
    """
    Returns True if the application is running from a DMG or another read-only
    /Volumes/ mount. This works reliably across macOS versions and APFS setups.
    """
    if sys.platform != "darwin":
        return False

    try:
        # Determine executable or script path
        app_path = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()

        # Must live under /Volumes/<something> (case-insensitive)
        parts_lower = [p.lower() for p in app_path.parts]
        if len(parts_lower) >= 3 and parts_lower[1] == "volumes":
            # Use original-case volume name for statvfs
            volume = f"/Volumes/{app_path.parts[2]}"

            # Check if the mount is read-only
            try:
                stats = os.statvfs(volume)
                if not (stats.f_flag & getattr(os, "ST_RDONLY", 1)):
                    # Volume is writable → probably external drive, not DMG
                    return False
            except Exception:
                # If statvfs fails, err on the side of caution
                pass

            # Under /Volumes/ and read-only → treat as DMG
            return True

    except Exception:
        pass

    return False


# -----------------------------------------------------------------------------
# User Dialog + Exit
# -----------------------------------------------------------------------------

def show_dmg_warning_and_exit() -> None:
    """
    Show a blocking macOS alert via osascript and exit immediately.
    """
    title = "Arcane Auditor"
    message = (
        "Arcane Auditor cannot run directly from a DMG.\n\n"
        "Please drag it to your Applications folder or another writable location, "
        "then run it from there."
    )

    try:
        subprocess.run(
            [
                "/usr/bin/osascript",
                "-e",
                f'display alert "{title}" message "{message}" as critical buttons {{"OK"}}',
            ],
            check=False,
        )
    except Exception:
        # If AppleScript fails silently (e.g., unsigned CI build), we still exit
        pass

    sys.exit(1)


# -----------------------------------------------------------------------------
# Entry Helper
# -----------------------------------------------------------------------------

def check_and_exit_if_dmg() -> None:
    """
    Call at application startup. If running from DMG, show warning and quit.
    """
    if is_running_from_dmg():
        show_dmg_warning_and_exit()
