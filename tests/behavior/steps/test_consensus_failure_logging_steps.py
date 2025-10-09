import logging
from datetime import datetime

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.collaboration.WSDE import WSDE
from devsynth.logger import DevSynthLogger
from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

scenarios(feature_path(__file__, "general", "consensus_failure_logging.feature"))


class DummyAgent:
    def __init__(self, name: str):
        self.name = name
        self.expertise = ["general"]
        self.current_role = None


@pytest.fixture
def context():
    class Context:
        pass

    ctx = Context()
    ctx.task = {"id": "t1", "title": "Test"}
    return ctx


@given("a WSDE team whose vote fails to reach a decision")
def given_team(context):
    team = WSDE("bdd-team", agents=[DummyAgent("a1"), DummyAgent("a2")])
    team.logger = DevSynthLogger("bdd")

    def failing_vote(task):
        return {"status": "failed"}

    def fallback_consensus(task):
        return {"method": "fallback"}

    team.consensus_vote = failing_vote
    team.build_consensus = fallback_consensus
    context.team = team


@when("the team runs consensus on a task")
def when_run_consensus(context, caplog):
    caplog.set_level(logging.ERROR)
    context.result = context.team.run_consensus(context.task)
    context.log_records = [
        r for r in caplog.records if r.message == "Consensus failure"
    ]


@then("a consensus failure is logged")
def then_logged(context):
    assert context.log_records, "Consensus failure was not logged"


@then("the result includes a fallback consensus")
def then_fallback(context):
    assert "consensus" in context.result
    assert context.result["consensus"].get("method") == "fallback"
