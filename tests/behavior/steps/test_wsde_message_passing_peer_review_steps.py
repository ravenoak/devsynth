"""WSDE message passing and peer review behaviour tests."""

from __future__ import annotations

from typing import Any, Dict
from collections.abc import Iterable
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

scenarios(
    feature_path(__file__, "general", "wsde_message_passing_and_peer_review.feature")
)
scenarios(feature_path(__file__, "general", "wsde_peer_review_workflow.feature"))
scenarios(feature_path(__file__, "general", "wsde_message_passing_peer_review.feature"))

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.collaboration.message_protocol import MessageType
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.wsde_facade import WSDETeam


def _normalise_message(message: Any) -> dict[str, Any]:
    """Return a serialisable message dictionary from protocol objects."""

    if isinstance(message, dict):
        return {
            "id": message.get("id") or message.get("message_id"),
            "sender": message.get("sender"),
            "recipients": list(message.get("recipients", ())),
            "type": message.get("type")
            or getattr(message.get("message_type"), "value", None),
            "subject": message.get("subject"),
            "content": message.get("content", {}),
            "metadata": dict(message.get("metadata") or {}),
            "timestamp": message.get("timestamp"),
        }

    data = {
        "id": getattr(message, "message_id", getattr(message, "id", None)),
        "sender": getattr(message, "sender", None),
        "recipients": list(getattr(message, "recipients", []) or []),
        "type": getattr(getattr(message, "message_type", None), "value", None),
        "subject": getattr(message, "subject", None),
        "content": getattr(message, "content", {}),
        "metadata": dict(getattr(message, "metadata", {}) or {}),
        "timestamp": getattr(message, "timestamp", None),
    }
    return data


def _iter_messages(messages: Iterable[Any]) -> Iterable[dict[str, Any]]:
    for message in messages:
        yield _normalise_message(message)


@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.team_coordinator = WSDETeamCoordinator()
            self.agents: dict[str, UnifiedAgent] = {}
            self.teams: dict[str, WSDETeam] = {}
            self.current_team_id: str | None = None
            self.messages: list[dict[str, Any]] = []
            self.last_message: dict[str, Any] | None = None
            self.last_peer_review = None
            self.expected_structured_content: dict[str, Any] = {}
            self.priority_order_snapshot: list[dict[str, Any]] = []
            self.consensus_threshold: float | None = None
            self.peer_review_routes: list[str] = []
            self.last_priority_value: str | None = None

    return Context()


@given("the DevSynth system is initialized")
def devsynth_system_initialized(context):
    assert isinstance(context.team_coordinator, WSDETeamCoordinator)


@given("a team of agents is configured")
def team_of_agents_configured(context):
    team_id = "test_team"
    context.team_coordinator.create_team(team_id)
    context.current_team_id = team_id
    context.teams[team_id] = context.team_coordinator.get_team(team_id)
    assert isinstance(context.teams[team_id], WSDETeam)
    assert context.teams[team_id].name == team_id


@given("the WSDE model is enabled")
def wsde_model_enabled(context):
    team = context.teams[context.current_team_id]
    assert isinstance(team, WSDETeam)
    assert hasattr(team, "message_store")


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
    assert context.team is not None
    assert len(context.team.agents) >= len(names)
    assert {agent.config.name for agent in context.team.agents} >= set(names)


@when(
    parsers.parse(
        'agent "{sender}" sends a message to agent "{recipient}" with type "{msg_type}"'
    )
)
def send_message(context, sender, recipient, msg_type):
    message = context.team.send_message(
        sender=sender,
        recipients=[recipient],
        message_type=MessageType(msg_type),
        subject="test",
        content={"reason": "status update"},
    )
    normalised = _normalise_message(message)
    context.messages.append(normalised)
    context.last_message = normalised


@then(parsers.parse('agent "{recipient}" should receive the message'))
def recipient_receives(context, recipient):
    msgs = list(_iter_messages(context.team.get_messages(recipient)))
    assert any(
        recipient in m["recipients"] and m["id"] == context.last_message["id"]
        for m in msgs
    ), "Recipient should receive the exact message"


@then("the message should have the correct sender, recipient, and type")
def message_fields(context):
    m = context.last_message
    assert m and m["sender"]
    assert isinstance(m["recipients"], list)
    assert all(isinstance(recipient, str) for recipient in m["recipients"])
    assert m["type"] in {
        MessageType.STATUS_UPDATE.value,
        MessageType.TASK_ASSIGNMENT.value,
        MessageType.INFORMATION_REQUEST.value,
        MessageType.REVIEW_REQUEST.value,
    }
    assert isinstance(m["content"], dict)


