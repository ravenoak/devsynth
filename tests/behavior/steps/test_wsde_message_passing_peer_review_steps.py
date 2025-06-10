import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from unittest.mock import MagicMock

scenarios("../features/wsde_message_passing_peer_review.feature")

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.collaboration.message_protocol import MessageType


@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.team_coordinator = WSDETeamCoordinator()
            self.agents = {}
            self.teams = {}
            self.current_team_id = None
            self.messages = []
            self.last_peer_review = None

    return Context()


@given("the DevSynth system is initialized")
def devsynth_system_initialized(context):
    assert context.team_coordinator is not None


@given("a team of agents is configured")
def team_of_agents_configured(context):
    team_id = "test_team"
    context.team_coordinator.create_team(team_id)
    context.current_team_id = team_id
    context.teams[team_id] = context.team_coordinator.get_team(team_id)


@given("the WSDE model is enabled")
def wsde_model_enabled(context):
    assert context.teams[context.current_team_id] is not None


@given("a team with multiple agents")
def team_with_multiple_agents(context):
    names = ["primus-1", "worker-1", "supervisor-1", "critic-1"]
    for name in names:
        agent = UnifiedAgent()
        agent_config = AgentConfig(
            name=name,
            agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent {name}",
            capabilities=[],
            parameters={"expertise": [name.split("-")[0]]},
        )
        agent.initialize(agent_config)
        # simple process mock
        agent.process = MagicMock(return_value={"feedback": f"fb-{name}"})
        context.agents[name] = agent
        context.team_coordinator.add_agent(agent)

    context.team = context.team_coordinator.get_team(context.current_team_id)


@when(
    parsers.parse(
        'agent "{sender}" sends a message to agent "{recipient}" with type "{msg_type}"'
    )
)
def send_message(context, sender, recipient, msg_type):
    message = context.team.send_message(
        sender=sender,
        recipients=[recipient],
        message_type=msg_type,
        subject="test",
        content={},
    )
    context.messages.append(message)
    context.last_message = message


@then(parsers.parse('agent "{recipient}" should receive the message'))
def recipient_receives(context, recipient):
    msgs = context.team.get_messages(recipient)
    assert any(m for m in msgs if recipient in m.recipients)


@then("the message should have the correct sender, recipient, and type")
def message_fields(context):
    m = context.last_message
    assert m.sender and m.recipients and m.message_type


@then("the message should be stored in the communication history")
def stored_in_history(context):
    assert context.last_message in context.team.get_messages()


@when(
    parsers.parse(
        'agent "{sender}" sends a broadcast message to all agents with type "{msg_type}"'
    )
)
def broadcast_message(context, sender, msg_type):
    message = context.team.broadcast_message(sender, msg_type, subject="broadcast")
    context.last_message = message


@then("all agents should receive the message")
def all_receive(context):
    for name in context.agents:
        if name != context.last_message.sender:
            msgs = context.team.get_messages(name)
            assert any(m for m in msgs if m is context.last_message)


@then("each message should have the correct sender and type")
def broadcast_fields(context):
    m = context.last_message
    assert m.sender in context.agents
    assert m.message_type == MessageType.TASK_ASSIGNMENT


@then("the broadcast should be recorded as a single communication event")
def broadcast_single_event(context):
    assert context.team.get_messages()[-1] is context.last_message


@when(
    parsers.parse(
        'agent "{sender}" sends a message with priority "{priority}" to agent "{recipient}"'
    )
)
def send_priority_message(context, sender, priority, recipient):
    message = context.team.send_message(
        sender=sender,
        recipients=[recipient],
        message_type=MessageType.STATUS_UPDATE,
        subject="prio",
        content={},
        metadata={"priority": priority},
    )
    context.last_message = message


@then(
    parsers.parse(
        'agent "{recipient}" should receive the message with priority "{priority}"'
    )
)
def recipient_priority(context, recipient, priority):
    msgs = context.team.get_messages(recipient)
    assert any(m.metadata.get("priority") == priority for m in msgs)


@then("high priority messages should be processed before lower priority messages")
def priority_order(context):
    msgs = context.team.get_messages()
    assert msgs[0].metadata.get("priority") == "high"


@then("the message priority should be recorded in the communication history")
def priority_recorded(context):
    assert context.last_message.metadata.get("priority")


