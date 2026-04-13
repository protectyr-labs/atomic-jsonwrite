# atomic-jsonwrite

> JSON writes that survive crashes.

[![CI](https://github.com/protectyr-labs/atomic-jsonwrite/actions/workflows/ci.yml/badge.svg)](https://github.com/protectyr-labs/atomic-jsonwrite/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg)](https://python.org)

`json.dump()` can leave a corrupt file if the process dies mid-write. This writes to a temp file, fsyncs to disk, and atomically replaces the target. The file is always valid JSON or the previous version -- never partial.


## Use Cases

**Agent state persistence** -- Your AI agent writes its state to a JSON file between runs. If the process crashes mid-write, the state file must not be corrupted.

**Configuration hot-reload** -- Multiple processes read a shared config file. When updating, the file must be either the old version or the complete new version -- never partial.

**Pipeline checkpointing** -- A data pipeline saves progress to JSON after each stage. If the pipeline crashes, it can resume from the last valid checkpoint.

## Quick Start

```bash
pip install atomic-jsonwrite
```

```python
from atomic_jsonwrite import atomic_write, atomic_read

atomic_write("state/config.json", {"version": 3, "debug": True})
# => writes temp file, fsync, os.replace -- crash-safe

data = atomic_read("state/config.json")
print(data["_written_at"])  # "2026-04-12T15:30:00+00:00" (auto-injected)
print(data["version"])      # 3

atomic_read("missing.json") # => None (never raises)
```

## Why Not Just json.dump()?

You could write this in 20 minutes. But you will get at least one of these wrong:

- **`flush()` is not enough** -- data can sit in the OS buffer after flush. `fsync()` forces it to the physical disk. Without fsync, a power failure loses your data.
- **`os.rename()` fails on Windows** if the target exists. `os.replace()` is atomic on both NTFS and POSIX. Most "atomic write" snippets on Stack Overflow use `os.rename()` and silently break on Windows.
- **Temp file in the same directory** -- `os.replace()` across filesystems (e.g., `/tmp` to `/data`) fails silently or raises on some systems. The temp file must be on the same mount.
- **Parent directory creation** -- `atomic_write` creates intermediate directories. `json.dump()` to a new path raises `FileNotFoundError`.

These are non-obvious. Most implementations miss at least one.

## API

| Function | Purpose |
|----------|---------|
| `atomic_write(filepath, data, indent=2, metadata=True)` | Write dict as JSON atomically; creates parent dirs |
| `atomic_read(filepath)` | Read JSON file; returns `None` if missing or corrupt |

### How It Works

1. Write to a temp file **in the same directory** as the target
2. `fsync()` the file descriptor to force OS buffer to disk
3. `os.replace()` atomically swaps temp file into target path
4. On failure, temp file is cleaned up -- target is untouched

### Metadata

By default, `_written_at` (ISO timestamp) is injected into the output. Disable with `metadata=False`:

```python
atomic_write("clean.json", {"pure": "data"}, metadata=False)
```

## Limitations

- **Not suitable for files larger than RAM** -- entire dict is serialized in memory before writing
- **Last-writer-wins** -- no file locking; concurrent writers will overwrite each other (but never corrupt)
- **No partial updates** -- rewrites the entire file every time
- **Dict only** -- top-level value must be a dict (not a list or scalar)

## See Also

- [halt-sentinel](https://github.com/protectyr-labs/halt-sentinel) -- emergency stop using atomic file writes

## License

MIT
