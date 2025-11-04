"""
Utility to detect if the application is running from a DMG on macOS.
"""

import sys
import platform
import subprocess
from arcane_paths import is_frozen

def is_running_from_dmg() -> bool:
    """
    Detect if the application is running from a DMG on macOS.
    
    Returns:
        bool: True if running from DMG, False otherwise
    """
    # Only relevant for macOS
    if platform.system() != "Darwin":
        return False
    
    try:
        # Get the executable path
        if is_frozen():
            app_path = sys.executable
        else:
            app_path = __file__
        
        # DMGs mount under /Volumes/
        return '/Volumes/' in app_path
        
    except Exception:
        # If we can't determine, assume it's safe
        return False


def show_dmg_warning_dialog() -> bool:
    """
    Show a native dialog warning the user they're running from a DMG.
    Always returns False (quit) since the app won't work from a DMG.
    """
    try:
        app_name = "Arcane Auditor"
        
        message = (
            f"{app_name} cannot run from a disk image (DMG).\\n\\n"
            f"Please copy {app_name}.app to a writable location such as:\\n"
            f"• /Applications (if you have admin rights)\\n"
            f"• ~/Applications (your personal Applications folder)\\n"
            f"• Any other folder you have write access to\\n\\n"
            f"Then launch the app from that location."
        )
        
        # Use osascript to show a native dialog
        script = f'''
        display dialog "{message}" ¬
            buttons {{"OK"}} ¬
            default button "OK" ¬
            with icon stop ¬
            with title "{app_name}"
        '''
        
        subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        
    except Exception:
        pass
    
    # Always return False - must quit
    return False


def check_and_warn_if_dmg() -> bool:
    """
    Check if running from DMG and show warning if so.
    
    Returns:
        bool: True if should continue (not a DMG), False if should quit (is a DMG)
    """
    if is_running_from_dmg():
        show_dmg_warning_dialog()
        return False
    return True