"""
Update checking service for Arcane Auditor.

Handles version checking and health status caching.
"""

import threading
import time
from typing import Dict, Any

from __version__ import __version__
from utils.update_checker import check_for_updates, compare_versions, GITHUB_RELEASES_BASE
from utils.preferences_manager import get_update_prefs

_HEALTH_CACHE_LOCK = threading.Lock()
_HEALTH_CACHE: Dict[str, Any] = {
    "latest_version": None,
    "release_url": GITHUB_RELEASES_BASE,
    "error": None,
    "timestamp": 0.0,
}


def _refresh_latest_version(force: bool = False) -> None:
    now = time.time()
    cache_valid = (
        not force
        and _HEALTH_CACHE["latest_version"] is not None
        and now - _HEALTH_CACHE["timestamp"] < 5 * 60
    )
    if cache_valid:
        return
 
    prefs = get_update_prefs()
    if not (prefs.get("enabled", False) and prefs.get("first_run_completed", False)):
        _HEALTH_CACHE["latest_version"] = None
        _HEALTH_CACHE["release_url"] = GITHUB_RELEASES_BASE
        _HEALTH_CACHE["error"] = None
        _HEALTH_CACHE["timestamp"] = now
        return

    result = check_for_updates()
    _HEALTH_CACHE["latest_version"] = result.get("latest_version")
    _HEALTH_CACHE["release_url"] = result.get("release_url", GITHUB_RELEASES_BASE)
    _HEALTH_CACHE["error"] = result.get("error")
    _HEALTH_CACHE["timestamp"] = now


def get_cached_health(force: bool = False) -> Dict[str, Any]:
    with _HEALTH_CACHE_LOCK:
        _refresh_latest_version(force=force)
        latest = _HEALTH_CACHE.get("latest_version")
        release_url = _HEALTH_CACHE.get("release_url", GITHUB_RELEASES_BASE)
        error = _HEALTH_CACHE.get("error")

    payload: Dict[str, Any] = {"status": "healthy", "version": __version__}

    if error:
        payload["update_error"] = error

    if latest:
        payload["update_info"] = {
            "latest_version": latest,
            "current_version": __version__,
            "update_available": compare_versions(__version__, latest),
            "release_url": release_url,
            "error": error,
        }

    return payload


