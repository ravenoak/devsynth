"""Property tests for MemorySystemAdapter operations.

Issue: issues/memory-adapter-integration.md ReqID: HMA-001, HMA-002
"""

from copy import deepcopy
from collections.abc import Callable

import pytest

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.context_manager import SimpleContextManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError

from .strategies import memory_item_strategy


@pytest.mark.property
@given(memory_item_strategy())
@pytest.mark.medium
def test_store_and_retrieve_round_trip(item: MemoryItem):
    """Stored items are retrievable with identical content and metadata.

    Issue: issues/memory-adapter-integration.md ReqID: HMA-001
    """

    adapter = MemorySystemAdapter.create_for_testing()
    stored_item = deepcopy(item)
    stored_item.id = ""
    stored_item.memory_type = MemoryType.SHORT_TERM

    item_id = adapter.write(stored_item)
    retrieved = adapter.read(item_id)

    assert retrieved.content == stored_item.content
    assert retrieved.memory_type == MemoryType.SHORT_TERM
    assert isinstance(retrieved.metadata, dict)
    assert retrieved.metadata == stored_item.metadata


@pytest.mark.property
@given(st.lists(st.text(), min_size=1, max_size=5))
@pytest.mark.medium
def test_search_without_filters_returns_all(contents):
    """Unfiltered search returns all stored items.

    Issue: issues/memory-adapter-integration.md ReqID: HMA-002
    """
    adapter = MemorySystemAdapter.create_for_testing()
    for text in contents:
        adapter.write(
            MemoryItem(id="", content=text, memory_type=MemoryType.SHORT_TERM)
        )
    all_contents = [item.content for item in adapter.search({})]
    assert sorted(all_contents) == sorted(contents)


class TransactionalStubStore:
    """Minimal transactional store used to exercise adapter safeguards."""

    def __init__(self) -> None:
        self.items: dict[str, MemoryItem] = {}
        self.calls: list[str] = []
        self._tx_counter = 0
        self._active: set[str] = set()

    def store(self, item: MemoryItem) -> str:
        self.calls.append("store")
        if not item.id:
            item.id = f"tx-{len(self.items) + 1}"
        self.items[item.id] = deepcopy(item)
        return item.id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        self.calls.append("retrieve")
        return deepcopy(self.items.get(item_id))

    def search(self, query: dict[str, object]) -> list[MemoryItem]:
        self.calls.append("search")
        return [deepcopy(item) for item in self.items.values()]

    def delete(self, item_id: str) -> bool:
        self.calls.append("delete")
        return self.items.pop(item_id, None) is not None

    def begin_transaction(self) -> str:
        self.calls.append("begin_transaction")
        self._tx_counter += 1
        tx = f"txn-{self._tx_counter}"
        self._active.add(tx)
        return tx

    def commit_transaction(self, transaction_id: str) -> bool:
        self.calls.append("commit_transaction")
        self._active.discard(transaction_id)
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        self.calls.append("rollback_transaction")
        self._active.discard(transaction_id)
        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        self.calls.append("is_transaction_active")
        return transaction_id in self._active


@pytest.mark.property
@given(st.lists(st.booleans(), min_size=1, max_size=3))
@pytest.mark.medium
def test_execute_in_transaction_handles_failures(outcomes: list[bool]):
    """execute_in_transaction commits on success and rolls back on failure."""

    store = TransactionalStubStore()
    adapter = MemorySystemAdapter(
        config={"memory_store_type": "memory"},
        memory_store=store,
        context_manager=SimpleContextManager(),
        vector_store=None,
        create_paths=False,
    )

    operations_log: list[int] = []
    fallback_log: list[str] = []
    operations: list[Callable[[], object]] = []

    for idx, should_succeed in enumerate(outcomes):

        def _operation(index: int = idx, ok: bool = should_succeed) -> object:
            operations_log.append(index)
            if not ok:
                raise RuntimeError("boom")
            return index

        operations.append(_operation)

    fallback_operations = [lambda: fallback_log.append("fallback")]

    if all(outcomes):
        result = adapter.execute_in_transaction(operations, fallback_operations)
        assert result == len(outcomes) - 1
        assert fallback_log == []
        assert "commit_transaction" in store.calls
        assert "rollback_transaction" not in store.calls
    else:
        with pytest.raises(MemoryStoreError):
            adapter.execute_in_transaction(operations, fallback_operations)
        assert fallback_log == ["fallback"]
        assert "rollback_transaction" in store.calls


@pytest.mark.property
@given(st.lists(st.text(min_size=1, max_size=8), min_size=1, max_size=3))
@pytest.mark.medium
def test_execute_in_transaction_without_support_raises(ids: list[str]):
    """Adapters guard transactional execution when the store lacks support."""

    adapter = MemorySystemAdapter.create_for_testing()
    recorded: list[str] = []

    operations = [lambda ident=ident: recorded.append(ident) for ident in ids]

    with pytest.raises(MemoryStoreError):
        adapter.execute_in_transaction(
            operations, [lambda: recorded.append("fallback")]
        )

    assert recorded == []
