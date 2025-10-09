from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.requirements.dialectical_reasoner import (
    DialecticalReasonerService,
)
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
)
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Load the feature file
scenarios(feature_path(__file__, "general", "requirement_to_edrr_link.feature"))


class DummyMemoryManager:
    """Simple in-memory recorder for memory operations."""

    def __init__(self):
        self.calls = []

    def store_with_edrr_phase(self, item, memory_type, edrr_phase, metadata):
        self.calls.append((item, memory_type, edrr_phase, metadata))
        return str(uuid4())


@pytest.fixture
def context():
    class Context:
        pass

    return Context()


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

    # Stub generation paths to avoid external calls
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


@given(parsers.parse('a requirement change of type "{change_type}"'))
def requirement_change(context, change_type: str):
    req = Requirement(title="Test", description="Desc", created_by="user")
    ctype = getattr(ChangeType, change_type.upper())
    context.change = RequirementChange(
        requirement_id=req.id,
        change_type=ctype,
        new_state=req if ctype != ChangeType.REMOVE else None,
        reason="test",
        created_by="user",
    )


@when("the change is evaluated")
def evaluate_change(context):
    context.reasoning = context.reasoner.evaluate_change(context.change)


@then(
    parsers.parse(
        'a requirement-to-reasoning relationship should be stored in memory with phase "{phase}"'
    )
)
def relationship_stored_with_phase(context, phase):
    # Find the RELATIONSHIP store call
    calls = [c for c in context.memory_manager.calls if c[1] == MemoryType.RELATIONSHIP]
    assert calls, "No RELATIONSHIP memory item stored"
    item, memory_type, edrr_phase, metadata = calls[-1]
    assert edrr_phase == phase
    assert item.get("type") == "requirement_to_reasoning"
    assert item.get("change_id") == str(context.change.id)
    assert item.get("reasoning_id") == str(context.reasoning.id)
    assert metadata["change_id"] == str(context.change.id)
    assert metadata.get("link") == "requirement->reasoning"
