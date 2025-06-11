import os
import json
import tempfile
from devsynth.application.memory.json_file_store import JSONFileStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.security.encryption import generate_key


def test_json_file_store_encryption(tmp_path):
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
