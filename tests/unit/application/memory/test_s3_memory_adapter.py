import json
from types import SimpleNamespace

import pytest

from devsynth.application.memory.adapters import s3_memory_adapter as s3_mod
from devsynth.application.memory.adapters.s3_memory_adapter import S3MemoryAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryTransactionError


@pytest.mark.medium
def test_store_retrieve_delete_roundtrip(monkeypatch):
    # Fake in-memory S3 client
    storage: dict[str, str] = {}

    class FakeBody:
        def __init__(self, data: str):
            self._data = data

        def read(self):
            return self._data

    class FakeClient:
        def put_object(self, Bucket, Key, Body):  # noqa: N803 (external API)
            storage[Key] = Body

        def get_object(self, Bucket, Key):  # noqa: N803
            if Key not in storage:
                raise s3_mod.ClientError("NoSuchKey")
            return {"Body": FakeBody(storage[Key])}

        def list_objects_v2(self, Bucket):  # noqa: N803
            return {"Contents": [{"Key": k} for k in storage.keys()]}

        def delete_object(self, Bucket, Key):  # noqa: N803
            if Key in storage:
                del storage[Key]

    # Monkeypatch module-level boto3 and ClientError so constructor works
    monkeypatch.setattr(s3_mod, "boto3", SimpleNamespace(client=lambda *_: FakeClient()))
    monkeypatch.setattr(s3_mod, "ClientError", Exception)

    adapter = S3MemoryAdapter(bucket="test-bucket")

    item = MemoryItem(id="", content="hello", memory_type=MemoryType.WORKING, metadata={})
    item_id = adapter.store(item)
    assert item_id

    retrieved = adapter.retrieve(item_id)
    assert retrieved is not None
    assert retrieved.content == "hello"
    assert retrieved.memory_type == MemoryType.WORKING

    # Update and re-store
    item.content = "updated"
    adapter.store(item)
    updated = adapter.retrieve(item_id)
    assert updated is not None and updated.content == "updated"

    # Delete
    assert adapter.delete(item_id) is True
    assert adapter.retrieve(item_id) is None


@pytest.mark.medium
def test_search_filters_by_type_and_metadata(monkeypatch):
    storage: dict[str, str] = {}

    class FakeBody:
        def __init__(self, data: str):
            self._data = data

        def read(self):
            return self._data

    class FakeClient:
        def put_object(self, Bucket, Key, Body):  # noqa: N803
            storage[Key] = Body

        def get_object(self, Bucket, Key):  # noqa: N803
            return {"Body": FakeBody(storage[Key])}

        def list_objects_v2(self, Bucket):  # noqa: N803
            return {"Contents": [{"Key": k} for k in storage.keys()]}

    monkeypatch.setattr(s3_mod, "boto3", SimpleNamespace(client=lambda *_: FakeClient()))
    monkeypatch.setattr(s3_mod, "ClientError", Exception)

    adapter = S3MemoryAdapter(bucket="b")

    def dump(item: MemoryItem) -> str:
        return json.dumps(
            {
                "id": item.id,
                "content": item.content,
                "memory_type": item.memory_type.value,
                "metadata": item.metadata,
                "created_at": None,
            }
        )

    a = MemoryItem(id="a", content="A", memory_type=MemoryType.WORKING, metadata={"tag": "x"})
    b = MemoryItem(id="b", content="B", memory_type=MemoryType.LONG_TERM, metadata={"tag": "y"})
    storage["a"] = dump(a)
    storage["b"] = dump(b)

    res = adapter.search({"type": MemoryType.WORKING})
    assert {i.id for i in res} == {"a"}

    res = adapter.search({"tag": "y"})
    assert {i.id for i in res} == {"b"}

    res = adapter.search({"type": MemoryType.LONG_TERM, "tag": "y"})
    assert {i.id for i in res} == {"b"}


@pytest.mark.medium
def test_transactions_are_unsupported(monkeypatch):
    monkeypatch.setattr(s3_mod, "boto3", SimpleNamespace(client=lambda *_: object()))
    monkeypatch.setattr(s3_mod, "ClientError", Exception)
    adapter = S3MemoryAdapter(bucket="b")

    with pytest.raises(MemoryTransactionError):
        adapter.store(MemoryItem(id="1", content="c", memory_type=MemoryType.WORKING), transaction_id="tx")

    for fn in (adapter.begin_transaction, lambda: adapter.commit_transaction("tx"), lambda: adapter.rollback_transaction("tx")):
        with pytest.raises(MemoryTransactionError):
            fn()
    assert adapter.is_transaction_active("tx") is False
