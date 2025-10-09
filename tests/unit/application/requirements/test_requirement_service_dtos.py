import sys
import uuid
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

if "devsynth.ports.requirement_port" not in sys.modules:
    requirement_port_stub = ModuleType("devsynth.ports.requirement_port")

    class RequirementRepositoryPort:  # pragma: no cover - test stub
        ...

    class ChangeRepositoryPort:  # pragma: no cover - test stub
        ...

    class DialecticalReasonerPort:  # pragma: no cover - test stub
        ...

    class NotificationPort:  # pragma: no cover - test stub
        ...

    requirement_port_stub.RequirementRepositoryPort = RequirementRepositoryPort
    requirement_port_stub.ChangeRepositoryPort = ChangeRepositoryPort
    requirement_port_stub.DialecticalReasonerPort = DialecticalReasonerPort
    requirement_port_stub.NotificationPort = NotificationPort
    sys.modules["devsynth.ports.requirement_port"] = requirement_port_stub

ROOT = Path(__file__).resolve().parents[4]

models_spec = spec_from_file_location(
    "devsynth.application.requirements.models",
    ROOT / "src/devsynth/application/requirements/models.py",
)
requirement_models = module_from_spec(models_spec)
assert models_spec.loader is not None
sys.modules[models_spec.name] = requirement_models
models_spec.loader.exec_module(requirement_models)

ChangeNotificationPayload = requirement_models.ChangeNotificationPayload
ChangeNotificationEvent = requirement_models.ChangeNotificationEvent
EDRRPhase = requirement_models.EDRRPhase
RequirementUpdateDTO = requirement_models.RequirementUpdateDTO

service_spec = spec_from_file_location(
    "devsynth.application.requirements.requirement_service",
    ROOT / "src/devsynth/application/requirements/requirement_service.py",
)
requirement_service_module = module_from_spec(service_spec)
assert service_spec.loader is not None
sys.modules[service_spec.name] = requirement_service_module
service_spec.loader.exec_module(requirement_service_module)
RequirementService = requirement_service_module.RequirementService
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)


@pytest.fixture
def requirement() -> Requirement:
    """Build a canonical requirement for update/delete scenarios."""

    return Requirement(
        id=uuid.uuid4(),
        title="Original",
        description="Initial description",
        status=RequirementStatus.DRAFT,
        priority=RequirementPriority.MEDIUM,
        type=RequirementType.FUNCTIONAL,
        created_by="author",
        dependencies=[],
        tags=["initial"],
        metadata={"key": "value"},
    )


@pytest.fixture
def service(requirement: Requirement) -> RequirementService:
    """Construct a requirement service with mocked ports."""

    requirement_repo = MagicMock()
    requirement_repo.get_requirement.return_value = requirement
    requirement_repo.save_requirement.side_effect = lambda req: req
    requirement_repo.delete_requirement.return_value = True

    change_repo = MagicMock()
    change_repo.save_change.side_effect = lambda change: change

    dialectical = MagicMock()
    notifier = MagicMock()

    return RequirementService(
        requirement_repository=requirement_repo,
        change_repository=change_repo,
        dialectical_reasoner=dialectical,
        notification_service=notifier,
    )


@pytest.mark.fast
def test_update_requirement_uses_typed_dto_and_dialectical_hooks(
    service: RequirementService,
    requirement: Requirement,
):
    """Requirement updates emit typed payloads and dialectical metadata."""

    updates = RequirementUpdateDTO(
        title="Updated",
        description="Refined description",
        priority=RequirementPriority.HIGH,
        tags=("initial", "refined"),
    )

    updated = service.update_requirement(
        requirement_id=requirement.id,
        updates=updates,
        user_id="reviewer",
        reason="Refinement",
    )

    assert isinstance(updated, Requirement)
    assert updated.title == "Updated"
    assert updated.description == "Refined description"
    assert updated.priority is RequirementPriority.HIGH
    assert updated.tags == ["initial", "refined"]

    service.dialectical_reasoner.evaluate_change.assert_called_once()
    service.dialectical_reasoner.assess_impact.assert_called_once()

    eval_args, eval_kwargs = service.dialectical_reasoner.evaluate_change.call_args
    change_arg: RequirementChange = eval_args[0]
    assert isinstance(change_arg, RequirementChange)
    assert change_arg.change_type is ChangeType.MODIFY
    assert change_arg.previous_state.title == "Original"
    assert change_arg.new_state.title == "Updated"
    assert eval_kwargs["edrr_phase"] is EDRRPhase.REFINE

    assess_kwargs = service.dialectical_reasoner.assess_impact.call_args.kwargs
    assert assess_kwargs["edrr_phase"] is EDRRPhase.REFINE

    service.notification_service.notify_change_proposed.assert_called_once()
    payload_arg: ChangeNotificationPayload = (
        service.notification_service.notify_change_proposed.call_args.args[0]
    )
    assert isinstance(payload_arg, ChangeNotificationPayload)
    assert payload_arg.event is ChangeNotificationEvent.PROPOSED
    assert payload_arg.audit.edrr_phase is EDRRPhase.REFINE
    assert payload_arg.audit.actor_id == "reviewer"


@pytest.mark.fast
def test_delete_requirement_emits_retrospect_phase(
    service: RequirementService, requirement: Requirement
):
    """Deleting a requirement notifies dialectical consumers with RETROSPECT phase."""

    deleted = service.delete_requirement(
        requirement_id=requirement.id,
        user_id="reviewer",
        reason="Obsolete",
    )

    assert deleted is True

    service.change_repository.save_change.assert_called_once()
    saved_change: RequirementChange = (
        service.change_repository.save_change.call_args.args[0]
    )
    assert saved_change.change_type is ChangeType.REMOVE
    assert saved_change.previous_state is requirement

    service.dialectical_reasoner.evaluate_change.assert_called_once()
    eval_kwargs = service.dialectical_reasoner.evaluate_change.call_args.kwargs
    assert eval_kwargs["edrr_phase"] is EDRRPhase.RETROSPECT

    service.dialectical_reasoner.assess_impact.assert_called_once()
    assess_kwargs = service.dialectical_reasoner.assess_impact.call_args.kwargs
    assert assess_kwargs["edrr_phase"] is EDRRPhase.RETROSPECT

    service.notification_service.notify_change_proposed.assert_called_once()
    payload_arg: ChangeNotificationPayload = (
        service.notification_service.notify_change_proposed.call_args.args[0]
    )
    assert isinstance(payload_arg, ChangeNotificationPayload)
    assert payload_arg.event is ChangeNotificationEvent.PROPOSED
    assert payload_arg.audit.edrr_phase is EDRRPhase.RETROSPECT
    assert payload_arg.audit.change.change_type is ChangeType.REMOVE
