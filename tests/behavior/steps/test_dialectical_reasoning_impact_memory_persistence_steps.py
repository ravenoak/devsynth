from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pytest_bdd import given, parsers, then, when

from devsynth.application.requirements.dialectical_reasoner import (
    DialecticalReasonerService,
)
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
)


class DummyMemoryManager:
    """In-memory store that can simulate failures."""

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = []

    def store_with_edrr_phase(self, item, memory_type, edrr_phase, metadata):
        if self.fail:
            raise RuntimeError("store failure")
        self.calls.append((item, memory_type, edrr_phase, metadata))
        return uuid4()


@pytest.fixture
def context():
    class Context:
        pass

    return Context()


def _build_reasoner(memory_manager):
    reasoning_repo = MagicMock()
    reasoning_repo.get_reasoning_for_change.return_value = None
    reasoning_repo.save_reasoning.side_effect = lambda r: r

    impact_repo = MagicMock()
    impact_repo.get_impact_assessment_for_change.return_value = None
    impact_repo.save_impact_assessment.side_effect = lambda a: a

    reasoner = DialecticalReasonerService(
        requirement_repository=MagicMock(),
        reasoning_repository=reasoning_repo,
        impact_repository=impact_repo,
        chat_repository=MagicMock(),
        notification_service=MagicMock(),
        llm_service=MagicMock(),
        memory_manager=memory_manager,
    )

    # Stub methods to avoid LLM calls
    reasoner._identify_affected_requirements = MagicMock(return_value=[])
    reasoner._identify_affected_components = MagicMock(return_value=[])
    reasoner._assess_risk_level = MagicMock(return_value="low")
    reasoner._estimate_effort = MagicMock(return_value="low")
    reasoner._generate_impact_analysis = MagicMock(return_value="analysis")
    reasoner._generate_impact_recommendations = MagicMock(return_value=["rec"])

    return reasoner, impact_repo


@pytest.mark.fast
@given("a dialectical reasoner with memory")
def reasoner_with_memory(context):
    memory_manager = DummyMemoryManager()
    context.reasoner, context.impact_repo = _build_reasoner(memory_manager)
    context.memory_manager = memory_manager


@pytest.mark.fast
@given("a dialectical reasoner with failing memory")
def reasoner_with_failing_memory(context):
    memory_manager = DummyMemoryManager(fail=True)
    context.reasoner, context.impact_repo = _build_reasoner(memory_manager)
    context.memory_manager = memory_manager


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
@when("the change impact is assessed")
def assess_change(context):
    context.assessment = context.reasoner.assess_impact(context.change)


@pytest.mark.fast
@then(
    parsers.parse(
        'the impact assessment should be stored in memory with phase "{phase}"'
    )
)
def assessment_stored_with_phase(context, phase):
    assert context.memory_manager.calls, "No impact stored"
    item, memory_type, edrr_phase, metadata = context.memory_manager.calls[-1]
    assert edrr_phase == phase
    assert memory_type == MemoryType.DOCUMENTATION
    assert metadata["change_id"] == str(context.change.id)


@pytest.mark.fast
@then("the impact assessment completes")
def assessment_completes(context):
    assert context.assessment is not None


@pytest.mark.fast
@then("a memory persistence warning is logged")
def memory_warning_logged(caplog):
    assert any(
        "Failed to persist impact assessment" in record.getMessage()
        for record in caplog.records
    )