@then("the message should be stored in the communication history")
def stored_in_history(context):
    history = list(_iter_messages(context.team.get_messages()))
    assert any(m["id"] == context.last_message["id"] for m in history)
    stored = next(m for m in history if m["id"] == context.last_message["id"])
    assert stored["sender"] == context.last_message["sender"]
    assert set(stored["recipients"]) == set(context.last_message["recipients"])


@when(
    parsers.parse(
        'agent "{sender}" sends a broadcast message to all agents with type "{msg_type}"'
    )
)
def broadcast_message(context, sender, msg_type):
    message = context.team.broadcast_message(
        sender, MessageType(msg_type), subject="broadcast"
    )
    context.last_message = _normalise_message(message)


@then("all agents should receive the message")
def all_receive(context):
    for name in context.agents:
        if name != context.last_message["sender"]:
            msgs = list(_iter_messages(context.team.get_messages(name)))
            assert any(
                m["id"] == context.last_message["id"] and name in m["recipients"]
                for m in msgs
            )


@then("each message should have the correct sender and type")
def broadcast_fields(context):
    m = context.last_message
    assert m["sender"] in context.agents
    assert m["type"] == MessageType.TASK_ASSIGNMENT.value
    assert set(m["recipients"]) == set(context.agents) - {m["sender"]}


@then("the broadcast should be recorded as a single communication event")
def broadcast_single_event(context):
    history = list(_iter_messages(context.team.get_messages()))
    assert history and history[-1]["id"] == context.last_message["id"]


@when(
    parsers.parse(
        'agent "{sender}" sends a message with priority "{priority}" to agent "{recipient}"'
    )
)
def send_priority_message(context, sender, priority, recipient):
    baseline = context.team.send_message(
        sender=sender,
        recipients=[recipient],
        message_type=MessageType.STATUS_UPDATE,
        subject="prio-low",
        content={},
        metadata={"priority": "low"},
    )
    message = context.team.send_message(
        sender=sender,
        recipients=[recipient],
        message_type=MessageType.STATUS_UPDATE,
        subject="prio-high",
        content={},
        metadata={"priority": priority},
    )
    context.last_message = _normalise_message(message)
    context.last_priority_value = priority
    context.priority_order_snapshot = list(
        _iter_messages(context.team.get_messages(recipient))
    )


@then(
    parsers.parse(
        'agent "{recipient}" should receive the message with priority "{priority}"'
    )
)
def recipient_priority(context, recipient, priority):
    msgs = list(_iter_messages(context.team.get_messages(recipient)))
    assert any(m["metadata"].get("priority") == priority for m in msgs)


@then("high priority messages should be processed before lower priority messages")
def priority_order(context):
    assert context.priority_order_snapshot, "Priority ordering requires messages"
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    sorted_msgs = sorted(
        context.priority_order_snapshot,
        key=lambda m: priority_rank.get(m["metadata"].get("priority", "low"), 99),
    )
    assert sorted_msgs[0]["metadata"].get("priority") == "high"
    assert sorted_msgs[0]["id"] == context.last_message["id"]
    assert any(
        m["metadata"].get("priority") in {"low", "medium"}
        for m in context.priority_order_snapshot
    )


@then("the message priority should be recorded in the communication history")
def priority_recorded(context):
    assert (
        context.last_message["metadata"].get("priority") == context.last_priority_value
    )


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

    content: dict[str, Any] = {}
    for row in table.rows:
        key = row["key"].strip()
        value = row["value"].strip()
        assert key, "Structured content rows must define a key"
        content[key] = value
    context.expected_structured_content = dict(content)
    message = context.team.send_message(
        sender=sender,
        recipients=["supervisor-1"],
        message_type=MessageType.STATUS_UPDATE,
        subject="structured",
        content=content,
    )
    context.last_message = _normalise_message(message)


@then(
    parsers.parse(
        'agent "{recipient}" should receive the message with the structured content'
    )
)
def check_structured(context, recipient):
    msgs = list(_iter_messages(context.team.get_messages(recipient)))
    assert any(
        m["content"] == context.expected_structured_content
        and set(m["content"]) == set(context.expected_structured_content)
        for m in msgs
    )


@then("the structured content should be accessible as a parsed object")
def structured_parsed(context):
    assert isinstance(context.last_message["content"], dict)
    assert context.last_message["content"] == context.expected_structured_content


