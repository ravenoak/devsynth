"""Benchmarks for layered cache promotion. ReqID: PERF-04"""

import pytest

from devsynth.memory.layered_cache import DictCacheLayer, MultiLayeredMemory


@pytest.mark.slow
def test_layered_cache_promotion_benchmark(benchmark):
    """Benchmark promoting an item from a lower layer. ReqID: PERF-04"""
    layers = [DictCacheLayer(), DictCacheLayer()]
    memory = MultiLayeredMemory(layers)
    layers[1].set("x", 1)

    def fetch_with_promotion() -> int:
        layers[0].store.pop("x", None)
        return memory.get("x")

    benchmark(fetch_with_promotion)
