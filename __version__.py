"""
Version information for Arcane Auditor.

This module provides a single source of truth for the application version.
It attempts to read the version from package metadata, falls back to pyproject.toml,
and finally to a hardcoded value if all else fails.
"""

from pathlib import Path


def _version_from_pyproject() -> str | None:
    """Attempt to read version from pyproject.toml (works in frozen builds)."""
    try:
        import tomllib  # Python 3.11+
        from utils.arcane_paths import resource_path

        pyproject_path = Path(resource_path("pyproject.toml"))
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        return pyproject_data["project"]["version"]
    except Exception:
        return None


# Prefer pyproject.toml when available (source or bundled)
_pyproject_version = _version_from_pyproject()

if _pyproject_version:
    __version__ = _pyproject_version
else:
    try:
        # Fallback: Try to get version from installed package metadata
        from importlib.metadata import version as metadata_version

        __version__ = metadata_version("arcane-auditor")
    except Exception:
        pass # failed to get version from installed package metadata

