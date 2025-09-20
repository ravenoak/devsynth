---
author: DevSynth Team
date: '2025-09-14'
status: review
tags:
- implementation
- invariants
title: Adapter Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Adapter Invariants
</div>

# Adapter Invariants

This note outlines invariants for the adapter subsystem that coordinate memory and provider integrations.

## Consistent Adapter Registry

`MemoryManager` maintains a stable mapping of adapter names to implementations. Adding an adapter preserves existing mappings.【F:tests/unit/application/memory/test_memory_manager.py†L1-L213】

```python
from devsynth.application.memory.memory_manager import MemoryManager

class SimpleStore:
    def __init__(self):
        self._store = {}
    def set(self, k, v):
        self._store[k] = v
    def get(self, k):
        return self._store.get(k)

mm = MemoryManager(adapters={"s1": SimpleStore()})
mm.adapters["s2"] = SimpleStore()
assert set(mm.adapters.keys()) == {"s1", "s2"}
```

Proof: [tests/integration/collaboration/test_cross_store_memory_sync.py](../../tests/integration/collaboration/test_cross_store_memory_sync.py).【F:tests/integration/collaboration/test_cross_store_memory_sync.py†L1-L86】

## Cross-store Synchronization

Operations on one adapter propagate to others, ensuring eventual consistency.

```python
from devsynth.application.memory.memory_manager import MemoryManager

class SimpleStore:
    def __init__(self):
        self._store = {}
    def set(self, k, v):
        self._store[k] = v
    def get(self, k):
        return self._store.get(k)

mm = MemoryManager(adapters={"s1": SimpleStore(), "s2": SimpleStore()})
mm.adapters["s1"].set("k", "v")
assert mm.adapters["s2"].get("k") == "v"
```

Simulation: [tests/performance/test_memory_adapter_simulation.py](../../tests/performance/test_memory_adapter_simulation.py) demonstrates storing 100 items across adapters.【F:tests/performance/test_memory_adapter_simulation.py†L1-L120】

## Issue Reference

- [memory-adapter-integration](../../issues/memory-adapter-integration.md)
- [memory-and-context-system](../../issues/memory-and-context-system.md)

## Coverage Signal (2025-09-20)

- Focused unit coverage (`tests/unit/application/memory/test_memory_manager.py`) confirms adapter preference, fallbacks, and sync-hook registration without optional backends, while the collaboration integration test validates cross-store propagation. The targeted sweep records 21.57 % line coverage for `memory_manager.py` and 15.84 % for `sync_manager.py`, quantifying exercised code paths after deselecting the flaky `test_store_prefers_graph_for_edrr_succeeds` case that still requires conflict-resolution fixes.【9c3de6†L1-L23】【F:issues/tmp_cov_memory_adapters.json†L1-L1】
