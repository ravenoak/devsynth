"""Tests for dialectical reasoner parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from collections.abc import Iterable
from uuid import UUID, uuid4

import pytest

from devsynth.application.requirements.dialectical_reasoner import (
    ConsensusError,
    DialecticalReasonerService,
)
from devsynth.application.requirements.models import EDRRPhase
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.requirement import (
    ChangeType,
    DialecticalReasoning,
    ImpactAssessment,
    Requirement,
    RequirementChange,
)

pytestmark = pytest.mark.fast


class _SequencedLLM:
    def __init__(self, responses: Iterable[str]) -> None:
        self._responses = iter(responses)

    def query(self, prompt: str) -> str:  # noqa: ANN001 - interface compatibility
        try:
            return next(self._responses)
        except StopIteration:  # pragma: no cover - defensive guard in tests
            raise AssertionError("Unexpected LLM query")


class _RequirementRepositoryStub:
    def __init__(self) -> None:
        self.requirements: dict[UUID, Requirement] = {}
        self.changes: dict[UUID, RequirementChange] = {}

    def get_all_requirements(self) -> list[Requirement]:
        return list(self.requirements.values())

    def get_requirement(self, requirement_id: UUID) -> Requirement | None:
        return self.requirements.get(requirement_id)

    def get_change(self, change_id: UUID) -> RequirementChange | None:
        return self.changes.get(change_id)


class _ReasoningRepositoryStub:
    def __init__(self) -> None:
        self.saved_reasoning: DialecticalReasoning | None = None

    def get_reasoning_for_change(self, change_id: UUID) -> DialecticalReasoning | None:
        return None

    def save_reasoning(self, reasoning: DialecticalReasoning) -> DialecticalReasoning:
        self.saved_reasoning = reasoning
        return reasoning

    def get_reasoning(self, reasoning_id: UUID) -> DialecticalReasoning | None:
        return None


class _ImpactRepositoryStub:
    def __init__(self) -> None:
        self.saved_assessment: ImpactAssessment | None = None

    def get_impact_assessment_for_change(
        self, change_id: UUID
    ) -> ImpactAssessment | None:
        return None

    def save_impact_assessment(self, assessment: ImpactAssessment) -> ImpactAssessment:
        self.saved_assessment = assessment
        return assessment


class _ChatRepositoryStub:
    def get_session(self, session_id: UUID):  # noqa: ANN001 - interface compatibility
        raise AssertionError("Chat repository should not be invoked in parsing tests")

    def save_message(self, message):  # noqa: ANN001 - interface compatibility
        raise AssertionError("Chat repository should not be invoked in parsing tests")

    def save_session(self, session):  # noqa: ANN001 - interface compatibility
        raise AssertionError("Chat repository should not be invoked in parsing tests")


class _NotificationStub:
    def __init__(self) -> None:
        self.last_payload = None

    def notify_change_proposed(self, payload):  # noqa: ANN001
        raise AssertionError("Change notifications are out of scope for parsing tests")

    def notify_change_approved(self, payload):  # noqa: ANN001
        raise AssertionError("Change notifications are out of scope for parsing tests")

    def notify_change_rejected(self, payload):  # noqa: ANN001
        raise AssertionError("Change notifications are out of scope for parsing tests")

    def notify_impact_assessment_completed(self, payload):  # noqa: ANN001
        self.last_payload = payload


@dataclass
class _MemoryRecord:
    payload: object
    memory_type: MemoryType
    edrr_phase: str


class _MemoryManagerStub:
    def __init__(self) -> None:
        self.records: list[_MemoryRecord] = []

    def store_with_edrr_phase(  # noqa: ANN001 - interface compatibility
        self,
        payload,
        *,
        memory_type,
        edrr_phase,
        metadata,
    ) -> None:
        self.records.append(
            _MemoryRecord(
                payload=payload, memory_type=memory_type, edrr_phase=edrr_phase
            )
        )


class _AssessmentNotificationGuard(_NotificationStub):
    def notify_impact_assessment_completed(self, payload):  # noqa: ANN001
        super().notify_impact_assessment_completed(payload)


def _build_reasoner(
    *,
    llm: _SequencedLLM,
    requirement_repo: _RequirementRepositoryStub,
    reasoning_repo: _ReasoningRepositoryStub,
    impact_repo: _ImpactRepositoryStub,
    memory_manager: _MemoryManagerStub,
    notification: _NotificationStub | None = None,
) -> DialecticalReasonerService:
    return DialecticalReasonerService(
        requirement_repository=requirement_repo,
        reasoning_repository=reasoning_repo,
        impact_repository=impact_repo,
        chat_repository=_ChatRepositoryStub(),
        notification_service=notification or _NotificationStub(),
        llm_service=llm,
        memory_manager=memory_manager,
    )


def test_argument_parsing_consensus_failure_payload_preserved() -> None:
    """Argument parsing remains deterministic even when consensus fails."""

    requirement_repo = _RequirementRepositoryStub()
    reasoning_repo = _ReasoningRepositoryStub()
    impact_repo = _ImpactRepositoryStub()
    memory_manager = _MemoryManagerStub()
    llm = _SequencedLLM(
        [
            "Support the change",  # thesis
            "Oppose the change",  # antithesis
            (
                "Argument 1:\n"
                "Position: Thesis\n"
                "Content: Improve reliability\n"
                "Counterargument: Hard to implement\n\n"
                "Argument 2:\n"
                "Position: Antithesis\n"
                "Content: Too costly\n"
                "Counterargument: Gains justify cost\n"
            ),
            "Balanced view",  # synthesis
            "Conclusion: Proceed\n\nRecommendation: Approve",  # conclusion/recommendation
            "no",  # consensus rejection
        ]
    )
    service = _build_reasoner(
        llm=llm,
        requirement_repo=requirement_repo,
        reasoning_repo=reasoning_repo,
        impact_repo=impact_repo,
        memory_manager=memory_manager,
    )

    change = RequirementChange(
        id=uuid4(),
        change_type=ChangeType.MODIFY,
        previous_state=Requirement(title="Old", description="Old desc"),
        new_state=Requirement(title="New", description="New desc"),
        reason="Reliability improvements",
        created_by="analyst",
    )

    with pytest.raises(ConsensusError):
        service.evaluate_change(change, edrr_phase=EDRRPhase.REFINE)

    argument_records = [
        record
        for record in memory_manager.records
        if record.memory_type is MemoryType.DIALECTICAL_REASONING
    ]
    assert len(argument_records) == 1
    saved_arguments = argument_records[0].payload["arguments"]
    assert saved_arguments == [
        {
            "position": "Thesis",
            "content": "Improve reliability",
            "counterargument": "Hard to implement",
        },
        {
            "position": "Antithesis",
            "content": "Too costly",
            "counterargument": "Gains justify cost",
        },
    ]


def test_assess_impact_recommendations_payload_preserved() -> None:
    """Impact assessment recommendations remain serialized as plain strings."""

    requirement_repo = _RequirementRepositoryStub()
    reasoning_repo = _ReasoningRepositoryStub()
    impact_repo = _ImpactRepositoryStub()
    memory_manager = _MemoryManagerStub()
    notification = _AssessmentNotificationGuard()
    llm = _SequencedLLM(
        [
            "Comprehensive analysis",  # impact analysis
            "- Roll out gradually\n- Update documentation",  # recommendations
        ]
    )
    service = _build_reasoner(
        llm=llm,
        requirement_repo=requirement_repo,
        reasoning_repo=reasoning_repo,
        impact_repo=impact_repo,
        memory_manager=memory_manager,
        notification=notification,
    )

    requirement_id = uuid4()
    baseline_requirement = Requirement(
        id=requirement_id,
        title="Existing",
        description="Existing description",
        metadata={"component": "api"},
    )
    requirement_repo.requirements[requirement_id] = baseline_requirement

    change = RequirementChange(
        id=uuid4(),
        requirement_id=requirement_id,
        change_type=ChangeType.MODIFY,
        previous_state=baseline_requirement,
        new_state=Requirement(
            id=requirement_id,
            title="Existing",
            description="Updated description",
            metadata={"component": "database"},
        ),
        reason="Data durability",
        created_by="analyst",
    )

    assessment = service.assess_impact(change, edrr_phase=EDRRPhase.REFINE)

    expected = ["Roll out gradually", "Update documentation"]
    assert assessment.recommendations == expected
    assert impact_repo.saved_assessment is assessment
    assert notification.last_payload is not None
    assert notification.last_payload.assessment.recommendations == expected
