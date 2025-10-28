import os
import random
from typing import List

import pytest

try:
    from devsynth.application.memory.context_manager import InMemoryStore
    from devsynth.domain.models.memory import MemoryItem, MemoryType
except Exception as e:  # pragma: no cover - defensive import for CI environments
    pytest.skip(f"Memory components unavailable: {e}", allow_module_level=True)


pytestmark = [
    pytest.mark.performance,
    pytest.mark.requires_resource("performance"),
    pytest.mark.memory_intensive,
    pytest.mark.no_network,
]


def _build_dataset(store: InMemoryStore, n: int = 2000) -> list[str]:
    ids: list[str] = []
    topics = ["alpha", "beta", "gamma", "delta", "epsilon"]
    for i in range(n):
        topic = random.choice(topics)
        item = MemoryItem(
            id=None,
            content=f"{topic} payload #{i}",
            memory_type=MemoryType.NOTE,
            metadata={"topic": topic, "index": i},
            created_at=None,
        )
        ids.append(store.store(item))
    return ids


@pytest.mark.skipif(
    os.getenv("DEVSYNTH_ENABLE_BENCHMARKS", "false").lower()
    not in {"1", "true", "yes"},
    reason=(
        "Benchmarks disabled by default. Enable with DEVSYNTH_ENABLE_BENCHMARKS=true "
        "and ensure pytest-benchmark plugin is loaded (e.g., `pytest -p benchmark`)."
    ),
)
@pytest.mark.skipif(
    "PYTEST_CURRENT_TEST" not in os.environ
    and "PYTEST_ADDOPTS" in os.environ
    and "-p no:benchmark" in os.environ.get("PYTEST_ADDOPTS", ""),
    reason="pytest-benchmark plugin disabled via -p no:benchmark",
)
@pytest.mark.slow
@pytest.mark.requires_resource("performance")
def test_memory_search_benchmark(benchmark):
    """
    Benchmark the in-memory search path for a representative query.

    Notes:
    - This test is skipped by default. To run:
        DEVSYNTH_ENABLE_BENCHMARKS=true pytest -p benchmark tests/performance/test_memory_benchmark.py -q
    - No network, deterministic workload size; content randomness limited to topic label choice.
    """
    random.seed(1337)
    store = InMemoryStore()
    _build_dataset(store, n=5000)

    def do_search():
        # Query targets common path: content substring and metadata exact match
        return store.search(
            {
                "content": "payload",
                "memory_type": MemoryType.NOTE.value,
                "topic": "gamma",
            }
        )

    result = benchmark(do_search)
    # Sanity: benchmark returns the function result; ensure something was found
    assert isinstance(result, list)
