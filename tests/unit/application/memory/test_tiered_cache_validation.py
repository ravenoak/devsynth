"""Property-based tests validating TieredCache LRU behavior. ReqID: TCV-000"""

from collections import OrderedDict

import pytest

pytest.importorskip("hypothesis")
from hypothesis import given
from hypothesis import strategies as st

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.tiered_cache import TieredCache
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.mark.property
@given(st.lists(st.text(min_size=1), min_size=1, max_size=50))
@pytest.mark.medium
def test_lru_eviction_matches_reference(accesses):
    """Cache contents mirror reference LRU model. ReqID: TCV-001"""
    cache = TieredCache(max_size=3)
    reference = OrderedDict()
    for key in accesses:
        if cache.contains(key):
            cache.get(key)
            reference.move_to_end(key)
        else:
            cache.put(key, key)
            if len(reference) >= 3:
                reference.popitem(last=False)
            reference[key] = key
    assert cache.get_keys() == list(reference.keys())


@pytest.mark.property
@given(st.lists(st.text(min_size=1), min_size=1, max_size=30))
@pytest.mark.medium
def test_hit_miss_counts_match_reference(accesses):
    """Hit/miss counters align with simulated access patterns. ReqID: TCV-002"""
    adapter = MemorySystemAdapter.create_for_testing()
    adapter.enable_tiered_cache(max_size=3)
    ids = {}
    reference = OrderedDict()
    hits = misses = 0
    for key in accesses:
        if key not in ids:
            item = MemoryItem(id="", content=key, memory_type=MemoryType.SHORT_TERM)
            ids[key] = adapter.write(item)
        item_id = ids[key]
        if key in reference:
            hits += 1
            reference.move_to_end(key)
        else:
            misses += 1
            if len(reference) >= 3:
                reference.popitem(last=False)
            reference[key] = item_id
        adapter.read(item_id)
    stats = adapter.get_cache_stats()
    assert stats["hits"] == hits
    assert stats["misses"] == misses
    assert adapter.cache.get_keys() == list(reference.keys())
