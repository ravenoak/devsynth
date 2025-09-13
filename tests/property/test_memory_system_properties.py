"""Property tests for MultiLayeredMemory invariants.

Issue: issues/memory-and-context-system.md ReqID: MEM-001
"""

import pytest

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.memory.layered_cache import DictCacheLayer, MultiLayeredMemory


@pytest.mark.property
@pytest.mark.medium
@given(key=st.text(min_size=1), value=st.integers())
@settings(max_examples=50)
def test_write_through_consistency(key: str, value: int) -> None:
    """Setting a key writes through to all layers.

    Issue: issues/memory-and-context-system.md ReqID: MEM-001
    """
    mem = MultiLayeredMemory([DictCacheLayer(), DictCacheLayer()])
    mem.set(key, value)
    assert all(layer.contains(key) for layer in mem.layers)


@pytest.mark.property
@pytest.mark.medium
@given(
    key=st.text(min_size=1),
    value=st.integers(),
    reads=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=50)
def test_hit_ratio_converges_to_one(key: str, value: int, reads: int) -> None:
    """Top-layer hit ratio approaches 1 with repeated reads.

    Issue: issues/memory-and-context-system.md ReqID: MEM-001
    """
    mem = MultiLayeredMemory([DictCacheLayer(), DictCacheLayer()])
    mem.set(key, value)
    for _ in range(reads):
        mem.get(key)
    assert pytest.approx(1.0, rel=0.0, abs=1 / mem._accesses) == mem.hit_ratio(0)
