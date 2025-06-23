"""Step definitions for delegate_task_consensus.feature."""

import pytest
from unittest.mock import MagicMock
from pytest_bdd import scenarios, given, when, then

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.domain.interfaces.agent import Agent

scenarios("../features/delegate_task_consensus.feature")


@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.coordinator = WSDETeamCoordinator()
            self.agents = []
            self.task = None
            self.result = None
    return Context()


@given("a coordinator with agents capable of voting")
def setup_voting_team(context):
    agent_names = ["agent1", "agent2", "agent3"]
    for name in agent_names:
        agent = MagicMock(spec=Agent)
        agent.name = name
        agent.agent_type = "vote"
        agent.process.return_value = {"solution": f"solution from {name}"}
        context.coordinator.add_agent(agent)
        context.agents.append(agent)


@when("I delegate a voting-based task")
def delegate_voting_task(context):
    context.task = {"vote": True, "description": "choose approach"}
    team = context.coordinator.teams[context.coordinator.current_team_id]
    team.build_consensus = MagicMock(
        return_value={
            "consensus": "approved",
            "votes": {a.name: "yes" for a in context.agents},
            "contributors": [a.name for a in context.agents],
            "method": "consensus_vote",
        }
    )
    context.result = context.coordinator.delegate_task(context.task)


@then("each agent should cast a vote")
def each_agent_votes(context):
    team = context.coordinator.teams[context.coordinator.current_team_id]
    team.build_consensus.assert_called_once_with(context.task)

@then("the outcome should be approved by consensus vote")
def result_consensus_vote(context):
    assert context.result.get("method") == "consensus_vote"
    assert context.result.get("result") == "approved"
