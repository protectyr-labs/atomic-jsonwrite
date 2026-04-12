import json
import os
import threading
import tempfile
import pytest
from atomic_jsonwrite import atomic_write, atomic_read

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d

def test_basic_write_and_read(tmp_dir):
    path = os.path.join(tmp_dir, "test.json")
    atomic_write(path, {"key": "value"})
    data = atomic_read(path)
    assert data is not None
    assert data["key"] == "value"

def test_metadata_injected(tmp_dir):
    path = os.path.join(tmp_dir, "meta.json")
    atomic_write(path, {"x": 1})
    data = atomic_read(path)
    assert "_written_at" in data

def test_creates_parent_directories(tmp_dir):
    path = os.path.join(tmp_dir, "nested", "deep", "file.json")
    atomic_write(path, {"nested": True})
    data = atomic_read(path)
    assert data["nested"] is True

def test_read_nonexistent_returns_none(tmp_dir):
    path = os.path.join(tmp_dir, "nope.json")
    assert atomic_read(path) is None

def test_concurrent_writes_no_corruption(tmp_dir):
    path = os.path.join(tmp_dir, "concurrent.json")
    errors = []
    def writer(n):
        try:
            atomic_write(path, {"writer": n, "data": "x" * 1000})
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(errors) == 0
    data = atomic_read(path)
    assert data is not None
    assert "writer" in data

def test_metadata_disabled(tmp_dir):
    path = os.path.join(tmp_dir, "nometa.json")
    atomic_write(path, {"clean": True}, metadata=False)
    data = atomic_read(path)
    assert "_written_at" not in data
    assert data["clean"] is True
