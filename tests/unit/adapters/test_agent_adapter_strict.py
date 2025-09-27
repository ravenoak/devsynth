"""Unit tests for the strictly typed agent adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest

from devsynth.adapters.agents.agent_adapter import (
    AgentAdapter,
    AgentCreationConfigPayload,
    DelegatedTaskRequest,
    SimplifiedAgentFactory,
    WSDETeamCoordinator,
    _load_default_config,
    _normalise_capabilities,
    _normalise_parameters,
)
from devsynth.domain.models.agent import AgentType
from devsynth.exceptions import ValidationError


class StubAgent:
    """Minimal agent implementation used for unit tests."""

    def __init__(self, name: str, result: dict[str, object]) -> None:
        self.name = name
        self._result = dict(result)
        self.config = SimpleNamespace(name=name)

    def initialize(self, config: object) -> None:  # pragma: no cover - unused in tests
        self.config = config

    def process(self, inputs: dict[str, object]) -> dict[str, object]:
        return dict(self._result)

    def get_capabilities(self) -> list[str]:  # pragma: no cover - unused in tests
        return []


class StubConsensusTeam:
    """Test double that fulfils :class:`ConsensusCapableTeam`."""

    def __init__(
        self,
        agents: list[StubAgent],
        critical_result: object | None = None,
        consensus_result: object | None = None,
    ) -> None:
        self.agents = list(agents)
        self._critical_result = critical_result or {"status": "critical", "result": "decision"}
        self._consensus_result = consensus_result
        self.added_solutions: list[tuple[dict[str, object], dict[str, object]]] = []
        self.consensus_payloads: list[dict[str, object]] = []
        self.dialectical_calls: list[tuple[dict[str, object], str]] = []

    def add_agent(self, agent: object) -> None:
        self.agents.append(agent)  # type: ignore[arg-type]

    def add_agents(self, agents: Sequence[object]) -> None:
        self.agents.extend(agents)  # type: ignore[arg-type]

    def vote_on_critical_decision(self, task: Mapping[str, object]) -> object:
        self._voted_task = dict(task)
        return self._critical_result

    def select_primus_by_expertise(self, task: Mapping[str, object]) -> None:
        self._selected_task = dict(task)

    def get_primus(self) -> StubAgent | None:
        return self.agents[0] if self.agents else None

    def add_solution(self, task: Mapping[str, object], solution: Mapping[str, object]) -> None:
        self.added_solutions.append((dict(task), dict(solution)))

    def build_consensus(self, payload: Mapping[str, object]) -> dict[str, object]:
        record = dict(payload)
        self.consensus_payloads.append(record)
        if self._consensus_result is not None:
            return self._consensus_result  # type: ignore[return-value]

        return {
            "status": "ok",
            "result": "agreement",
            "initial_preferences": {"alpha": 1},
            "explanation": "complete",
            "rounds": [1],
            "final_preferences": {"alpha": 1},
        }

    def apply_enhanced_dialectical_reasoning_multi(
        self, task: Mapping[str, object], critic_agent: StubAgent
    ) -> dict[str, object]:
        snapshot = (dict(task), critic_agent.name)
        self.dialectical_calls.append(snapshot)
        return {"analysis": "ready"}


@pytest.mark.fast
def test_agent_creation_payload_serialises_configuration() -> None:
    payload = AgentCreationConfigPayload.from_mapping(
        "planner",
        {
            "name": "planner-1",
            "description": "Planning agent",
            "capabilities": ["plan", "estimate"],
            "parameters": {"temperature": 0.1},
        },
    )

    config = payload.to_agent_config()

    assert payload.capabilities == ("plan", "estimate")
    assert payload.parameters == {"temperature": 0.1}
    assert config.name == "planner-1"
    assert config.agent_type is AgentType.PLANNER
    assert config.capabilities == ["plan", "estimate"]


@pytest.mark.fast
def test_agent_creation_payload_defaults_to_orchestrator() -> None:
    payload = AgentCreationConfigPayload.from_mapping("unknown", None)

    assert payload.agent_type is AgentType.ORCHESTRATOR
    assert payload.capabilities == ()
    assert payload.parameters == {}


@pytest.mark.fast
def test_load_default_config_handles_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "nope.yml"

    assert _load_default_config(missing_path) == {}


@pytest.mark.fast
def test_load_default_config_parses_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text("flag: true\nanswer: 42\n")

    loaded = _load_default_config(config_path)

    assert loaded == {"flag": True, "answer": 42}


@pytest.mark.fast
def test_normalise_helpers_return_defaults() -> None:
    assert _normalise_capabilities("abc") == ()
    assert _normalise_capabilities(["a", "b"]) == ("a", "b")
    assert _normalise_parameters("not-a-mapping") == {}
    assert _normalise_parameters({"limit": 5}) == {"limit": 5}


@pytest.mark.fast
def test_delegated_task_request_option_labels_from_solutions() -> None:
    request = DelegatedTaskRequest.from_mapping(
        {"solutions": [{"content": "alpha"}, {"agent": "beta"}]}
    )

    assert request.option_labels([]) == ["alpha", "beta"]


@pytest.mark.fast
def test_delegated_task_request_option_labels_from_agents() -> None:
    agents = [StubAgent("orchestrator", {"result": "ok"}), StubAgent("critic", {"result": "ok"})]
    request = DelegatedTaskRequest.from_mapping({})

    assert request.option_labels(agents) == ["orchestrator", "critic"]


@pytest.mark.fast
def test_delegated_task_request_rejects_none_payload() -> None:
    with pytest.raises(ValidationError):
        DelegatedTaskRequest.from_mapping(None)


@pytest.mark.fast
def test_delegated_task_request_iter_solutions_filters_invalid() -> None:
    request = DelegatedTaskRequest.from_mapping(
        {"solutions": [{"content": "alpha"}, "ignored", {"agent": "beta"}]}
    )

    assert request.iter_solutions() == ({"content": "alpha"}, {"agent": "beta"})


@pytest.mark.fast
def test_delegated_task_request_solution_from_agent_handles_confidence() -> None:
    request = DelegatedTaskRequest.from_mapping({})
    agent = StubAgent("alpha", {"result": "ignored"})

    solution = request.solution_from_agent(
        agent,
        {"result": "done", "confidence": "not-a-number", "reasoning": "trace"},
    )

    assert solution == {
        "agent": "alpha",
        "content": "done",
        "confidence": 1.0,
        "reasoning": "trace",
    }


@pytest.mark.fast
def test_delegated_task_request_consensus_payload_and_contributors() -> None:
    request = DelegatedTaskRequest.from_mapping({"details": "value"})
    payload = request.consensus_payload(["one", "two"])

    assert payload["options"] == ["one", "two"]
    assert DelegatedTaskRequest.contributors_from_consensus({}) == []


@pytest.mark.fast
def test_delegate_task_requires_active_team() -> None:
    coordinator = WSDETeamCoordinator()

    with pytest.raises(ValidationError):
        coordinator.delegate_task({})


@pytest.mark.fast
def test_delegate_task_requires_agents() -> None:
    coordinator = WSDETeamCoordinator()
    coordinator.teams["demo"] = StubConsensusTeam([])
    coordinator.current_team_id = "demo"

    with pytest.raises(ValidationError):
        coordinator.delegate_task({})


@pytest.mark.fast
def test_delegate_task_runs_consensus_flow() -> None:
    agents = [StubAgent("alpha", {"result": "A"}), StubAgent("beta", {"result": "B"})]
    coordinator = WSDETeamCoordinator()
    team = StubConsensusTeam(agents)
    coordinator.teams["demo"] = team
    coordinator.current_team_id = "demo"

    result = coordinator.delegate_task({"details": "value", "solutions": [{"content": "A"}]})

    assert result["status"] == "ok"
    assert team.consensus_payloads[-1]["options"] == ["A"]
    assert team.added_solutions, "solutions should be recorded for consensus"
    assert team.dialectical_calls[-1][1] in {"alpha", "beta"}


@pytest.mark.fast
def test_delegate_task_handles_non_mapping_decision() -> None:
    agents = [StubAgent("alpha", {"result": "A"}), StubAgent("beta", {"result": "B"})]
    coordinator = WSDETeamCoordinator()
    team = StubConsensusTeam(agents, critical_result="denied")
    coordinator.teams["critical"] = team
    coordinator.current_team_id = "critical"

    result = coordinator.delegate_task({"type": "critical_decision", "is_critical": True})

    assert result == {"result": "denied"}


@pytest.mark.fast
def test_delegate_task_handles_non_mapping_consensus() -> None:
    agents = [StubAgent("alpha", {"result": "A"}), StubAgent("beta", {"result": "B"})]
    coordinator = WSDETeamCoordinator()
    team = StubConsensusTeam(agents, consensus_result="summary")
    coordinator.teams["consensus"] = team
    coordinator.current_team_id = "consensus"

    result = coordinator.delegate_task({"details": "value"})

    assert result["result"] == "summary"
    assert result["contributors"] == []


@pytest.mark.fast
def test_agent_adapter_process_task_single_agent_path() -> None:
    adapter = AgentAdapter()
    team = StubConsensusTeam([StubAgent("solo", {"result": "done"})])
    adapter.agent_coordinator.teams["default"] = team
    adapter.agent_coordinator.current_team_id = "default"
    adapter.multi_agent_enabled = False

    result = adapter.process_task({"payload": "value"})

    assert result == {"result": "done"}


@pytest.mark.fast
def test_agent_adapter_process_task_multi_agent_path() -> None:
    adapter = AgentAdapter()
    team = StubConsensusTeam([StubAgent("alpha", {"result": "A"}), StubAgent("beta", {"result": "B"})])
    adapter.agent_coordinator.teams["multi"] = team
    adapter.agent_coordinator.current_team_id = "multi"
    adapter.multi_agent_enabled = True

    result = adapter.process_task({"details": "value"})

    assert result["status"] == "ok"
    assert result["consensus"] == "agreement"


@pytest.mark.fast
def test_solution_from_agent_handles_none_response() -> None:
    request = DelegatedTaskRequest.from_mapping({})
    agent = StubAgent("alpha", {"result": "unused"})

    solution = request.solution_from_agent(agent, None)

    assert solution["content"] == ""
    assert solution["confidence"] == 1.0


@pytest.mark.fast
def test_add_agent_creates_default_team() -> None:
    coordinator = WSDETeamCoordinator()
    coordinator.add_agent(StubAgent("alpha", {"result": "ok"}))

    assert coordinator.current_team_id == "default_team"
    assert coordinator.get_team("default_team") is not None


@pytest.mark.fast
def test_create_team_uses_collaboration_when_memory_manager(monkeypatch) -> None:
    created: dict[str, tuple[str, object]] = {}

    def fake_collaborative_team(*, name: str, memory_manager: object):
        created["args"] = (name, memory_manager)
        return StubConsensusTeam([])

    monkeypatch.setattr(
        "devsynth.application.collaboration.collaborative_wsde_team.CollaborativeWSDETeam",
        fake_collaborative_team,
    )

    memory_manager = SimpleNamespace()
    coordinator = WSDETeamCoordinator(memory_manager=memory_manager)
    team = coordinator.create_team("collab")

    assert created["args"] == ("collab", memory_manager)
    assert coordinator.get_team("collab") is team


@pytest.mark.fast
def test_simplified_agent_factory_normalises_configuration() -> None:
    class RecordingAgent(StubAgent):
        def __init__(self) -> None:
            super().__init__("recording", {"result": "ok"})
            self.initialized = None

        def initialize(self, config: object) -> None:  # type: ignore[override]
            self.initialized = config

    factory = SimplifiedAgentFactory()
    factory.register_agent_type("recording", RecordingAgent)

    agent = factory.create_agent("recording", {"capabilities": "solo", "parameters": {"rate": 2}})

    assert isinstance(agent, RecordingAgent)
    assert agent.initialized is not None
    assert agent.initialized.capabilities == []
    assert agent.initialized.parameters == {"rate": 2}


@pytest.mark.fast
def test_simplified_agent_factory_sets_llm_port() -> None:
    class PortAwareAgent(StubAgent):
        def __init__(self) -> None:
            super().__init__("port", {"result": "ok"})
            self.received_port = None

        def set_llm_port(self, port: object) -> None:  # type: ignore[override]
            self.received_port = port

    llm_port = SimpleNamespace()
    factory = SimplifiedAgentFactory(llm_port=llm_port)
    factory.register_agent_type("port", PortAwareAgent)

    agent = factory.create_agent("port")

    assert isinstance(agent, PortAwareAgent)
    assert agent.received_port is llm_port


@pytest.mark.fast
def test_simplified_agent_factory_default_agent() -> None:
    factory = SimplifiedAgentFactory()

    agent = factory.create_agent(AgentType.ORCHESTRATOR.value)

    assert hasattr(agent, "process")


@pytest.mark.fast
def test_simplified_agent_factory_future_registry_branch() -> None:
    class FutureAgent(StubAgent):
        def __init__(self) -> None:
            super().__init__("future", {"result": "ok"})

    factory = SimplifiedAgentFactory()
    factory.future_agent_types["future"] = FutureAgent

    agent = factory.create_agent("future")

    assert isinstance(agent, FutureAgent)


@pytest.mark.fast
def test_agent_adapter_configuration_enables_multi_agent() -> None:
    adapter = AgentAdapter(config={"features": {"wsde_collaboration": True}})

    assert adapter.multi_agent_enabled is True


@pytest.mark.fast
def test_agent_adapter_registers_custom_agent() -> None:
    class RegisteredAgent(StubAgent):
        def __init__(self) -> None:
            super().__init__("registered", {"result": "ok"})

    adapter = AgentAdapter()
    adapter.register_agent_type("registered", RegisteredAgent)
    agent = adapter.create_agent("registered", {"capabilities": ["act"]})

    assert isinstance(agent, RegisteredAgent)


@pytest.mark.fast
def test_agent_adapter_team_helpers_round_trip() -> None:
    adapter = AgentAdapter()
    team = StubConsensusTeam([StubAgent("alpha", {"result": "A"})])
    adapter.agent_coordinator.teams["alpha"] = team
    adapter.agent_coordinator.current_team_id = "alpha"

    assert adapter.get_team("alpha") is team
    adapter.set_current_team("alpha")
    adapter.add_agents_to_team([StubAgent("beta", {"result": "B"})])

    assert len(adapter.get_team("alpha").agents) == 2  # type: ignore[union-attr]


@pytest.mark.fast
def test_agent_adapter_process_task_without_team_raises() -> None:
    adapter = AgentAdapter()

    with pytest.raises(ValidationError):
        adapter.process_task({})


@pytest.mark.fast
def test_wsde_team_coordinator_create_team_without_memory() -> None:
    coordinator = WSDETeamCoordinator()

    team = coordinator.create_team("unit")

    assert coordinator.get_team("unit") is team
