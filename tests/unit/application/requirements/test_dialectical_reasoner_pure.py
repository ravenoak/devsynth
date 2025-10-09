"""Pure helper tests for the dialectical reasoner."""

from __future__ import annotations

from uuid import uuid4

import pytest

from devsynth.application.requirements.dialectical_reasoner import (
    DialecticalReasonerService,
)
from devsynth.domain.models.requirement import (
    Requirement,
    RequirementChange,
    RequirementPriority,
)

pytestmark = pytest.mark.fast


class _StubRequirementRepository:
    def __init__(self) -> None:
        self.requirements: list[Requirement] = []
        self.lookup: dict = {}

    def get_all_requirements(self) -> list[Requirement]:
        return list(self.requirements)

    def get_requirement(self, req_id):  # noqa: ANN001 - interface compatibility
        return self.lookup.get(req_id)


def _service_with_repo(repo: _StubRequirementRepository) -> DialecticalReasonerService:
    service = object.__new__(DialecticalReasonerService)
    service.requirement_repository = repo
    return service


def test_identify_affected_requirements_collects_dependencies() -> None:
    """Dependent requirement identifiers are returned in sorted order.

    ReqID: N/A
    """

    repo = _StubRequirementRepository()
    changed_id = uuid4()
    dependent_a = Requirement(id=uuid4(), dependencies=[changed_id])
    dependent_b = Requirement(id=uuid4(), dependencies=[uuid4(), changed_id])
    repo.requirements = [dependent_b, dependent_a]

    change = RequirementChange(requirement_id=changed_id)
    service = _service_with_repo(repo)

    affected = service._identify_affected_requirements(change)

    assert affected == sorted([changed_id, dependent_a.id, dependent_b.id], key=str)


def test_identify_affected_components_merges_sources() -> None:
    """Components from existing and new requirement states are merged uniquely.

    ReqID: N/A
    """

    repo = _StubRequirementRepository()
    changed_id = uuid4()
    repo.lookup[changed_id] = Requirement(
        id=changed_id,
        priority=RequirementPriority.MEDIUM,
        metadata={"component": "api"},
    )

    new_state = Requirement(metadata={"component": "database"})
    change = RequirementChange(requirement_id=changed_id, new_state=new_state)
    service = _service_with_repo(repo)

    components = service._identify_affected_components(change)

    assert components == ["api", "database"]


def test_assess_risk_level_accounts_for_priority() -> None:
    """Risk assessment responds to both priority and blast radius.

    ReqID: N/A
    """

    repo = _StubRequirementRepository()
    changed_id = uuid4()
    high_req = Requirement(
        id=changed_id,
        priority=RequirementPriority.CRITICAL,
    )
    repo.lookup[changed_id] = high_req
    service = _service_with_repo(repo)

    change = RequirementChange(requirement_id=changed_id)
    affected = [uuid4() for _ in range(4)]
    assert service._assess_risk_level(change, affected) == "critical"

    repo.lookup[changed_id] = Requirement(
        id=changed_id,
        priority=RequirementPriority.MEDIUM,
    )
    medium_span = [uuid4() for _ in range(3)]
    assert service._assess_risk_level(change, medium_span) == "medium"
    assert service._assess_risk_level(change, []) == "low"


def test_estimate_effort_scales_with_affected_entities() -> None:
    """Effort estimation is additive across requirements and components.

    ReqID: N/A
    """

    service = _service_with_repo(_StubRequirementRepository())
    change = RequirementChange(requirement_id=uuid4())

    assert service._estimate_effort(change, [], []) == "low"
    assert (
        service._estimate_effort(
            change,
            [uuid4(), uuid4(), uuid4()],
            ["api"],
        )
        == "medium"
    )
    assert (
        service._estimate_effort(
            change,
            [uuid4() for _ in range(5)],
            ["api", "db", "ui", "worker"],
        )
        == "very high"
    )
