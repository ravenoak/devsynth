from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.collaboration.WSDE import WSDE
from devsynth.domain.wsde.workflow import progress_roles
from devsynth.methodology.base import Phase
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "collaboration_flow.feature"))


@pytest.fixture
def context():
    class Context:
        pass

    return Context()


@given("a WSDE team with pending memory")
def wsde_team_with_pending_memory(context):
    context.team = WSDE(name="bdd-team")
    agent = MagicMock()
    agent.name = "agent"
    context.team.add_agent(agent)
    mm = MagicMock()
    mm.sync_manager = MagicMock()
    mm.sync_manager._queue = [("default", MagicMock())]
    mm.flush_updates = MagicMock(side_effect=lambda: mm.sync_manager._queue.clear())
    context.memory_manager = mm


@when("the team progresses through the EXPAND phase")
def progress_expand_phase(context):
    progress_roles(context.team, Phase.EXPAND, context.memory_manager)


@then("the role assignments are returned by identifier")
def role_assignments_by_identifier(context):
    assignments = context.team.get_role_assignments()
    assert list(assignments.keys()) == [context.team.agents[0].id]


@then("the memory queue is empty")
def memory_queue_is_empty(context):
    assert context.memory_manager.flush_updates.called
    assert context.memory_manager.sync_manager._queue == []
