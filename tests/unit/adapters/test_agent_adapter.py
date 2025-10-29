"""Unit tests for ``devsynth.adapters.agents.agent_adapter``."""

from __future__ import annotations

import sys
from collections.abc import MutableMapping
from types import ModuleType
from typing import Any

import pytest

from devsynth.adapters.agents import agent_adapter
from devsynth.adapters.agents.agent_adapter import (
    AgentAdapter,
    AgentInitializationPayload,
    SimplifiedAgentFactory,
    WSDETeamCoordinator,
    _coerce_mapping,
    _coerce_str_sequence,
    _coerce_task_solutions,
    _import_agent,
    _load_default_config,
    _UnifiedAgentFallback,
)
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.exceptions import ValidationError


class StubAgent:
    """Minimal agent implementation used for adapter tests."""

    def __init__(self) -> None:
        self.config: AgentConfig | None = None
        self.llm_port: Any | None = None
        self.process_calls: list[dict[str, Any]] = []
        self.name = "stub"

    def initialize(self, config: AgentConfig) -> None:
        self.config = config
        self.name = config.name

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.process_calls.append(inputs)
        return {
            "result": f"answer-{self.name}",
            "confidence": 0.5,
            "reasoning": "stub",
        }

    def get_capabilities(self) -> list[str]:
        return ["stub"]

    def set_llm_port(self, llm_port: Any) -> None:
        self.llm_port = llm_port


class StubTeam:
    """Team stub mirroring the hooks exercised by :class:`WSDETeamCoordinator`."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.agents: list[StubAgent] = []
        self._primus: StubAgent | None = None
        self.added_solutions: list[dict[str, Any]] = []

    def add_agent(self, agent: StubAgent) -> None:
        self.agents.append(agent)

    def assign_roles(self) -> None:  # pragma: no cover - hook unused in tests
        pass

    def vote_on_critical_decision(
        self, task: MutableMapping[str, Any]
    ) -> dict[str, Any]:
        return {"status": "critical", "result": task.get("prompt", "")}

    def select_primus_by_expertise(self, _task: MutableMapping[str, Any]) -> None:
        self._primus = self.agents[0] if self.agents else None

    def get_primus(self) -> StubAgent | None:
        return self._primus

    def add_solution(
        self, task: MutableMapping[str, Any], solution: dict[str, Any]
    ) -> None:
        self.added_solutions.append(solution)
        task.setdefault("solutions", []).append(solution)

    def build_consensus(self, payload: MutableMapping[str, Any]) -> dict[str, Any]:
        options = payload.get("options", [])
        return {
            "status": "ok",
            "result": options[0] if options else None,
            "initial_preferences": {agent.name: 1 for agent in self.agents},
            "final_preferences": {agent.name: 1 for agent in self.agents},
            "rounds": [],
            "explanation": "normalized",
        }

    def apply_enhanced_dialectical_reasoning_multi(
        self, _task: MutableMapping[str, Any], critic_agent: StubAgent
    ) -> dict[str, Any]:
        return {"critic": critic_agent.name}


@pytest.mark.fast
def test_factory_initializes_agent_with_config_payload() -> None:
    """Factory normalizes config dictionaries into :class:`AgentConfig`."""

    class DummyLLMPort:
        pass

    llm_port = DummyLLMPort()
    factory = SimplifiedAgentFactory(llm_port=llm_port)
    factory.register_agent_type(AgentType.CODE.value, StubAgent)

    agent = factory.create_agent(
        AgentType.CODE.value,
        {
            "name": "alpha",
            "description": "Primary coding agent",
            "capabilities": ["refactor", "plan"],
            "parameters": {"temperature": 0.1},
        },
    )

    assert isinstance(agent, StubAgent)
    assert agent.config is not None
    assert agent.config.name == "alpha"
    assert agent.config.agent_type is AgentType.CODE
    assert agent.config.capabilities == ["refactor", "plan"]
    assert agent.config.parameters == {"temperature": 0.1}
    assert agent.llm_port is llm_port


@pytest.mark.fast
def test_delegate_task_builds_consensus_payload_from_solutions(monkeypatch) -> None:
    """Coordinator shapes tasks and consensus results without real backends."""

    monkeypatch.setattr(
        "devsynth.adapters.agents.agent_adapter.WSDETeam", StubTeam, raising=False
    )

    coordinator = WSDETeamCoordinator()
    coordinator.teams["team-alpha"] = StubTeam("team-alpha")
    coordinator.current_team_id = "team-alpha"
    team = coordinator.teams["team-alpha"]

    first_agent = StubAgent()
    second_agent = StubAgent()
    first_agent.initialize(AgentConfig(name="alpha", agent_type=AgentType.CODE))
    second_agent.initialize(AgentConfig(name="bravo", agent_type=AgentType.CODE))

    coordinator.add_agents([first_agent, second_agent])

    task: MutableMapping[str, Any] = {"prompt": "Solve"}
    result = coordinator.delegate_task(task)

    assert result["status"] == "ok"
    assert result["method"] == "consensus_deliberation"
    assert result["consensus"] == "answer-alpha"
    assert result["contributors"] == ["alpha", "bravo"]
    assert result["dialectical_analysis"] == {"critic": "alpha"}
    assert team.added_solutions and len(task["solutions"]) == 2
    assert task["solutions"][0]["agent"] == "alpha"


@pytest.mark.fast
def test_process_task_without_agents_raises_validation_error() -> None:
    """Single-agent mode guards against missing team members."""

    adapter = AgentAdapter(config={"features": {"wsde_collaboration": False}})

    with pytest.raises(ValidationError):
        adapter.process_task({})


@pytest.mark.fast
def test_coerce_task_solutions_filters_invalid_entries() -> None:
    """Normalization drops malformed solutions and coerces types."""

    data = [
        {"agent": 42, "content": 99, "confidence": "0.3", "reasoning": 123},
        "invalid",
        {"agent": "beta", "content": "answer", "confidence": 0.7},
    ]

    result = _coerce_task_solutions(data)

    assert result[0] == {
        "agent": "42",
        "content": "99",
        "reasoning": "123",
    }
    assert result[1] == {
        "agent": "beta",
        "content": "answer",
        "confidence": 0.7,
    }


@pytest.mark.fast
def test_import_agent_falls_back_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Import failures resolve to the provided fallback class."""

    class LocalFallback(_UnifiedAgentFallback):
        pass

    def boom(module_path: str) -> None:
        raise ImportError(f"boom:{module_path}")

    monkeypatch.setattr(agent_adapter, "import_module", boom)

    resolved = _import_agent("missing.module", "MissingClass", LocalFallback)

    assert resolved is LocalFallback


