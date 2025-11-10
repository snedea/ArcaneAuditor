"""
Update Checker Module

Checks GitHub releases for new versions and compares against the current app version.
"""

import requests
from typing import Any, Dict, Optional
from packaging import version as packaging_version
from __version__ import __version__

# GitHub API endpoint
GITHUB_API_URL = "https://api.github.com/repos/Developers-and-Dragons/ArcaneAuditor/releases/latest"
REQUEST_TIMEOUT = 2  # seconds


def get_latest_version() -> Optional[str]:
    """
    Fetch and parse GitHub response to get latest version tag_name.

    Returns:
        Latest version string (e.g., "1.2.0") or None on error
    """
    try:
        headers = {
            "User-Agent": f"ArcaneAuditor/{__version__}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.get(GITHUB_API_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        tag_name = data.get("tag_name", "")

        # Remove 'v' prefix if present (e.g., "v1.2.0" -> "1.2.0")
        if tag_name.startswith("v"):
            tag_name = tag_name[1:]

        return tag_name if tag_name else None
    except (requests.RequestException, KeyError, ValueError) as e:
        # Silent failure - log internally but don't raise
        print(f"Update check failed: {e}")
        return None


def compare_versions(current: str, latest: str) -> bool:
    """
    Compare semantic versions using packaging.version.

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        True if latest > current, False otherwise
    """
    try:
        current_ver = packaging_version.parse(current)
        latest_ver = packaging_version.parse(latest)
        return latest_ver > current_ver
    except (packaging_version.InvalidVersion, ValueError):
        # If version parsing fails, assume no update available
        return False


def check_for_updates(force: bool = False) -> Dict[str, Any]:
    """
    Main function to check for updates.

    Args:
        force: Retained for API compatibility (ignored).

    Returns:
        Dict with update information:
        {
            "update_available": bool,
            "latest_version": str,
            "current_version": str,
            "error": Optional[str]
        }
    """
    current_version = __version__
    result = {
        "update_available": False,
        "latest_version": current_version,
        "current_version": current_version,
        "error": None
    }

    latest_version = get_latest_version()

    if latest_version is None:
        result["error"] = "Could not fetch latest version"
        return result

    result["latest_version"] = latest_version

    if compare_versions(current_version, latest_version):
        result["update_available"] = True

    return result

