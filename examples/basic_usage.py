"""Basic usage example for atomic-jsonwrite."""
from atomic_jsonwrite import atomic_write, atomic_read
import os
import tempfile

def main():
    # Create a temp directory for demo
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "state", "app.json")

        # Write some state
        atomic_write(path, {
            "version": 3,
            "users_online": 42,
            "features": {"dark_mode": True, "beta": False},
        })
        print(f"Written to: {path}")

        # Read it back
        data = atomic_read(path)
        print(f"Read back: {data}")
        print(f"Written at: {data['_written_at']}")

        # Overwrite safely
        atomic_write(path, {"version": 4, "users_online": 57})
        data = atomic_read(path)
        print(f"Updated version: {data['version']}")

        # Demonstrate metadata=False
        clean_path = os.path.join(tmp, "clean.json")
        atomic_write(clean_path, {"pure": "data"}, metadata=False)
        clean = atomic_read(clean_path)
        print(f"Clean (no metadata): {clean}")

        # Read nonexistent file
        missing = atomic_read(os.path.join(tmp, "nope.json"))
        print(f"Missing file returns: {missing}")

if __name__ == "__main__":
    main()
