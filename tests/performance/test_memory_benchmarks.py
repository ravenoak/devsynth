"""Benchmarks for memory operations. ReqID: PERF-01"""

import os
from devsynth.application.memory.context_manager import InMemoryStore
from devsynth.application.memory.json_file_store import JSONFileStore
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


def test_json_store_write_benchmark(tmp_path, benchmark):
    """Benchmark JSONFileStore writes. ReqID: PERF-01"""
    os.environ["DEVSYNTH_NO_FILE_LOGGING"] = "1"
    store = JSONFileStore(str(tmp_path), version_control=False)

    def store_items() -> None:
        for i in range(100):
            item = MemoryItem(
                id="",
                memory_type=MemoryType.WORKING,
                content=f"data {i}",
                metadata={},
            )
            store.store(item)

    benchmark(store_items)


def test_json_store_search_benchmark(tmp_path, benchmark):
    """Benchmark JSONFileStore search. ReqID: PERF-01"""
    os.environ["DEVSYNTH_NO_FILE_LOGGING"] = "1"
    store = JSONFileStore(str(tmp_path), version_control=False)
    for i in range(100):
        item = MemoryItem(
            id="",
            memory_type=MemoryType.WORKING,
            content=f"data {i}",
            metadata={},
        )
        store.store(item)

    benchmark(lambda: store.search({"memory_type": MemoryType.WORKING}))
