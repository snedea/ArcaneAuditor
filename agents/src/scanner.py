from __future__ import annotations

"""Find Workday Extend artifact files in a local directory tree."""

import logging
from pathlib import Path

from src.models import ScanError, ScanManifest

logger = logging.getLogger(__name__)

EXTEND_EXTENSIONS: frozenset[str] = frozenset({".pmd", ".pod", ".script", ".amd", ".smd"})


def scan_local(path: Path) -> ScanManifest:
    """Walk a directory tree and collect all Workday Extend artifact files by extension.

    Args:
        path: Root directory to scan. Must exist and be a directory.

    Returns:
        A ScanManifest with root_path, files_by_type keyed by extension (without dot),
        and a computed total_count.

    Raises:
        ScanError: If path does not exist or is not a directory.
    """
    if not path.exists():
        raise ScanError(f"Path does not exist: {path}")

    if not path.is_dir():
        raise ScanError(f"Path is not a directory: {path}")

    files_by_type: dict[str, list[Path]] = {
        "pmd": [],
        "pod": [],
        "script": [],
        "amd": [],
        "smd": [],
    }

    for item in path.rglob("*"):
        if not item.is_file():
            continue
        if item.suffix not in EXTEND_EXTENSIONS:
            continue
        ext_key = item.suffix[1:]
        files_by_type[ext_key].append(item)

    logger.debug("scan_local: root=%s total=%d", path, sum(len(v) for v in files_by_type.values()))

    return ScanManifest(root_path=path, files_by_type=files_by_type)