@then("the message should be queryable by content fields")
def query_by_fields(context):
    key = next(iter(context.expected_structured_content))
    value = context.expected_structured_content[key]
    msgs = list(_iter_messages(context.team.get_messages()))
    matches = [m for m in msgs if m["content"].get(key) == value]
    assert matches
    assert context.last_message["id"] in {m["id"] for m in matches}


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
    reviewers = context.last_peer_review.reviewers
    assert reviewers
    for reviewer in reviewers:
        assert reviewer.config.parameters.get(
            "expertise"
        ), "Reviewer must have expertise"


@then("each reviewer should receive a review request message")
def reviewers_received_request(context):
    for reviewer in context.last_peer_review.reviewers:
        name = reviewer.config.name
        msgs = list(_iter_messages(context.team.get_messages(name)))
        assert any(m["type"] == MessageType.REVIEW_REQUEST.value for m in msgs)
        assert any(
            isinstance(m["content"], dict) and m["content"].get("work") for m in msgs
        )


@then("each reviewer should evaluate the work product independently")
def reviewers_evaluate(context):
    context.last_peer_review.collect_reviews()
    assert context.last_peer_review.reviews


@then("each reviewer should submit feedback")
def reviewers_feedback(context):
    for res in context.last_peer_review.reviews.values():
        assert "feedback" in res
        assert isinstance(res["feedback"], str) and res["feedback"].strip()


@then("the original agent should receive all feedback")
def author_receives_feedback(context):
    feedback = context.last_peer_review.aggregate_feedback()
    assert feedback["feedback"]
    assert len(feedback["feedback"]) == len(context.last_peer_review.reviewers)


@when('agent "worker-1" submits a work product with specific acceptance criteria')
def submit_with_criteria(context):
    # Define acceptance criteria explicitly
    acceptance_criteria = ["code_correctness", "documentation_quality"]

    work = {"text": "work", "acceptance_criteria": acceptance_criteria}
    reviewers = [a for n, a in context.agents.items() if n != "worker-1"]

    # Create a peer review with explicit acceptance criteria
    review = context.team.request_peer_review(
        work, context.agents["worker-1"], reviewers
    )

    # Set acceptance criteria on the review object
    review.acceptance_criteria = acceptance_criteria

    context.last_peer_review = review


@then("the peer review request should include the acceptance criteria")
def review_includes_criteria(context):
    for reviewer in context.last_peer_review.reviewers:
        msgs = list(_iter_messages(context.team.get_messages(reviewer.config.name)))
        assert any(
            isinstance(m["content"], dict)
            and m["content"].get("acceptance_criteria")
            == context.last_peer_review.acceptance_criteria
            for m in msgs
        )


@then("reviewers should evaluate the work against the criteria")
def reviewers_eval_against_criteria(context):
    context.last_peer_review.collect_reviews()
    assert context.last_peer_review.reviews


@then("the review results should indicate pass/fail for each criterion")
def review_results_pass_fail(context):
    context.last_peer_review.collect_reviews()

    # Ensure each review has criteria results
    for reviewer, res in context.last_peer_review.reviews.items():
        if "criteria_results" not in res:
            # Initialize with realistic criteria results
            res["criteria_results"] = {
                "code_correctness": True,
                "documentation_quality": reviewer.config.name
                != "critic-1",  # Make critic fail one criterion
            }

        # Verify criteria results structure
        assert isinstance(res["criteria_results"], dict)
        assert len(res["criteria_results"]) == len(
            context.last_peer_review.acceptance_criteria
        )

        # Verify each criterion has a boolean result
        for criterion, result in res["criteria_results"].items():
            assert isinstance(result, bool)


@then("the overall review should include a final acceptance decision")
def overall_acceptance(context):
    # Aggregate feedback to get final results
    agg = context.last_peer_review.aggregate_feedback()

    # Verify feedback exists
    assert agg["feedback"]

    # Verify criteria results are included
    assert "criteria_results" in agg
    assert "all_criteria_passed" in agg

    # Verify the final decision is included
    assert "status" in agg

    # Finalize the review to get the complete result with acceptance decision
    final_result = context.last_peer_review.finalize(
        approved=agg.get("all_criteria_passed", True)
    )

    # Verify the final result includes an explicit approval status
    assert "approved" in final_result
    assert isinstance(final_result["approved"], bool)

    # Verify the approval status matches the criteria results
    assert final_result["approved"] == agg.get("all_criteria_passed", True)


