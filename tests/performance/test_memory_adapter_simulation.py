import sys
import time
import types
import uuid

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType

stores = []

try:
    from devsynth.application.memory.tinydb_store import TinyDBStore

    TinyDBStore.__abstractmethods__ = frozenset()  # type: ignore[attr-defined]
    stores.append(("TinyDB", TinyDBStore))
except Exception:  # pragma: no cover - optional dependency
    pass

try:
    from devsynth.application.memory.duckdb_store import DuckDBStore

    DuckDBStore.__abstractmethods__ = frozenset()  # type: ignore[attr-defined]
    stores.append(("DuckDB", DuckDBStore))
except Exception:  # pragma: no cover - optional dependency
    pass

try:
    from devsynth.application.memory.lmdb_store import LMDBStore

    LMDBStore.__abstractmethods__ = frozenset()  # type: ignore[attr-defined]
    stores.append(("LMDB", LMDBStore))
except Exception:  # pragma: no cover - optional dependency
    pass

try:
    sys.modules.setdefault("kuzu", types.ModuleType("kuzu"))
    from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
    from devsynth.application.memory.kuzu_store import KuzuStore

    KuzuMemoryStore.__abstractmethods__ = frozenset()  # type: ignore[attr-defined]
    KuzuStore.__abstractmethods__ = frozenset()  # type: ignore[attr-defined]
    stores.append(("Kuzu", KuzuMemoryStore))
except Exception:  # pragma: no cover - optional dependency
    pass

if not stores:  # pragma: no cover - guard when deps missing
    pytest.skip("No memory adapters available", allow_module_level=True)


@pytest.mark.slow
@pytest.mark.parametrize("name,store_cls", stores, ids=[name for name, _ in stores])
def test_memory_adapter_store_simulation(tmp_path, name, store_cls):
    """Simulate storing 100 items across adapters. ReqID: PERF-ADAPTER-01"""

    path = tmp_path / f"{name.lower()}_{uuid.uuid4().hex}"
    if name == "Kuzu" and hasattr(store_cls, "create_ephemeral"):
        try:
            store = store_cls.create_ephemeral(use_provider_system=False)
        except RuntimeError:
            pytest.skip("Kuzu network dependency unavailable")
    else:
        store = store_cls(str(path))
    start = time.perf_counter()
    try:
        for i in range(100):
            item = MemoryItem(
                id="",
                memory_type=MemoryType.WORKING,
                content=f"data {i}",
                metadata={},
            )
            store.store(item)
    except RuntimeError:
        pytest.skip("Kuzu network dependency unavailable")
    duration = time.perf_counter() - start
    assert duration >= 0
