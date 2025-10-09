from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.collaboration.peer_review import run_peer_review
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.wsde_facade import WSDETeam
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "peer_review.feature"))


@pytest.fixture
def context():
    class Context:
        pass

    return Context()


@given("the DevSynth system is initialized")
def system_initialized(context):
    context.coordinator = WSDETeamCoordinator()


@given("a team of agents is configured")
def configure_team(context):
    context.team = context.coordinator.create_team("peer-team")


@given("the WSDE model is enabled")
def wsde_enabled(context):
    assert isinstance(context.team, WSDETeam)


@given("a simple work product and two reviewers")
def simple_work_and_reviewers(context):
    author = UnifiedAgent()
    author.initialize(AgentConfig(name="author", agent_type=AgentType.ORCHESTRATOR))
    r1 = UnifiedAgent()
    r1.initialize(AgentConfig(name="rev1", agent_type=AgentType.ORCHESTRATOR))
    r2 = UnifiedAgent()
    r2.initialize(AgentConfig(name="rev2", agent_type=AgentType.ORCHESTRATOR))
    for agent in (author, r1, r2):
        context.coordinator.add_agent(agent)
    r1.process = MagicMock(return_value={"feedback": "ok", "opinion": "approve"})
    r2.process = MagicMock(return_value={"feedback": "ok", "opinion": "approve"})
    context.team.build_consensus = MagicMock(
        return_value={
            "method": "majority_opinion",
            "majority_opinion": "approve",
            "agent_opinions": {
                "rev1": {"opinion": "approve", "rationale": ""},
                "rev2": {"opinion": "approve", "rationale": ""},
            },
        }
    )
    context.work = {"code": "print('hi')"}
    context.author = author
    context.reviewers = [r1, r2]


@when("the peer review workflow is executed")
def execute_workflow(context):
    context.result = run_peer_review(
        context.work,
        context.author,
        context.reviewers,
        team=context.team,
    )


@then("a consensus result should be produced")
def consensus_result(context):
    assert "consensus" in context.result
    assert context.result["consensus"]["method"] == "majority_opinion"


@then("the system should provide a summary of the consensus")
def summary_of_consensus(context):
    summary = context.team.summarize_consensus_result(context.result["consensus"])
    assert "approve" in summary


@given("a voting result with a clear winner")
def voting_result_setup(context):
    context.team = WSDETeam("vote-team")
    context.voting_result = {
        "status": "completed",
        "result": {"winner": "optA"},
        "vote_counts": {"optA": 3, "optB": 1},
    }


@when("the team summarizes the voting result")
def team_summarizes_vote(context):
    context.vote_summary = context.team.summarize_voting_result(context.voting_result)


@then("the summary should mention the winning option")
def summary_mentions_winner(context):
    assert "optA" in context.vote_summary