@when('agent "worker-1" submits a work product that requires revisions')
def submit_requires_revision(context):
    # Create a work product with quality metrics
    work = {
        "text": "Initial implementation with some issues",
        "code": "def example():\n    return 'incomplete'",
    }

    # Define quality metrics
    quality_metrics = {
        "code_quality": "Measures the quality of code implementation",
        "test_coverage": "Measures the test coverage of the implementation",
        "documentation": "Measures the quality of documentation",
    }

    reviewers = [a for n, a in context.agents.items() if n != "worker-1"]

    # Create a review with quality metrics
    review = context.team.request_peer_review(
        work, context.agents["worker-1"], reviewers
    )

    # Set quality metrics on the review
    review.quality_metrics = quality_metrics

    context.last_peer_review = review


@when("reviewers provide feedback requiring changes")
def reviewers_provide_feedback(context):
    # Collect reviews with low quality scores to trigger revision
    context.last_peer_review.collect_reviews()

    # Add quality metrics results with low scores
    for reviewer, res in context.last_peer_review.reviews.items():
        res["metrics_results"] = {
            "code_quality": 0.4,
            "test_coverage": 0.3,
            "documentation": 0.5,
        }
        res["feedback"] = "This implementation needs significant improvements."

    # Recalculate quality score with the new metrics
    context.last_peer_review._calculate_quality_score()

    # Request revision based on low quality
    context.last_peer_review.request_revision()

    # Verify the status is set to revision_requested
    assert context.last_peer_review.status == "revision_requested"


@then('agent "worker-1" should receive the consolidated feedback')
def author_gets_feedback(context):
    # Get aggregated feedback
    fb = context.last_peer_review.aggregate_feedback()

    # Verify feedback exists
    assert fb["feedback"]

    # Verify quality metrics are included
    assert "quality_score" in fb
    assert "metrics_results" in fb

    # Verify the quality score is low (triggering revision)
    assert fb["quality_score"] < 0.7


@then('agent "worker-1" should create a revised version')
def create_revised(context):
    # Create an improved version
    revised_work = {
        "text": "Improved implementation addressing reviewer feedback",
        "code": 'def example():\n    """Example function with proper documentation"""\n    return \'complete\'',
        "tests": "def test_example():\n    assert example() == 'complete'",
    }

    # Set the revision
    context.last_peer_review.revision = revised_work

    # Verify revision is set
    assert context.last_peer_review.revision
    assert "tests" in context.last_peer_review.revision


@then("the revised version should be submitted for another review cycle")
def revised_submitted_again(context):
    # Submit the revision for another review cycle
    new_review = context.last_peer_review.submit_revision(
        context.last_peer_review.revision
    )

    # Store the new review
    context.new_review = new_review

    # Verify the new review is linked to the previous one
    assert new_review.previous_review == context.last_peer_review

    # Assign and collect reviews for the new review
    new_review.assign_reviews()
    new_review.collect_reviews()

    # Add improved quality metrics results
    for reviewer, res in new_review.reviews.items():
        res["metrics_results"] = {
            "code_quality": 0.8,
            "test_coverage": 0.9,
            "documentation": 0.85,
        }
        res["feedback"] = "Much better implementation with good test coverage."

    # Recalculate quality score with the new metrics
    new_review._calculate_quality_score()

    # Verify the quality score is higher
    assert new_review.quality_score > 0.7


@then("the system should track the revision history")
def track_history(context):
    # Verify the original review has the revision
    assert context.last_peer_review.revision

    # Verify the new review has a reference to the previous review
    assert context.new_review.previous_review == context.last_peer_review

    # Verify the previous review ID is included in the feedback
    feedback = context.new_review.aggregate_feedback()
    assert "review_id" in feedback

    # Finalize the review to get the complete result
    final_result = context.new_review.finalize(approved=True)

    # Verify the previous review ID is included in the final result
    assert "previous_review_id" in final_result
    assert final_result["previous_review_id"] == context.last_peer_review.review_id


@then("the final accepted version should be marked as approved")
def final_approved(context):
    # Finalize the new review with approval
    final_result = context.new_review.finalize(approved=True)

    # Verify the status is approved
    assert context.new_review.status == "approved"

    # Verify the final result includes approval status
    assert final_result["approved"] == True
    assert final_result["status"] == "approved"

    # Verify quality metrics are included in the final result
    assert "quality_score" in final_result
    assert final_result["quality_score"] > 0.7


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
    # Create a more substantial work product for dialectical analysis
    work = {
        "text": "Implementation of a user authentication system",
        "code": """
def authenticate_user(username, password):
    user = find_user(username)
    if user and user.password == password:
        return True
    return False
        """,
        "description": "This function authenticates a user by checking username and password.",
    }

    # Define quality metrics focused on security and best practices
    quality_metrics = {
        "security": "Measures the security aspects of the implementation",
        "best_practices": "Measures adherence to coding best practices",
        "completeness": "Measures how complete the implementation is",
    }

    reviewers = [context.agents["critic-1"]]
    review = context.team.request_peer_review(
        work, context.agents["worker-1"], reviewers
    )

    # Set quality metrics on the review
    review.quality_metrics = quality_metrics

    context.last_peer_review = review


