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
            self.error = None
            self.no_solutions = False
            self.dialectical_error = False

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


@given("a coordinator with agents unable to propose solutions")
def setup_agents_no_solution(context):
    agent_names = ["agent1", "agent2"]
    for name in agent_names:
        agent = MagicMock(spec=Agent)
        agent.name = name
        agent.agent_type = "vote"
        agent.process.return_value = {"solution": None}
        context.coordinator.add_agent(agent)
        context.agents.append(agent)
    context.no_solutions = True


@given("the dialectical reasoning module raises an exception")
def dialectical_module_raises(context):
    context.dialectical_error = True


@when("I delegate a voting-based task")
def delegate_voting_task(context):
    context.task = {"vote": True, "description": "choose approach"}
    team = context.coordinator.teams[context.coordinator.current_team_id]
    if context.no_solutions:
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "",
                "contributors": [],
                "method": "consensus",
                "reasoning": "No solutions available",
            }
        )
    else:
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "approved",
                "votes": {a.name: "yes" for a in context.agents},
                "contributors": [a.name for a in context.agents],
                "method": "consensus_vote",
            }
        )

    if context.dialectical_error:
        team.apply_enhanced_dialectical_reasoning_multi = MagicMock(
            side_effect=Exception("Dialectical reasoning failed")
        )

    try:
        context.result = context.coordinator.delegate_task(context.task)
    except Exception as exc:
        context.error = str(exc)


@then("each agent should cast a vote")
def each_agent_votes(context):
    team = context.coordinator.teams[context.coordinator.current_team_id]
    team.build_consensus.assert_called_once_with(context.task)


@then("the outcome should be approved by consensus vote")
def result_consensus_vote(context):
    assert context.result.get("method") == "consensus_vote"
    assert context.result.get("result") == "approved"


@then("the system should return an error message indicating no solutions were proposed")
def no_solutions_error(context):
    assert context.result is not None
    assert context.result.get("reasoning") == "No solutions available"


@then("the system should return a graceful dialectical reasoning error message")
def dialectical_error_message(context):
    assert context.result is None
    assert context.error is not None
    assert "Dialectical reasoning failed" in context.error
