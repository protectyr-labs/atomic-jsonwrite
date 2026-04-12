# Architecture

## Problem Context

In a multi-agent pipeline, several processes write JSON state files concurrently.
A process crash during `json.dump()` can leave a zero-byte or partially-written
file, which cascades into `JSONDecodeError` for every downstream reader. We needed
a write primitive that guarantees the file is always valid JSON.

## Approach

Write-to-temp-then-replace: the classic pattern from database WAL (write-ahead
logging), adapted for single-file JSON state.

## Alternatives Considered

| Option | Pros | Cons | Why Not |
|--------|------|------|---------|
| Standard `json.dump()` | Simple, no dependencies | Corrupt file on crash | The exact problem we're solving |
| File locking (`fcntl.flock`) | Prevents concurrent access | Doesn't help with crash safety; platform-specific | Lock files are a coordination mechanism, not a durability mechanism |
| SQLite for state | ACID guarantees, concurrent-safe | Heavy dependency for simple key-value state | Overkill for config/state files under 1MB |
| Write + rename (no fsync) | Simpler code | Data may be in OS buffer, not on disk — power loss loses it | fsync is the difference between "probably safe" and "guaranteed safe" |

## Key Design Decisions

### Why fsync?
- **Decision:** Call `os.fsync(fd)` before `os.replace()`.
- **Rationale:** `f.flush()` only moves data from Python's buffer to the OS buffer. `fsync` forces the OS to write to the physical disk. Without it, a power failure (not just process crash) can lose the data.
- **Consequence:** ~1-5ms overhead per write. Acceptable for state files; not suitable for high-frequency logging.

### Why os.replace over os.rename?
- **Decision:** Use `os.replace()` instead of `os.rename()`.
- **Rationale:** On Windows, `os.rename()` raises `FileExistsError` if the target already exists. `os.replace()` atomically overwrites on both NTFS and POSIX.
- **Consequence:** Requires Python 3.3+.

### Why same-directory temp file?
- **Decision:** Create temp file with `tempfile.mkstemp(dir=target_dir)`.
- **Rationale:** `os.replace()` fails across filesystem boundaries (e.g., `/tmp` to `/data`). Same directory guarantees same filesystem.
- **Consequence:** Requires write permission to the target directory (not just the target file).

### Why metadata injection?
- **Decision:** Auto-add `_written_at` ISO timestamp to every write.
- **Rationale:** When debugging "why is this state stale?", the first question is always "when was it last written?" Embedding the timestamp eliminates the need for `stat()` calls or external logging.
- **Consequence:** Adds one key to every JSON file. Configurable via `metadata=False` for clean output.

## Known Limitations

- Not suitable for files larger than available RAM (entire dict must fit in memory)
- `_written_at` is wallclock time — no monotonic guarantees across clock adjustments
- No built-in file locking — concurrent writers are safe (atomic replace) but last-writer-wins
- No schema validation — caller is responsible for data structure correctness
