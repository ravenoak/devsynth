"""Runtime regression checks for layered cache protocols."""

from __future__ import annotations

import importlib
from dataclasses import dataclass

import pytest


@pytest.mark.fast
def test_layered_cache_reload_exposes_runtime_protocol() -> None:
    """Reloading the layered cache module preserves runtime-safe protocols."""

    module = importlib.reload(importlib.import_module("devsynth.memory.layered_cache"))

    assert hasattr(module, "CacheLayerProtocol")
    assert hasattr(module, "DictCacheLayer")
    assert hasattr(module, "MultiLayeredMemory")

    layer = module.DictCacheLayer()
    assert isinstance(layer, module.CacheLayerProtocol)

    memory = module.MultiLayeredMemory([layer])
    memory.write("alpha", 1)
    assert memory.read("alpha") == 1


@pytest.mark.fast
def test_protocol_runtime_checks_accept_custom_layers() -> None:
    """Custom cache layers satisfying the protocol pass runtime checks."""

    from devsynth.memory.layered_cache import CacheLayerProtocol, MultiLayeredMemory

    @dataclass
    class Layer(CacheLayerProtocol[int]):
        store: dict[str, int]

        def get(self, key: str) -> int:
            return self.store[key]

        def set(self, key: str, value: int) -> None:
            self.store[key] = value

        def contains(self, key: str) -> bool:
            return key in self.store

    layer = Layer(store={})
    assert isinstance(layer, CacheLayerProtocol)

    cache = MultiLayeredMemory([layer])
    cache.write("beta", 2)
    assert cache.read("beta") == 2


@pytest.mark.fast
def test_layered_cache_protocol_remains_runtime_checkable() -> None:
    """The public namespace exposes the protocol for downstream runtime checks."""

    from devsynth.memory import CacheLayerProtocol

    assert isinstance(CacheLayerProtocol, type)
    assert CacheLayerProtocol.__name__ == "CacheLayerProtocol"

    class Impl:
        def __init__(self) -> None:
            self._data: dict[str, int] = {}

        def get(self, key: str) -> int:
            return self._data[key]

        def set(self, key: str, value: int) -> None:
            self._data[key] = value

        def contains(self, key: str) -> bool:
            return key in self._data

    impl = Impl()
    assert isinstance(impl, CacheLayerProtocol)
