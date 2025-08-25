"""Property-based tests for tiered cache integration. ReqID: HMA-003"""

import pytest

pytest.importorskip("hypothesis")
from hypothesis import given
from hypothesis import strategies as st

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.mark.property
@given(st.text())
@pytest.mark.medium
def test_second_read_hits_cache(content):
    """Second read of an item results in a cache hit. ReqID: HMA-003"""
    adapter = MemorySystemAdapter.create_for_testing()
    adapter.enable_tiered_cache(max_size=5)
    item = MemoryItem(id="", content=content, memory_type=MemoryType.SHORT_TERM)
    item_id = adapter.write(item)
    adapter.read(item_id)  # populate cache
    hits_before = adapter.get_cache_stats()["hits"]
    adapter.read(item_id)
    assert adapter.get_cache_stats()["hits"] == hits_before + 1


@pytest.mark.property
@given(st.lists(st.text(), min_size=1, max_size=20))
@pytest.mark.medium
def test_cache_never_exceeds_max_size(contents):
    """Cache size stays within limit regardless of inputs. ReqID: HMA-004"""
    adapter = MemorySystemAdapter.create_for_testing()
    adapter.enable_tiered_cache(max_size=5)
    ids = []
    for text in contents:
        item = MemoryItem(id="", content=text, memory_type=MemoryType.SHORT_TERM)
        item_id = adapter.write(item)
        ids.append(item_id)
        adapter.read(item_id)
    assert adapter.get_cache_size() <= 5
