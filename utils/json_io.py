"""
JSON IO helpers including atomic write support.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Union


def atomic_write_json(
    target_path: Union[str, Path],
    data: Any,
    *,
    indent: int = 2,
    encoding: str = "utf-8",
) -> None:
    """Atomically write JSON data to a target path.

    Args:
        target_path: Destination path for the JSON document.
        data: JSON-serialisable data.
        indent: Indentation level for emitted JSON.
        encoding: Text encoding for the file.

    Raises:
        OSError: If writing or replacing the file fails.
        TypeError: If JSON serialisation fails.
    """

    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)

    try:
        with os.fdopen(tmp_fd, "w", encoding=encoding) as handle:
            json.dump(data, handle, indent=indent, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            # Best effort cleanup; preserve original exception
            pass
        raise

