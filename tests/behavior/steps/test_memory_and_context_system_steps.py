"""BDD steps covering the memory and context system specification.

ReqID: memory-and-context-system
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.memory.context_manager import SimpleContextManager
from devsynth.application.memory.multi_layered_memory import MultiLayeredMemorySystem
from devsynth.domain.models.memory import MemoryItem, MemoryType
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "memory_and_context_system.feature"))


@dataclass
class MemoryContext:
    """Shared state for memory-and-context scenarios."""

    memory_system: MultiLayeredMemorySystem | None = None
    context_manager: SimpleContextManager | None = None
    stored_ids_by_content: dict[str, str] = field(default_factory=dict)
    latest_context: dict[str, Any] = field(default_factory=dict)


@pytest.fixture
def memory_context() -> MemoryContext:
    return MemoryContext()


def _coerce_memory_type(raw: str) -> MemoryType:
    try:
        return MemoryType[raw.upper()]
    except KeyError as exc:  # pragma: no cover - defensive guard for invalid fixtures
        raise AssertionError(f"Unknown memory type '{raw}'") from exc


@given("a multi-layered memory system")
def given_memory_system(memory_context: MemoryContext) -> None:
    memory_context.memory_system = MultiLayeredMemorySystem()


@given("a simple context manager")
def given_context_manager(memory_context: MemoryContext) -> None:
    memory_context.context_manager = SimpleContextManager()


@given(
    parsers.parse(
        'I store a memory item with content "{content}" and type "{memory_type}"'
    )
)
@when(
    parsers.parse(
        'I store a memory item with content "{content}" and type "{memory_type}"'
    )
)
def store_memory_item(
    memory_context: MemoryContext, content: str, memory_type: str
) -> None:
    assert memory_context.memory_system is not None, "Memory system must be initialised"
    item = MemoryItem(
        id="", content=content, memory_type=_coerce_memory_type(memory_type)
    )
    item_id = memory_context.memory_system.store(item)
    memory_context.stored_ids_by_content[content] = item_id


@given(
    parsers.parse(
        'I store a memory item with id "{item_id}", content "{content}", and type "{memory_type}"'
    )
)
@when(
    parsers.parse(
        'I store a memory item with id "{item_id}", content "{content}", and type "{memory_type}"'
    )
)
def store_memory_item_with_id(
    memory_context: MemoryContext, item_id: str, content: str, memory_type: str
) -> None:
    assert memory_context.memory_system is not None, "Memory system must be initialised"
    item = MemoryItem(
        id=item_id, content=content, memory_type=_coerce_memory_type(memory_type)
    )
    stored_id = memory_context.memory_system.store(item)
    memory_context.stored_ids_by_content[content] = stored_id


@when(parsers.parse('I add the context value "{key}" as "{value}"'))
def add_context_value(memory_context: MemoryContext, key: str, value: str) -> None:
    assert (
        memory_context.context_manager is not None
    ), "Context manager must be initialised"
    memory_context.context_manager.add_to_context(key, value)


@when("I request the full context")
def when_request_full_context(memory_context: MemoryContext) -> None:
    assert (
        memory_context.context_manager is not None
    ), "Context manager must be initialised"
    memory_context.latest_context = memory_context.context_manager.get_full_context()


@then(parsers.parse('the {layer} layer should contain "{content}"'))
def then_layer_contains(
    memory_context: MemoryContext, layer: str, content: str
) -> None:
    assert memory_context.memory_system is not None, "Memory system must be initialised"
    items = memory_context.memory_system.get_items_by_layer(layer)
    assert any(
        item.content == content for item in items
    ), f"{content} not found in {layer} layer"


@then(parsers.parse('the full context should include key "{key}" with value "{value}"'))
def then_context_includes_pair(
    memory_context: MemoryContext, key: str, value: str
) -> None:
    assert memory_context.latest_context, "Full context should have been requested"
    assert memory_context.latest_context.get(key) == value


@then(parsers.parse('retrieving "{item_id}" should return content "{expected}"'))
def then_retrieve_returns_latest(
    memory_context: MemoryContext, item_id: str, expected: str
) -> None:
    assert memory_context.memory_system is not None, "Memory system must be initialised"
    item = memory_context.memory_system.retrieve(item_id)
    assert item is not None, f"Memory item {item_id} not found"
    assert item.content == expected
