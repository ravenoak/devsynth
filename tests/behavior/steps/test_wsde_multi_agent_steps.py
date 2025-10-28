from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.edrr.wsde_specialized_agents import (
    CriticAgent,
    ResearchLeadAgent,
    TestWriterAgent,
    run_specialist_rotation,
)
from devsynth.application.memory.adapters.enhanced_graph_memory_adapter import (
    EnhancedGraphMemoryAdapter,
    ResearchArtifact,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType
from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

scenarios(feature_path(__file__, "general", "wsde_multi_agent.feature"))


class _Context:
    def __init__(self) -> None:
        self.graph_adapter: EnhancedGraphMemoryAdapter | None = None
        self.rotation_outputs: dict[str, dict[str, Any]] = {}
        self.artifact_id: str | None = None


@pytest.fixture
def context() -> _Context:
    return _Context()


@given("a graph memory adapter with research artefacts")
def graph_with_research_artifacts(context: _Context, tmp_path: Path) -> None:
    adapter = EnhancedGraphMemoryAdapter(base_path=str(tmp_path), use_rdflib_store=True)

    requirement = MemoryItem(
        id="node1",
        content="Investigate traversal",
        memory_type=MemoryType.REQUIREMENT,
        metadata={},
    )
    implementation = MemoryItem(
        id="node2",
        content="Traversal implementation",
        memory_type=MemoryType.CODE,
        metadata={"related_to": "node1"},
    )
    adapter.store(requirement)
    adapter.store(implementation)

    artifact = ResearchArtifact(
        title="Traversal Evidence",
        summary="Summary of traversal guarantees",
        citation_url="file://artifacts/traversal.txt",
        evidence_hash="hash123",
        published_at=datetime.datetime.now(datetime.UTC),
        supports=("node2",),
        derived_from=("node1",),
        metadata={"roles": ("Research Lead", "Critic", "Test Writer")},
    )
    context.artifact_id = adapter.store_research_artifact(artifact)

    context.graph_adapter = adapter


@when(parsers.parse('the specialist rotation runs from "{start_node}"'))
def run_specialist_rotation_step(context: _Context, start_node: str) -> None:
    assert context.graph_adapter is not None, "Graph adapter not initialised"
    agents = [ResearchLeadAgent(), CriticAgent(), TestWriterAgent()]
    task = {"question": "What is the traversal guarantee?"}
    outputs = run_specialist_rotation(task, context.graph_adapter, start_node, agents)
    context.rotation_outputs = outputs


@then("the research lead plan should include provenance entries")
def check_research_lead_plan(context: _Context) -> None:
    lead_result = context.rotation_outputs.get("ResearchLeadAgent")
    assert lead_result is not None, "Lead result missing"
    plan = lead_result.get("plan")
    assert isinstance(plan, dict)
    assert plan.get("provenance"), "Provenance entries were not captured"
    reachable = plan.get("reachable_nodes")
    assert "node2" in reachable, "Traversal did not follow related nodes"


@then("the critic result should approve the plan")
def check_critic_result(context: _Context) -> None:
    critic_result = context.rotation_outputs.get("CriticAgent")
    assert critic_result is not None, "Critic result missing"
    assert critic_result.get("approved") is True
    assert "node2" in critic_result.get("baseline_neighbors", [])


@then("the test writer should produce executable validation tests")
def check_test_writer(context: _Context) -> None:
    test_writer = context.rotation_outputs.get("TestWriterAgent")
    assert test_writer is not None, "Test Writer result missing"
    test_cases = test_writer.get("test_cases", [])
    assert test_cases, "No test cases were generated"
    assert any(case.get("id") == "test_node2" for case in test_cases)
    assert test_writer.get("blocked") is False
