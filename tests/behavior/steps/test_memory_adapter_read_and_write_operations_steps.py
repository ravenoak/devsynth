"""BDD steps validating layered cache read/write symmetry.

ReqID: memory-adapter-read-and-write-operations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.memory.layered_cache import DictCacheLayer, MultiLayeredMemory
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(
    feature_path(
        __file__, "general", "memory_adapter_read_and_write_operations.feature"
    )
)


@dataclass
class CacheContext:
    """Shared state for layered cache scenarios."""

    layers: list[DictCacheLayer] = field(default_factory=list)
    memory: MultiLayeredMemory | None = None
    last_key: str | None = None
    last_value: Any | None = None
    last_read_value: Any | None = None
    error: Exception | None = None


@pytest.fixture
def cache_context() -> CacheContext:
    return CacheContext()


@given("a two-layer in-memory cache")
def given_two_layer_cache(cache_context: CacheContext) -> None:
    cache_context.layers = [DictCacheLayer(), DictCacheLayer()]
    cache_context.memory = MultiLayeredMemory(cache_context.layers)


@when(parsers.parse('I write the key "{key}" with value "{value}"'))
def when_write_key(cache_context: CacheContext, key: str, value: str) -> None:
    assert cache_context.memory is not None, "Memory system must be initialised"
    cache_context.memory.write(key, value)
    cache_context.last_key = key
    cache_context.last_value = value


@then(parsers.parse('each layer should store "{value}" for "{key}"'))
def then_layers_store_value(cache_context: CacheContext, key: str, value: str) -> None:
    assert cache_context.layers, "Cache layers should be populated"
    for layer in cache_context.layers:
        assert layer.read(key) == value, f"Layer did not persist {key}"


@then(parsers.parse('reading "{key}" should return "{value}"'))
def then_read_returns_value(cache_context: CacheContext, key: str, value: str) -> None:
    assert cache_context.memory is not None, "Memory system must be initialised"
    result = cache_context.memory.read(key)
    cache_context.last_read_value = result
    assert result == value


@when(parsers.parse('I attempt to read the key "{key}"'))
def when_attempt_read(cache_context: CacheContext, key: str) -> None:
    assert cache_context.memory is not None, "Memory system must be initialised"
    cache_context.error = None
    try:
        cache_context.memory.read(key)
    except Exception as exc:  # pragma: no cover - defensive for unexpected errors
        cache_context.error = exc


@then(parsers.parse('a KeyError should be raised for "{key}"'))
def then_key_error(cache_context: CacheContext, key: str) -> None:
    assert cache_context.error is not None, "Expected an exception to be captured"
    assert isinstance(cache_context.error, KeyError)
    assert cache_context.error.args[0] == key
