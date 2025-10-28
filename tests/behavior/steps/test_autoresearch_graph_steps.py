from __future__ import annotations

import datetime
from pathlib import Path
from typing import Set

import pytest

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

pytest.importorskip("pytest_bdd")

from pytest_bdd import given, scenarios, then, when

from devsynth.application.memory.adapters.enhanced_graph_memory_adapter import (
    EnhancedGraphMemoryAdapter,
)
from devsynth.application.memory.adapters.graph_memory_adapter import DEVSYNTH
from devsynth.domain.models.memory import MemoryItem, MemoryType

scenarios(feature_path(__file__, "general", "advanced_graph_memory_features.feature"))


class _Context:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.adapter = EnhancedGraphMemoryAdapter(
            base_path=str(base_path), use_rdflib_store=True
        )
        self.artifact_path: Path | None = None
        self.artifact_id: str | None = None
        self.traversal_result: set[str] = set()


@pytest.fixture
def context(tmp_path: Path) -> _Context:
    return _Context(tmp_path)


@given("a persistent enhanced graph memory adapter")
def persistent_adapter(context: _Context) -> None:
    assert context.adapter is not None


@given('a stored research artifact supporting "node2" derived from "node1"')
def stored_research_artifact(context: _Context) -> None:
    adapter = context.adapter
    item_one = MemoryItem(
        id="node1",
        content="baseline",
        memory_type=MemoryType.REQUIREMENT,
        metadata={},
    )
    item_two = MemoryItem(
        id="node2",
        content="implementation",
        memory_type=MemoryType.CODE,
        metadata={"related_to": "node1"},
    )
    adapter.store(item_one)
    adapter.store(item_two)

    artifact_path = context.base_path / "artifact.txt"
    artifact_path.write_text("Graph traversal with research nodes")
    artifact = adapter.ingest_research_artifact_from_path(
        artifact_path,
        title="Traversal Paper",
        citation_url="file://" + str(artifact_path),
        published_at=datetime.datetime.now(datetime.UTC),
        supports=["node2"],
        derived_from=["node1"],
    )
    context.artifact_path = artifact_path
    context.artifact_id = artifact.identifier


@when('I traverse from "{start}" to depth {depth:d} excluding research artifacts')
def traverse_without_research(context: _Context, start: str, depth: int) -> None:
    context.traversal_result = context.adapter.traverse_graph(start, depth)


@when('I traverse from "{start}" to depth {depth:d} including research artifacts')
def traverse_with_research(context: _Context, start: str, depth: int) -> None:
    context.traversal_result = context.adapter.traverse_graph(
        start, depth, include_research=True
    )


@then('the traversal result should equal "node2"')
def traversal_equals_node(context: _Context) -> None:
    assert context.traversal_result == {"node2"}


@then("the traversal result should contain the stored research artifact identifier")
def traversal_contains_artifact(context: _Context) -> None:
    assert context.artifact_id is not None
    assert context.artifact_id in context.traversal_result


@then("the traversal result should be empty")
def traversal_should_be_empty(context: _Context) -> None:
    assert context.traversal_result == set()


@when("I reload the enhanced graph memory adapter")
def reload_adapter(context: _Context) -> None:
    context.adapter = EnhancedGraphMemoryAdapter(
        base_path=str(context.base_path), use_rdflib_store=True
    )


@then(
    'traversing from "node1" to depth 2 including research artifacts should contain the stored research artifact identifier'
)
def traversal_after_reload_contains_artifact(context: _Context) -> None:
    context.traversal_result = context.adapter.traverse_graph(
        "node1", 2, include_research=True
    )
    traversal_contains_artifact(context)


@then("recomputing the stored research artifact hash should match the persisted digest")
def recompute_hash_matches(context: _Context) -> None:
    assert context.artifact_path is not None
    assert context.artifact_id is not None
    digest = context.adapter.compute_evidence_hash(context.artifact_path)
    artifact_uri = context.adapter._resolve_node_uri(context.artifact_id)  # type: ignore[attr-defined]
    assert artifact_uri is not None
    stored_hash = context.adapter.graph.value(artifact_uri, DEVSYNTH.evidenceHash)
    assert str(stored_hash) == digest
