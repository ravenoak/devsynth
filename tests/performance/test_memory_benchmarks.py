"""Benchmarks for memory operations. ReqID: PERF-01"""

from devsynth.application.memory.context_manager import InMemoryStore
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType


def test_memory_store_benchmark(benchmark):
    """Benchmark storing 100 memory items. ReqID: PERF-01"""
    manager = MemoryManager({"mem": InMemoryStore()})

    def store_items() -> None:
        for i in range(100):
            item = MemoryItem(
                id="",
                memory_type=MemoryType.WORKING,
                content=f"data {i}",
                metadata={},
            )
            manager.store_item(item)

    benchmark(store_items)


def test_memory_query_benchmark(benchmark):
    """Benchmark querying memory items by type. ReqID: PERF-01"""
    manager = MemoryManager({"mem": InMemoryStore()})
    for i in range(100):
        item = MemoryItem(
            id="",
            memory_type=MemoryType.WORKING,
            content=f"data {i}",
            metadata={},
        )
        manager.store_item(item)

    benchmark(lambda: manager.query_by_type(MemoryType.WORKING))
