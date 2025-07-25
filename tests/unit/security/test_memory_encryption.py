import os
import json
import tempfile
import pytest
from devsynth.application.memory.json_file_store import JSONFileStore

try:
    from devsynth.application.memory.lmdb_store import LMDBStore
except ImportError:
    LMDBStore = None
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.application.memory.tinydb_store import TinyDBStore
from devsynth.security.encryption import generate_key


def test_json_file_store_encryption_succeeds(tmp_path):
    """Test that json file store encryption succeeds.

    ReqID: N/A"""
    os.environ.pop("DEVSYNTH_NO_FILE_LOGGING", None)
    key = generate_key()
    store = JSONFileStore(str(tmp_path), encryption_enabled=True, encryption_key=key)
    item = MemoryItem(id="", content="secret", memory_type=MemoryType.SHORT_TERM)
    item_id = store.store(item)
    file_path = os.path.join(str(tmp_path), "memory_items.json")
    with open(file_path, "rb") as f:
        raw = f.read()
    assert b"secret" not in raw
    retrieved = store.retrieve(item_id)
    assert retrieved.content == "secret"


@pytest.mark.requires_resource("lmdb")
def test_lmdb_store_encryption_succeeds(tmp_path):
    """Test that lmdb store encryption succeeds.

    ReqID: N/A"""
    key = generate_key()
    store = LMDBStore(str(tmp_path), encryption_enabled=True, encryption_key=key)
    item = MemoryItem(id="", content="secret", memory_type=MemoryType.SHORT_TERM)
    item_id = store.store(item)
    store.close()
    data_file = os.path.join(str(tmp_path), "memory.lmdb", "data.mdb")
    with open(data_file, "rb") as f:
        raw = f.read()
    assert b"secret" not in raw
    store = LMDBStore(str(tmp_path), encryption_enabled=True, encryption_key=key)
    retrieved = store.retrieve(item_id)
    assert retrieved.content == "secret"


def test_tinydb_store_encryption_succeeds(tmp_path):
    """Test that tinydb store encryption succeeds."""
    key = generate_key()
    store = TinyDBStore(str(tmp_path), encryption_enabled=True, encryption_key=key)
    item = MemoryItem(id="", content="secret", memory_type=MemoryType.SHORT_TERM)
    item_id = store.store(item)
    store.close()
    data_file = os.path.join(str(tmp_path), "memory.json")
    with open(data_file, "rb") as f:
        raw = f.read()
    assert b"secret" not in raw
    store = TinyDBStore(str(tmp_path), encryption_enabled=True, encryption_key=key)
    retrieved = store.retrieve(item_id)
    assert retrieved.content == "secret"
    store.close()
