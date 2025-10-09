from __future__ import annotations

import datetime
from pathlib import Path

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st

from devsynth.application.memory.adapters.enhanced_graph_memory_adapter import (
    DEVSYNTH,
    RDF,
    RELATION,
    EnhancedGraphMemoryAdapter,
)

pytest.importorskip("rdflib")


pytestmark = [pytest.mark.medium]


def _make_adapter(tmp_path: Path) -> EnhancedGraphMemoryAdapter:
    return EnhancedGraphMemoryAdapter(base_path=str(tmp_path), use_rdflib_store=True)


@pytest.mark.medium
@given(
    chain_length=st.integers(min_value=1, max_value=6),
    max_depth=st.integers(min_value=1, max_value=6),
    include_research_node=st.booleans(),
)
@settings(max_examples=10, deadline=None)
def test_traverse_graph_depth_bound(
    tmp_path, chain_length, max_depth, include_research_node
):
    adapter = _make_adapter(tmp_path)
    node_ids = [f"node{i}" for i in range(chain_length + 1)]

    for node_id in node_ids:
        adapter._ensure_node_uri(node_id)

    for left, right in zip(node_ids, node_ids[1:]):
        left_uri = adapter._ensure_node_uri(left)
        right_uri = adapter._ensure_node_uri(right)
        adapter.graph.add((left_uri, DEVSYNTH.relatedTo, right_uri))
        adapter.graph.add((right_uri, DEVSYNTH.relatedTo, left_uri))
        if RELATION is not None:
            adapter.graph.add((left_uri, RELATION.relatedTo, right_uri))
            adapter.graph.add((right_uri, RELATION.relatedTo, left_uri))

    if include_research_node:
        last_uri = adapter._ensure_node_uri(node_ids[-1])
        adapter.graph.add((last_uri, RDF.type, DEVSYNTH.ResearchArtifact))

    discovered_no_research = adapter.traverse_graph(
        node_ids[0], max_depth, include_research=False
    )
    discovered_with_research = adapter.traverse_graph(
        node_ids[0], max_depth, include_research=True
    )

    limit = min(max_depth, chain_length)
    reachable = {node_ids[index] for index in range(1, limit + 1)}

    if include_research_node and limit == chain_length:
        assert node_ids[-1] not in discovered_no_research
    expected_without_research = reachable - (
        {node_ids[-1]} if include_research_node and limit == chain_length else set()
    )

    assert discovered_no_research == expected_without_research
    assert discovered_with_research == reachable
    beyond = {node_ids[index] for index in range(limit + 1, chain_length + 1)}
    assert discovered_no_research.isdisjoint(beyond)
    assert discovered_with_research.isdisjoint(beyond)


@pytest.mark.medium
@given(
    content=st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=1,
        max_size=40,
    )
)
@settings(max_examples=5, deadline=None)
def test_research_provenance_persists(tmp_path, content):
    adapter = _make_adapter(tmp_path)
    start_id = "node0"
    adapter._ensure_node_uri(start_id)

    artifact_path = tmp_path / "artifact.txt"
    artifact_path.write_text(content)

    artifact = adapter.ingest_research_artifact_from_path(
        artifact_path,
        title="Artifact",
        citation_url=f"file://{artifact_path}",
        published_at=datetime.datetime.now(datetime.timezone.utc),
        supports=[start_id],
        derived_from=[start_id],
    )

    reloaded = _make_adapter(tmp_path)
    discovered = reloaded.traverse_graph(start_id, max_depth=2, include_research=True)
    assert artifact.identifier in discovered

    recomputed = reloaded.compute_evidence_hash(artifact_path)
    assert recomputed == artifact.evidence_hash
