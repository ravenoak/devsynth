"""Step definitions for delegate_task.feature without mocks."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.domain.models.wsde_facade import WSDETeam
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


def _module_stub(name: str, **attributes: object) -> ModuleType:
    """Return a module-like namespace populated with the provided attributes."""

    module = ModuleType(name)
    for attribute, value in attributes.items():
        setattr(module, attribute, value)
    return module


def _load_coordinator() -> AgentCoordinatorImpl:
    """Import and return a fresh ``AgentCoordinatorImpl`` instance."""

    module_name = "devsynth.application.collaboration.coordinator"
    module = importlib.import_module(module_name)
    sys.modules.setdefault(module_name, module)
    coordinator_cls = getattr(module, "AgentCoordinatorImpl")
    return coordinator_cls({"features": {"wsde_collaboration": True}})


scenarios(feature_path(__file__, "general", "delegate_task.feature"))
scenarios(feature_path(__file__, "general", "multi_agent_task_delegation.feature"))


class SimpleTeam(WSDETeam):
    """WSDE team with deterministic consensus and dialectical hooks."""

    def __init__(self) -> None:
        super().__init__(name="TestSimpleTeam")
        self.dialectical_called = False

    def build_consensus(self, task):  # type: ignore[override]
        return {
            "consensus": "final",
            "contributors": [a.name for a in self.agents],
            "method": "consensus_synthesis",
        }

    def apply_enhanced_dialectical_reasoning(self, task, critic_agent):  # type: ignore[override]
        self.dialectical_called = True
        return {"steps": ["thesis", "antithesis", "synthesis"]}


class SimpleAgent:
    """Minimal agent implementation used for behavior tests."""

    def __init__(
        self, name: str, agent_type: str, expertise: list[str] | None = None
    ) -> None:
        self.name = name
        self.agent_type = agent_type
        self.expertise = expertise or []
        self.current_role = None
        self.config = _module_stub(
            f"{name}_config",
            name=name,
            parameters={"expertise": self.expertise},
        )

        def process(inputs):
            result = {"solution": f"solution from {self.name}"}
            setattr(process, "return_value", result)
            self.last_inputs = inputs
            return result

        self.process = process

    def initialize(self, config) -> None:  # noqa: D401 - part of Agent protocol
        self.config = config

    def get_capabilities(self) -> list[str]:
        return self.expertise


@pytest.fixture
def context():
    class Context:
        def __init__(self) -> None:
            self.coordinator = _load_coordinator()
            self.coordinator.team = SimpleTeam()
            self.agents: list[SimpleAgent] = []
            self.result = None
            self.task = None
            self.critic: SimpleAgent | None = None

    return Context()


@given("a team coordinator with multiple agents")
def setup_team(context) -> None:
    specs = [
        ("planner", "planner", ["planning"]),
        ("code", "code", ["coding"]),
        ("test", "test", ["testing"]),
        ("validation", "validation", ["qa"]),
    ]
    for name, agent_type, exp in specs:
        agent = SimpleAgent(name, agent_type, exp)
        context.coordinator.add_agent(agent)
        context.agents.append(agent)


@given("a critic agent with dialectical reasoning expertise")
def add_critic_agent(context) -> None:
    critic = SimpleAgent("critic", "critic", ["analysis"])
    context.coordinator.add_agent(critic)
    context.agents.append(critic)
    context.critic = critic


@when("I delegate a collaborative team task")
def delegate_task(context) -> None:
    context.task = {"team_task": True, "description": "do work"}
    context.result = context.coordinator.delegate_task(context.task)


@when("I delegate a dialectical reasoning task")
def delegate_dialectical_task(context) -> None:
    context.task = {"team_task": True, "dialectical": True, "description": "debate"}
    context.result = context.coordinator.delegate_task(context.task)


@then("each agent should process the task")
def each_agent_processed(context) -> None:
    for agent in context.agents:
        assert hasattr(agent, "last_inputs")
        assert context.task["description"] in agent.last_inputs.get("description", "")


@then("the delegation result should include all contributors")
def result_includes_contributors(context) -> None:
    assert set(context.result.get("contributors", [])) == {
        a.name for a in context.agents
    }


@then("the consensus result should be final")
def consensus_result_final(context) -> None:
    assert context.result.get("result") == "final"


@then("the delegation method should be consensus based")
def method_consensus(context) -> None:
    assert context.result.get("method") == "consensus_synthesis"


@then("the team should apply dialectical reasoning before consensus")
def dialectical_reasoning_applied(context) -> None:
    team: SimpleTeam = context.coordinator.team  # type: ignore[assignment]
    assert team.dialectical_called is True
