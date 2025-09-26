"""Step definitions for delegate_task_consensus.feature."""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.domain.interfaces.agent import Agent

pytestmark = [pytest.mark.fast]

scenarios("../features/general/delegate_task_consensus.feature")
scenarios("../features/delegating_tasks_with_consensus_voting.feature")


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
                "result": None,
                "status": "failed",
                "consensus": None,
                "initial_preferences": {},
                "final_preferences": {},
                "rounds": [],
                "explanation": "No solutions available",
            }
        )
    else:
        team.build_consensus = MagicMock(
            return_value={
                "result": "approved",
                "status": "approved",
                "consensus": "approved",
                "votes": {a.name: "yes" for a in context.agents},
                "initial_preferences": {a.name: "yes" for a in context.agents},
                "final_preferences": {a.name: "yes" for a in context.agents},
                "rounds": [
                    {
                        "round": 1,
                        "preferences": {a.name: "yes" for a in context.agents},
                    }
                ],
                "explanation": "Consensus reached via vote",
            }
        )

    if context.dialectical_error:
        team.apply_enhanced_dialectical_reasoning_multi = MagicMock(
            side_effect=Exception("Dialectical reasoning failed")
        )
    else:
        team.apply_enhanced_dialectical_reasoning_multi = MagicMock(
            return_value={"status": "ok"}
        )

    try:
        context.result = context.coordinator.delegate_task(context.task)
    except Exception as exc:
        context.error = str(exc)


@then("each agent should cast a vote")
def each_agent_votes(context):
    team = context.coordinator.teams[context.coordinator.current_team_id]
    team.build_consensus.assert_called_once()
    payload = team.build_consensus.call_args.args[0]
    assert payload.get("vote") is True
    assert payload.get("description") == context.task["description"]
    assert set(payload.get("options", [])) == {a.name for a in context.agents}


@then("the outcome should be approved by consensus vote")
def result_consensus_vote(context):
    assert context.result.get("method") == "consensus_deliberation"
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
