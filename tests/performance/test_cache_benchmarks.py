"""Benchmarks for tiered cache operations. ReqID: PERF-04"""

from devsynth.application.memory.tiered_cache import TieredCache


def test_cache_put_benchmark(benchmark):
    """Benchmark inserting 1000 items. ReqID: PERF-04"""
    cache = TieredCache(max_size=1000)

    def fill_cache() -> None:
        for i in range(1000):
            cache.put(f"key{i}", i)

    benchmark(fill_cache)


def test_cache_get_benchmark(benchmark):
    """Benchmark retrieving a cached item. ReqID: PERF-04"""
    cache = TieredCache(max_size=1000)
    for i in range(1000):
        cache.put(f"key{i}", i)

    benchmark(lambda: cache.get("key500"))
