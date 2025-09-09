"""Property tests for MemorySystemAdapter operations.

Issue: issues/memory-adapter-integration.md ReqID: HMA-001, HMA-002
"""

import pytest

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.mark.property
@given(st.text())
@pytest.mark.medium
def test_store_and_retrieve_round_trip(content):
    """Stored items are retrievable with identical content.

    Issue: issues/memory-adapter-integration.md ReqID: HMA-001
    """
    adapter = MemorySystemAdapter.create_for_testing()
    item = MemoryItem(id="", content=content, memory_type=MemoryType.SHORT_TERM)
    item_id = adapter.write(item)
    retrieved = adapter.read(item_id)
    assert retrieved.content == content
    assert retrieved.memory_type == MemoryType.SHORT_TERM


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
