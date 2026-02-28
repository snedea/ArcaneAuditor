"""Find Workday Extend artifact files in a local directory tree."""

from __future__ import annotations

import logging
import os
import stat
import subprocess
import tempfile
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


def scan_github(repo: str, branch: str, token: str) -> ScanManifest:
    """Clone a GitHub repo and scan it for Workday Extend artifact files.

    Args:
        repo: Repository in 'owner/repo' format (e.g. 'acme/payroll-extend').
        branch: Branch name to clone (e.g. 'main').
        token: GitHub personal access token for private repos.
               Pass an empty string for public repos.

    Returns:
        A ScanManifest with root_path pointing to the cloned directory,
        files_by_type populated, and repo/branch/temp_dir fields set.
        The caller MUST call shutil.rmtree(manifest.temp_dir, ignore_errors=True)
        after the auditor has finished with root_path.

    Raises:
        ScanError: If repo format is invalid, git clone fails, or the local
                   scan raises ScanError.

    Note:
        If git clone fails or scan_local raises, the temporary clone directory is
        NOT cleaned up -- the OS will eventually reclaim it. Callers running in a
        tight loop against failing repos should be aware of accumulation in /tmp.
    """
    parts = repo.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ScanError(f"Invalid repo format: '{repo}'. Expected 'owner/repo'.")

    clone_url = f"https://github.com/{repo}.git"

    # Build subprocess environment. Pass credentials via GIT_ASKPASS so the
    # token never appears in argv (which ps aux exposes to all local users).
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"

    askpass_path: Path | None = None
    if token and token.strip():
        askpass_fd, askpass_str = tempfile.mkstemp(prefix="arcane_askpass_", suffix=".sh")
        askpass_path = Path(askpass_str)
        with os.fdopen(askpass_fd, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("printf '%s\\n' \"$GIT_TOKEN\"\n")
        askpass_path.chmod(stat.S_IRWXU)
        env["GIT_ASKPASS"] = str(askpass_path)
        env["GIT_TOKEN"] = token

    tmp_path = Path(tempfile.mkdtemp(prefix="arcane_auditor_"))
    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", "--branch", branch, clone_url, str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            env=env,
        )
        if result.returncode != 0:
            raise ScanError(f"git clone failed for repo '{repo}' branch '{branch}': {result.stderr.strip()}")
        manifest = scan_local(tmp_path)
        manifest.repo = repo
        manifest.branch = branch
        manifest.temp_dir = tmp_path
        logger.debug("scan_github: repo=%s branch=%s total=%d tmp=%s", repo, branch, manifest.total_count, tmp_path)
        return manifest
    except ScanError:
        raise
    except subprocess.TimeoutExpired as exc:
        raise ScanError(f"git clone timed out for repo '{repo}' after 120 seconds.") from exc
    except OSError as exc:
        raise ScanError(f"OS error while cloning repo '{repo}': {exc}") from exc
    finally:
        if askpass_path is not None:
            askpass_path.unlink(missing_ok=True)
