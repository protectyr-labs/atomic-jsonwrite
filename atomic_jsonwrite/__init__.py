"""
Atomic JSON file writer.
Writes to a temporary file first, then atomically replaces the target.
os.replace() is atomic on NTFS (Windows) and most POSIX filesystems.
"""
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from typing import Any, Optional

_IS_WINDOWS = sys.platform == "win32"
_REPLACE_RETRIES = 5 if _IS_WINDOWS else 0
_REPLACE_DELAY = 0.01  # seconds between retries

__version__ = "0.1.0"


def atomic_write(
    filepath: str,
    data: dict[str, Any],
    indent: int = 2,
    metadata: bool = True,
) -> str:
    """
    Atomically write JSON data to a file.
    Uses tempfile + fsync + os.replace for crash safety.
    Auto-creates parent directories if they don't exist.
    """
    abs_path = os.path.abspath(filepath)
    dir_name = os.path.dirname(abs_path)
    os.makedirs(dir_name, exist_ok=True)

    if metadata:
        output = {"_written_at": datetime.now(timezone.utc).isoformat(), **data}
    else:
        output = data

    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dir_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=indent, default=str)
            f.flush()
            os.fsync(f.fileno())
        # On Windows, os.replace() can raise PermissionError when another
        # process/thread has the target file open.  Retry briefly.
        last_err: Optional[Exception] = None
        for attempt in range(_REPLACE_RETRIES + 1):
            try:
                os.replace(tmp_path, abs_path)
                last_err = None
                break
            except PermissionError as e:
                last_err = e
                if attempt < _REPLACE_RETRIES:
                    time.sleep(_REPLACE_DELAY * (attempt + 1))
        if last_err is not None:
            raise last_err
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return filepath


def atomic_read(filepath: str) -> Optional[dict[str, Any]]:
    """Safely read a JSON file. Returns None if missing or corrupt."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