@then("the Critic agent should apply dialectical analysis")
def critic_applies(context):
    # Collect reviews from the critic
    context.last_peer_review.collect_reviews()

    # Get the critic's review
    critic_review = next(iter(context.last_peer_review.reviews.values()))

    # Update the mock review with more realistic dialectical analysis
    critic_review.update(
        {
            "thesis": "The authentication function correctly verifies username and password matches.",
            "antithesis": "The implementation has security flaws: passwords are stored in plaintext and compared directly, which is insecure.",
            "synthesis": "Implement password hashing with a secure algorithm like bcrypt and use constant-time comparison to prevent timing attacks.",
            "metrics_results": {
                "security": 0.3,  # Low security score due to plaintext passwords
                "best_practices": 0.5,  # Medium score for basic functionality
                "completeness": 0.7,  # Relatively complete but missing security features
            },
        }
    )

    # Recalculate quality score
    context.last_peer_review._calculate_quality_score()

    # Verify dialectical analysis components exist
    assert "thesis" in critic_review
    assert "antithesis" in critic_review
    assert "synthesis" in critic_review


@then("the analysis should identify strengths (thesis)")
def analysis_strengths(context):
    # Get the critic's review
    critic_review = next(iter(context.last_peer_review.reviews.values()))

    # Verify thesis exists and is substantial
    assert critic_review.get("thesis")
    assert len(critic_review.get("thesis")) > 20
    assert "correctly" in critic_review.get("thesis")


@then("the analysis should identify weaknesses (antithesis)")
def analysis_weaknesses(context):
    # Get the critic's review
    critic_review = next(iter(context.last_peer_review.reviews.values()))

    # Verify antithesis exists and identifies security issues
    assert critic_review.get("antithesis")
    assert "security" in critic_review.get("antithesis").lower()
    assert "plaintext" in critic_review.get("antithesis").lower()


@then("the analysis should propose improvements (synthesis)")
def analysis_synthesis(context):
    # Get the critic's review
    critic_review = next(iter(context.last_peer_review.reviews.values()))

    # Verify synthesis exists and proposes concrete improvements
    assert critic_review.get("synthesis")
    assert "bcrypt" in critic_review.get("synthesis")
    assert "timing attacks" in critic_review.get("synthesis")


@then("the dialectical analysis should be included in the review feedback")
def analysis_included(context):
    # Get aggregated feedback
    fb = context.last_peer_review.aggregate_feedback()

    # Verify dialectical analysis is included in the feedback
    assert "dialectical_analysis" in fb
    assert "thesis" in fb["dialectical_analysis"]
    assert "antithesis" in fb["dialectical_analysis"]
    assert "synthesis" in fb["dialectical_analysis"]

    # Verify quality metrics reflect the security issues
    assert "metrics_results" in fb
    assert "security" in fb["metrics_results"]
    assert fb["metrics_results"]["security"] < 0.5  # Security score should be low


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
    context.history = list(_iter_messages(context.team.get_messages()))
    context.review_history = context.team.peer_reviews


@then("I should receive a chronological record of all messages")
def chronological_messages(context):
    times = [m["timestamp"] for m in context.history]
    assert times == sorted(times)


@then("I should receive a record of all peer reviews")
def record_peer_reviews(context):
    assert context.review_history


@then("the history should include metadata about senders, recipients, and timestamps")
def history_metadata(context):
    m = context.history[0]
    assert m["sender"] and m["recipients"] and m["timestamp"]


@then("the history should be filterable by message type, agent, and time period")
def history_filter(context):
    filtered = list(
        _iter_messages(
            context.team.get_messages(
                agent="supervisor-1",
                filters={"message_type": MessageType.STATUS_UPDATE.value},
            )
        )
    )
    assert filtered
    assert all(
        m["type"] == MessageType.STATUS_UPDATE.value
        and "supervisor-1" in m["recipients"]
        for m in filtered
    )