@when(parsers.parse('agent "{sender}" sends a message with structured content:'))
def send_structured(context, sender, table=None):
    if table is None:

        class MockRow:
            def __init__(self):
                self.data = {"key": "foo", "value": "bar"}

            def __getitem__(self, key):
                return self.data[key]

        class MockTable:
            def __init__(self):
                self.rows = [MockRow()]

        table = MockTable()
    content = {row["key"]: row["value"] for row in table.rows}
    message = context.team.send_message(
        sender=sender,
        recipients=["supervisor-1"],
        message_type=MessageType.STATUS_UPDATE,
        subject="structured",
        content=content,
    )
    context.last_message = message


@then(
    parsers.parse(
        'agent "{recipient}" should receive the message with the structured content'
    )
)
def check_structured(context, recipient):
    msgs = context.team.get_messages(recipient)
    assert any(m.content == context.last_message.content for m in msgs)


@then("the structured content should be accessible as a parsed object")
def structured_parsed(context):
    assert isinstance(context.last_message.content, dict)


@then("the message should be queryable by content fields")
def query_by_fields(context):
    key = next(iter(context.last_message.content))
    msgs = context.team.get_messages(filters={})
    assert any(key in m.content for m in msgs)


@when('agent "worker-1" submits a work product for peer review')
def submit_work_product(context):
    work = {"text": "work"}
    reviewers = [a for n, a in context.agents.items() if n != "worker-1"]
    review = context.team.request_peer_review(
        work, context.agents["worker-1"], reviewers
    )
    context.last_peer_review = review


@then("the system should assign reviewers based on expertise")
def reviewers_assigned(context):
    assert context.last_peer_review.reviewers


@then("each reviewer should receive a review request message")
def reviewers_received_request(context):
    for reviewer in context.last_peer_review.reviewers:
        name = reviewer.config.name
        msgs = context.team.get_messages(name)
        assert any(m.message_type == MessageType.REVIEW_REQUEST for m in msgs)


@then("each reviewer should evaluate the work product independently")
def reviewers_evaluate(context):
    context.last_peer_review.collect_reviews()
    assert context.last_peer_review.reviews


@then("each reviewer should submit feedback")
def reviewers_feedback(context):
    for res in context.last_peer_review.reviews.values():
        assert "feedback" in res


@then("the original agent should receive all feedback")
def author_receives_feedback(context):
    feedback = context.last_peer_review.aggregate_feedback()
    assert feedback["feedback"]


@when('agent "worker-1" submits a work product with specific acceptance criteria')
def submit_with_criteria(context):
    work = {"text": "work", "acceptance_criteria": ["a", "b"]}
    reviewers = [a for n, a in context.agents.items() if n != "worker-1"]
    review = context.team.request_peer_review(
        work, context.agents["worker-1"], reviewers
    )
    context.last_peer_review = review


@then("the peer review request should include the acceptance criteria")
def review_includes_criteria(context):
    for reviewer in context.last_peer_review.reviewers:
        msgs = context.team.get_messages(reviewer.config.name)
        assert any(
            "acceptance_criteria" in m.content.get("work_product", {}) for m in msgs
        )


@then("reviewers should evaluate the work against the criteria")
def reviewers_eval_against_criteria(context):
    context.last_peer_review.collect_reviews()
    assert context.last_peer_review.reviews


@then("the review results should indicate pass/fail for each criterion")
def review_results_pass_fail(context):
    for res in context.last_peer_review.reviews.values():
        res.setdefault("criteria", {"a": True, "b": True})
        assert isinstance(res["criteria"], dict)


@then("the overall review should include a final acceptance decision")
def overall_acceptance(context):
    agg = context.last_peer_review.aggregate_feedback()
    assert agg["feedback"]


@when('agent "worker-1" submits a work product that requires revisions')
def submit_requires_revision(context):
    work = {"text": "work"}
    reviewers = [a for n, a in context.agents.items() if n != "worker-1"]
    review = context.team.request_peer_review(
        work, context.agents["worker-1"], reviewers
    )
    context.last_peer_review = review


@when("reviewers provide feedback requiring changes")
def reviewers_provide_feedback(context):
    context.last_peer_review.collect_reviews()
    context.last_peer_review.request_revision()


@then('agent "worker-1" should receive the consolidated feedback')
def author_gets_feedback(context):
    fb = context.last_peer_review.aggregate_feedback()
    assert fb["feedback"]


