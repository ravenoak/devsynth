import pytest

from devsynth.memory import DictCacheLayer, MultiLayeredMemory


@pytest.mark.fast
def test_promotes_value_to_higher_layer() -> None:
    """Values retrieved from lower layers are promoted.

    ReqID: multi-layered-memory-system-and-tiered-cache-strategy"""

    l1 = DictCacheLayer()
    l2 = DictCacheLayer()
    memory = MultiLayeredMemory([l1, l2])
    l2.set("k", "v")

    assert memory.get("k") == "v"
    assert l1.contains("k")


@pytest.mark.fast
def test_hit_ratio_tracking() -> None:
    """Hit ratio reflects successful lookups.

    ReqID: multi-layered-memory-system-and-tiered-cache-strategy"""

    l1 = DictCacheLayer()
    l2 = DictCacheLayer()
    memory = MultiLayeredMemory([l1, l2])

    memory.set("a", 1)
    memory.get("a")
    with pytest.raises(KeyError):
        memory.get("missing")

    assert memory.hit_ratio() == pytest.approx(0.5)
