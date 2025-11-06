"""
Version information for Arcane Auditor.

This module provides a single source of truth for the application version.
It attempts to read the version from package metadata, falls back to pyproject.toml,
and finally to a hardcoded value if all else fails.
"""

from pathlib import Path

try:
    # Primary: Try to get version from installed package metadata
    from importlib.metadata import version
    
    __version__ = version("arcane-auditor")
except Exception:
    # Fallback for development or if not installed
    try:
        import tomllib  # Python 3.11+
        
        # Read from pyproject.toml
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
            __version__ = pyproject_data["project"]["version"]
    except Exception:
        # Final fallback: hardcoded version
        __version__ = "1.2.0"