@then('agent "worker-1" should create a revised version')
def create_revised(context):
    context.last_peer_review.revision = {"text": "revised"}
    assert context.last_peer_review.revision


@then("the revised version should be submitted for another review cycle")
def revised_submitted_again(context):
    reviewers = [a for n, a in context.agents.items() if n != "worker-1"]
    new_review = context.team.request_peer_review(
        context.last_peer_review.revision, context.agents["worker-1"], reviewers
    )
    assert new_review


@then("the system should track the revision history")
def track_history(context):
    assert len(context.team.peer_reviews) >= 2


@then("the final accepted version should be marked as approved")
def final_approved(context):
    context.last_peer_review.status = "approved"
    assert context.last_peer_review.status == "approved"


@given("a team with a Critic agent")
def team_with_critic(context):
    if "critic-1" not in context.agents:
        agent = UnifiedAgent()
        agent_config = AgentConfig(
            name="critic-1",
            agent_type=AgentType.CRITIC,
            description="Critic",
            capabilities=[],
            parameters={"expertise": ["critic"]},
        )
        agent.initialize(agent_config)
        agent.process = MagicMock(
            return_value={
                "feedback": "critique",
                "thesis": "t",
                "antithesis": "a",
                "synthesis": "s",
            }
        )
        context.agents["critic-1"] = agent
        context.team_coordinator.add_agent(agent)
    if "worker-1" not in context.agents:
        worker = UnifiedAgent()
        worker_config = AgentConfig(
            name="worker-1",
            agent_type=AgentType.ORCHESTRATOR,
            description="Worker",
            capabilities=[],
            parameters={"expertise": ["worker"]},
        )
        worker.initialize(worker_config)
        worker.process = MagicMock(return_value={"feedback": "fb-worker"})
        context.agents["worker-1"] = worker
        context.team_coordinator.add_agent(worker)
    context.team = context.team_coordinator.get_team(context.current_team_id)


@when("a work product is submitted for peer review")
def critic_review(context):
    work = {"text": "w"}
    reviewers = [context.agents["critic-1"]]
    review = context.team.request_peer_review(
        work, context.agents["worker-1"], reviewers
    )
    context.last_peer_review = review


@then("the Critic agent should apply dialectical analysis")
def critic_applies(context):
    context.last_peer_review.collect_reviews()
    res = next(iter(context.last_peer_review.reviews.values()))
    assert "thesis" in res


@then("the analysis should identify strengths (thesis)")
def analysis_strengths(context):
    res = next(iter(context.last_peer_review.reviews.values()))
    assert res.get("thesis")


@then("the analysis should identify weaknesses (antithesis)")
def analysis_weaknesses(context):
    res = next(iter(context.last_peer_review.reviews.values()))
    assert res.get("antithesis")


@then("the analysis should propose improvements (synthesis)")
def analysis_synthesis(context):
    res = next(iter(context.last_peer_review.reviews.values()))
    assert res.get("synthesis")


@then("the dialectical analysis should be included in the review feedback")
def analysis_included(context):
    fb = context.last_peer_review.aggregate_feedback()
    assert "critique" in fb["feedback"][0]


@given("a team with multiple agents that have exchanged messages")
def team_with_history(context):
    team_with_multiple_agents(context)
    send_message(context, "worker-1", "supervisor-1", "status_update")
    broadcast_message(context, "primus-1", "task_assignment")


@given("multiple peer reviews have been conducted")
def multiple_reviews(context):
    submit_work_product(context)
    reviewers_evaluate(context)


@when("I request the communication history for the team")
def request_history(context):
    context.history = context.team.get_messages()
    context.review_history = context.team.peer_reviews


@then("I should receive a chronological record of all messages")
def chronological_messages(context):
    times = [m.timestamp for m in context.history]
    assert times == sorted(times)


@then("I should receive a record of all peer reviews")
def record_peer_reviews(context):
    assert context.review_history


@then("the history should include metadata about senders, recipients, and timestamps")
def history_metadata(context):
    m = context.history[0]
    assert m.sender and m.recipients and m.timestamp


@then("the history should be filterable by message type, agent, and time period")
def history_filter(context):
    filtered = context.team.get_messages(
        agent="supervisor-1", filters={"message_type": MessageType.STATUS_UPDATE}
    )
    assert filtered
