import pytest

from devsynth.application.memory.tiered_cache import TieredCache


@pytest.mark.unit
@pytest.mark.fast
def test_eviction_loop_terminates() -> None:
    """Eviction loop terminates and bounds cache size. ReqID: TCV-003"""
    cache = TieredCache(max_size=3)
    for i in range(10):
        cache.put(f"k{i}", i)
    assert len(cache.get_keys()) == 3


@pytest.mark.unit
@pytest.mark.fast
def test_preserves_typed_values() -> None:
    """Generic cache returns strongly typed values."""

    cache: TieredCache[int] = TieredCache(max_size=2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    assert cache.get("missing") is None