@pytest.mark.fast
def test_import_agent_rejects_non_class(monkeypatch: pytest.MonkeyPatch) -> None:
    """Attributes that are not classes fall back gracefully."""

    module_name = "tests.unit.adapters.dummy_module"
    dummy_module = ModuleType(module_name)
    dummy_module.Agent = object()
    sys.modules[module_name] = dummy_module

    try:
        resolved = _import_agent(module_name, "Agent", _UnifiedAgentFallback)
    finally:
        sys.modules.pop(module_name, None)

    assert resolved is _UnifiedAgentFallback


@pytest.mark.fast
def test_lookup_agent_class_caches_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """Factory caches resolved lookups to avoid repeated imports."""

    factory = SimplifiedAgentFactory()

    class CustomAgent(StubAgent):
        pass

    factory.register_agent_type("custom", CustomAgent)
    assert factory._lookup_agent_class("custom") is CustomAgent

    monkeypatch.setattr(agent_adapter, "_import_agent", lambda *args: StubAgent)
    resolved = factory._lookup_agent_class(AgentType.CODE.value)
    assert resolved is StubAgent
    # Cache should now return the resolved class without calling the monkeypatched helper
    monkeypatch.setattr(
        agent_adapter, "_import_agent", lambda *args: _UnifiedAgentFallback
    )
    assert factory._lookup_agent_class(AgentType.CODE.value) is StubAgent


