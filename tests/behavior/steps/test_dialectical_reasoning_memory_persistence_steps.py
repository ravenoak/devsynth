from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pytest_bdd import given, parsers, then, when

from devsynth.application.requirements.dialectical_reasoner import (
    ConsensusError,
    DialecticalReasonerService,
)
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
)


class DummyMemoryManager:
    """Simple in-memory store for reasoning results."""

    def __init__(self):
        self.calls = []

    def store_with_edrr_phase(self, item, memory_type, edrr_phase, metadata):
        self.calls.append((item, memory_type, edrr_phase, metadata))
        return uuid4()


@pytest.fixture
def context():
    class Context:
        pass

    return Context()


@pytest.mark.fast
@given("a dialectical reasoner with memory")
def reasoner_with_memory(context):
    memory_manager = DummyMemoryManager()
    reasoning_repo = MagicMock()
    reasoning_repo.get_reasoning_for_change.return_value = None
    reasoning_repo.save_reasoning.side_effect = lambda r: r

    llm_service = MagicMock()
    llm_service.query.return_value = "yes"

    reasoner = DialecticalReasonerService(
        requirement_repository=MagicMock(),
        reasoning_repository=reasoning_repo,
        impact_repository=MagicMock(),
        chat_repository=MagicMock(),
        notification_service=MagicMock(),
        llm_service=llm_service,
        memory_manager=memory_manager,
    )

    # Stub generation methods to avoid LLM calls
    reasoner._generate_thesis = MagicMock(return_value="thesis")
    reasoner._generate_antithesis = MagicMock(return_value="antithesis")
    reasoner._generate_arguments = MagicMock(
        return_value=[{"position": "pro", "content": "arg"}]
    )
    reasoner._generate_synthesis = MagicMock(return_value="synthesis")
    reasoner._generate_conclusion_and_recommendation = MagicMock(
        return_value=("conclusion", "recommendation")
    )

    context.reasoner = reasoner
    context.memory_manager = memory_manager
    context.reasoning_repo = reasoning_repo


@pytest.mark.fast
@given("a requirement change")
def requirement_change(context):
    req = Requirement(title="Test", description="Desc", created_by="user")
    context.change = RequirementChange(
        requirement_id=req.id,
        change_type=ChangeType.ADD,
        new_state=req,
        reason="new feature",
        created_by="user",
    )


@pytest.mark.fast
@when("the change is evaluated")
def evaluate_change(context):
    context.reasoning = context.reasoner.evaluate_change(context.change)


@pytest.mark.fast
@when("the change is evaluated with invalid consensus output")
def evaluate_change_invalid(context):
    context.reasoner.llm_service.query.return_value = "maybe"
    with pytest.raises(ConsensusError) as err:
        context.reasoner.evaluate_change(context.change)
    context.consensus_error = err.value


@pytest.mark.fast
@then(
    parsers.parse(
        'the reasoning result should be stored in memory with phase "{phase}"'
    )
)
def reasoning_stored_with_phase(context, phase):
    assert context.memory_manager.calls, "No reasoning stored"
    item, memory_type, edrr_phase, metadata = context.memory_manager.calls[-1]
    assert edrr_phase == phase
    assert memory_type == MemoryType.DIALECTICAL_REASONING
    assert metadata["change_id"] == str(context.change.id)


@pytest.mark.fast
@then("a consensus error is raised")
def consensus_error_raised(context):
    assert isinstance(context.consensus_error, ConsensusError)
