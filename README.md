# atomic-jsonwrite

Crash-safe JSON persistence with `fsync` + atomic replace. Works on Windows (NTFS) and POSIX.

## Why This Exists

We kept losing state files in a multi-agent pipeline when processes crashed mid-write.
Standard `json.dump()` can leave a corrupt or empty file if the process dies between
opening the file and finishing the write. This library guarantees that the target file
is either the old version or the complete new version — never a partial write.

## Demo

```
$ python examples/basic_usage.py
Written to: /tmp/.../state/app.json
Read back: {'_written_at': '2026-04-12T18:30:00+00:00', 'version': 3, 'users_online': 42, 'features': {'dark_mode': True, 'beta': False}}
Written at: 2026-04-12T18:30:00+00:00
Updated version: 4
Clean (no metadata): {'pure': 'data'}
Missing file returns: None
```

## Concurrent Safety

`atomic_write` is safe to call from multiple threads or processes targeting the
same file. Each call writes to its own temporary file, then atomically replaces
the target. You never get a partial or corrupt read.

```python
import threading
from atomic_jsonwrite import atomic_write, atomic_read

def writer(path, thread_id, iterations=100):
    for i in range(iterations):
        atomic_write(path, {"thread": thread_id, "seq": i})

path = "shared_state.json"
threads = [threading.Thread(target=writer, args=(path, t)) for t in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# Final state is always a complete, valid JSON document
# written by whichever thread won the last os.replace()
data = atomic_read(path)
print(data)  # e.g. {'_written_at': '...', 'thread': 2, 'seq': 99}
```

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