@pytest.mark.fast
def test_delegate_task_handles_processing_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Coordinator tolerates agent processing errors and builds fallback options."""

    class FlakyAgent(StubAgent):
        def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("fail")

    class ReliableAgent(StubAgent):
        def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
            return {
                "result": "win",
                "confidence": 1,
                "reasoning": "coherent",
            }

    class SparseTeam(StubTeam):
        def add_solution(self, task, solution):  # type: ignore[override]
            self.added_solutions.append(solution)

        def build_consensus(self, payload):  # type: ignore[override]
            return {
                "status": "ok",
                "result": payload["options"][0],
                "initial_preferences": {agent.name: 1 for agent in self.agents},
                "final_preferences": {agent.name: 1 for agent in self.agents},
                "rounds": ["r1"],
                "explanation": "agreement",
            }

    monkeypatch.setattr(
        "devsynth.adapters.agents.agent_adapter.WSDETeam", SparseTeam, raising=False
    )

    coordinator = WSDETeamCoordinator()
    team = SparseTeam("team")
    coordinator.teams["team"] = team
    coordinator.current_team_id = "team"

    flaky = FlakyAgent()
    flaky.initialize(AgentConfig(name="flaky", agent_type=AgentType.CODE))
    reliable = ReliableAgent()
    reliable.initialize(AgentConfig(name="reliable", agent_type=AgentType.CODE))

    coordinator.add_agents([flaky, reliable])

    result = coordinator.delegate_task({"prompt": "go"})

    assert result["contributors"] == ["flaky", "reliable"]
    assert result["consensus"] == "flaky"
    assert result["dialectical_analysis"] == {"critic": "flaky"}


@pytest.mark.fast
def test_delegate_task_handles_critical_decisions() -> None:
    """Critical tasks bypass consensus and use the voting pathway."""

    coordinator = WSDETeamCoordinator()
    team = StubTeam("critical")
    coordinator.teams["critical"] = team
    coordinator.current_team_id = "critical"

    agent_one = StubAgent()
    agent_two = StubAgent()
    team.add_agent(agent_one)
    team.add_agent(agent_two)

    result = coordinator.delegate_task(
        {"type": "critical_decision", "is_critical": True}
    )

    assert result["status"] == "critical"


@pytest.mark.fast
def test_delegate_task_requires_active_team() -> None:
    """Coordinator raises when no team is active."""

    coordinator = WSDETeamCoordinator()

    with pytest.raises(ValidationError):
        coordinator.delegate_task({})


@pytest.mark.fast
def test_agent_adapter_process_task_single_agent_flow() -> None:
    """Single-agent mode proxies processing to the first agent."""

    adapter = AgentAdapter(config={"features": {"wsde_collaboration": False}})
    team = StubTeam("solo")
    agent = StubAgent()
    agent.initialize(AgentConfig(name="solo", agent_type=AgentType.CODE))

    adapter.agent_coordinator.teams["solo"] = team
    adapter.agent_coordinator.current_team_id = "solo"
    team.add_agent(agent)

    result = adapter.process_task({"prompt": "work"})

    assert result["result"] == "answer-solo"


@pytest.mark.fast
def test_agent_initialization_payload_handles_unknown_type() -> None:
    """Unknown agent types fall back to the orchestrator role."""

    payload = AgentInitializationPayload.from_mapping(
        {
            "name": "mystery",
            "description": "Unknown agent",
            "capabilities": ("plan", "critique"),
            "parameters": {"depth": 2},
        },
        "mystery",
    )

    assert payload.agent_type is AgentType.ORCHESTRATOR
    assert payload.capabilities == ["plan", "critique"]
    assert payload.parameters == {"depth": 2}


@pytest.mark.fast
def test_coerce_helpers_normalize_inputs() -> None:
    """Helper utilities coerce mappings and iterables into predictable types."""

    mapping_result = _coerce_mapping({1: "value"})
    sequence_result = _coerce_str_sequence({"alpha", "beta"})

    assert mapping_result == {"1": "value"}
    assert sorted(sequence_result) == ["alpha", "beta"]


@pytest.mark.fast
def test_unified_agent_fallback_behaviour() -> None:
    """Fallback agent provides minimal behaviour without optional deps."""

    fallback = _UnifiedAgentFallback()
    config = AgentConfig(name="fallback", agent_type=AgentType.CODE)
    fallback.initialize(config)
    fallback.set_llm_port("llm")

    result = fallback.process({"result": "ok"})

    assert fallback.config is config
    assert fallback.get_capabilities() == []
    assert result == {"status": "ok", "result": "ok"}
    assert fallback.llm_port == "llm"


@pytest.mark.fast
def test_load_default_config_uses_yaml_loader(tmp_path, monkeypatch) -> None:
    """Default config loader defers to yaml.safe_load when available."""

    config_file = tmp_path / "default.yml"
    config_file.write_text("features:\n  wsde_collaboration: true\n", encoding="utf-8")

    class DummyYaml:
        def safe_load(self, handle: Any) -> dict[str, Any]:
            return {"features": {"wsde_collaboration": True}}

    monkeypatch.setattr(agent_adapter, "import_module", lambda name: DummyYaml())

    data = _load_default_config(config_file)

    assert data["features"]["wsde_collaboration"] is True


@pytest.mark.fast
def test_lookup_agent_class_uses_future_specs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Future agent specifications resolve through the cached loader."""

    factory = SimplifiedAgentFactory()
    monkeypatch.setattr(agent_adapter, "_import_agent", lambda *args: StubAgent)

    resolved = factory._lookup_agent_class(AgentType.CRITIC.value)

    assert resolved is StubAgent


