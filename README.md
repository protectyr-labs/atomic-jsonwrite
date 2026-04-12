# atomic-jsonwrite

Crash-safe JSON persistence with `fsync` + atomic replace. Works on Windows (NTFS) and POSIX.

## Why This Exists

We kept losing state files in a multi-agent pipeline when processes crashed mid-write.
Standard `json.dump()` can leave a corrupt or empty file if the process dies between
opening the file and finishing the write. This library guarantees that the target file
is either the old version or the complete new version — never a partial write.

## Install

```bash
pip install git+https://github.com/protectyr-labs/atomic-jsonwrite.git
```

## Quick Start

```python
from atomic_jsonwrite import atomic_write, atomic_read

# Safe even if the process crashes mid-write
atomic_write("state/config.json", {"version": 3, "debug": True})

# Read back — returns None if file missing or corrupt
data = atomic_read("state/config.json")
print(data["_written_at"])  # "2026-04-12T15:30:00+00:00"
```

## API

### `atomic_write(filepath, data, indent=2, metadata=True)`

Write a dict as JSON atomically. Creates parent directories if needed.

- `filepath` — target file path
- `data` — dict to serialize
- `indent` — JSON indentation (default 2)
- `metadata` — inject `_written_at` ISO timestamp (default True)

Returns the filepath. Raises `OSError` on failure.

### `atomic_read(filepath)`

Read a JSON file safely. Returns `None` if file is missing or corrupt. Never raises exceptions.

## How It Works

1. Write to a temporary file in the **same directory** as the target
2. `fsync` the file descriptor to force the OS to flush to disk
3. `os.replace()` atomically swaps the temp file into the target path
4. On failure, the temp file is cleaned up — the target is untouched

See [ARCHITECTURE.md](./ARCHITECTURE.md) for design decisions.

## License

MIT — extracted from Protectyr Labs' production systems.
