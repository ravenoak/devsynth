"""Step definitions for delegate_task.feature."""

import pytest
from unittest.mock import MagicMock
from pytest_bdd import scenarios, given, when, then

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.domain.interfaces.agent import Agent

scenarios("../features/delegate_task.feature")


@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.coordinator = WSDETeamCoordinator()
            self.agents = []
            self.result = None
            self.task = None
    return Context()


@given("a team coordinator with multiple agents")
def setup_team(context):
    # Create mock agents with names and types
    agent_types = ["planner", "code", "test", "validation"]
    for idx, a_type in enumerate(agent_types):
        agent = MagicMock(spec=Agent)
        agent.name = f"agent{idx}"
        agent.agent_type = a_type
        agent.process.return_value = {"solution": f"solution from {agent.name}"}
        context.coordinator.add_agent(agent)
        context.agents.append(agent)


@when("I delegate a collaborative team task")
def delegate_task(context):
    context.task = {"team_task": True, "description": "do work"}
    # Mock build_consensus on the team to return contributions from all agents
    team = context.coordinator.teams[context.coordinator.current_team_id]
    team.build_consensus = MagicMock(
        return_value={
            "consensus": "final",
            "contributors": [a.name for a in context.agents],
            "method": "consensus_synthesis",
        }
    )
    context.result = context.coordinator.delegate_task(context.task)


@then("each agent should process the task")
def each_agent_processed(context):
    for agent in context.agents:
        agent.process.assert_called()


@then("the delegation result should include all contributors")
def result_includes_contributors(context):
    assert set(context.result.get("contributors", [])) == {a.name for a in context.agents}


@then("the delegation method should be consensus based")
def method_consensus(context):
    assert context.result.get("method") == "consensus_synthesis"