@pytest.mark.fast
def test_create_team_uses_collaborative_when_memory_manager(monkeypatch) -> None:
    """Coordinator selects the collaborative team when memory is available."""

    created: dict[str, Any] = {}

    class DummyTeam(StubTeam):
        def __init__(self, name: str, memory_manager: Any) -> None:
            super().__init__(name)
            created["args"] = (name, memory_manager)

    module_name = "devsynth.application.collaboration.collaborative_wsde_team"
    stub_module = ModuleType(module_name)
    stub_module.CollaborativeWSDETeam = DummyTeam  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, module_name, stub_module)

    coordinator = WSDETeamCoordinator(memory_manager=object())
    team = coordinator.create_team("memory-team")

    assert isinstance(team, DummyTeam)
    assert created["args"][0] == "memory-team"
    assert coordinator.current_team_id == "memory-team"


@pytest.mark.fast
def test_add_agent_creates_default_team(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adding an agent with no active team creates the default team."""

    coordinator = WSDETeamCoordinator()

    def fake_create(team_id: str) -> StubTeam:
        team = StubTeam(team_id)
        coordinator.teams[team_id] = team
        coordinator.current_team_id = team_id
        return team

    monkeypatch.setattr(coordinator, "create_team", fake_create)

    agent = StubAgent()
    coordinator.add_agent(agent)

    assert coordinator.current_team_id == "default_team"
    assert coordinator.teams["default_team"].agents[0] is agent


@pytest.mark.fast
def test_agent_adapter_register_agent_type() -> None:
    """Test that agent types can be registered."""
    adapter = AgentAdapter()
    adapter.register_agent_type("test_agent", StubAgent)
    # The factory should now be able to create this agent type
    agent = adapter.create_agent("test_agent")
    assert isinstance(agent, StubAgent)


@pytest.mark.fast
def test_agent_adapter_get_team() -> None:
    """Test getting a team by ID."""
    adapter = AgentAdapter()
    team = adapter.create_team("test_team")
    retrieved = adapter.get_team("test_team")
    assert retrieved is team
    assert retrieved.name == "test_team"


@pytest.mark.fast
def test_agent_adapter_get_team_nonexistent() -> None:
    """Test getting a nonexistent team returns None."""
    adapter = AgentAdapter()
    result = adapter.get_team("nonexistent")
    assert result is None


@pytest.mark.fast
def test_agent_adapter_set_current_team() -> None:
    """Test setting the current active team."""
    adapter = AgentAdapter()
    team1 = adapter.create_team("team1")
    team2 = adapter.create_team("team2")

    # Initially, the last created team should be current
    assert adapter.agent_coordinator.current_team_id == "team2"

    # Set current team explicitly
    adapter.set_current_team("team1")
    assert adapter.agent_coordinator.current_team_id == "team1"


@pytest.mark.fast
def test_agent_adapter_process_task_multi_agent_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When collaboration is enabled, the adapter delegates to the coordinator."""

    adapter = AgentAdapter(config={"features": {"wsde_collaboration": True}})

    monkeypatch.setattr(
        adapter.agent_coordinator,
        "delegate_task",
        lambda task: {"handled": task.get("prompt")},
    )

    result = adapter.process_task({"prompt": "multi"})

    assert result == {"handled": "multi"}
