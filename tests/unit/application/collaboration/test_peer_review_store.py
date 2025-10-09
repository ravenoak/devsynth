import sys
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest


class _StubPasswordHasher:
    def __init__(self, *args, **kwargs):  # type: ignore[override]
        pass

    def hash(self, value):  # type: ignore[override]
        return "hash"

    def verify(self, hashed, value):  # type: ignore[override]
        return True

    def check_needs_rehash(self, hashed):  # type: ignore[override]
        return False


_argon2_stub = SimpleNamespace(
    PasswordHasher=_StubPasswordHasher,
    exceptions=SimpleNamespace(VerifyMismatchError=RuntimeError),
)
sys.modules.setdefault("argon2", _argon2_stub)
sys.modules.setdefault("argon2.exceptions", _argon2_stub.exceptions)

_jsonschema_stub = SimpleNamespace(
    validate=lambda *args, **kwargs: None,
    exceptions=SimpleNamespace(ValidationError=RuntimeError, SchemaError=RuntimeError),
)
sys.modules.setdefault("jsonschema", _jsonschema_stub)
sys.modules.setdefault("jsonschema.exceptions", _jsonschema_stub.exceptions)

_toml_stub = SimpleNamespace(
    load=lambda *args, **kwargs: {}, dump=lambda *args, **kwargs: None
)
sys.modules.setdefault("toml", _toml_stub)

_yaml_stub = SimpleNamespace(
    safe_load=lambda *args, **kwargs: {}, dump=lambda *args, **kwargs: None
)
sys.modules.setdefault("yaml", _yaml_stub)


class _StubValidationError(Exception):
    """Minimal ValidationError replacement for tests."""


class _StubFieldValidationInfo:
    pass


def _stub_field(*args, default=None, **kwargs):
    return default


def _stub_field_validator(*args, **kwargs):
    def decorator(func):
        return func

    return decorator


_pydantic_stub = SimpleNamespace(
    ValidationError=_StubValidationError,
    Field=_stub_field,
    FieldValidationInfo=_StubFieldValidationInfo,
    field_validator=_stub_field_validator,
    dataclasses=SimpleNamespace(dataclass=dataclass),
)
sys.modules.setdefault("pydantic", _pydantic_stub)
sys.modules.setdefault("pydantic.dataclasses", _pydantic_stub.dataclasses)


class _StubBaseSettings:
    def __init__(self, *args, **kwargs):
        pass


_pydantic_settings_stub = SimpleNamespace(
    BaseSettings=_StubBaseSettings,
    SettingsConfigDict=dict,
)
sys.modules.setdefault("pydantic_settings", _pydantic_settings_stub)

_memory_manager_module = ModuleType("devsynth.application.memory.memory_manager")


class _StubMemoryManager:
    def __init__(self, *args, **kwargs):
        pass


_memory_manager_module.MemoryManager = _StubMemoryManager
sys.modules.setdefault(
    "devsynth.application.memory.memory_manager", _memory_manager_module
)
parent_memory_module = sys.modules.setdefault(
    "devsynth.application.memory", ModuleType("devsynth.application.memory")
)
setattr(parent_memory_module, "memory_manager", _memory_manager_module)

import pytest

from devsynth.application.collaboration.dto import (
    AgentOpinionRecord,
    ConsensusOutcome,
    PeerReviewRecord,
)
from devsynth.application.collaboration.exceptions import (
    ConsensusError as CollaborationConsensusError,
)
from devsynth.application.collaboration.exceptions import (
    PeerReviewConsensusError,
)
from devsynth.application.collaboration.peer_review import (
    PeerReview,
    ReviewDecision,
    _PeerReviewRecordStorage,
)
from devsynth.application.collaboration.structures import ReviewCycleSpec


class DummyMemoryManager:
    def __init__(self) -> None:
        self.adapters = {"tinydb": object()}
        self.flushed = False

    def flush_updates(self) -> None:
        self.flushed = True


@pytest.mark.fast
def test_store_in_memory_persists_peer_review_record() -> None:
    """ReqID: N/A"""

    mm = DummyMemoryManager()
    review = PeerReview(
        cycle=ReviewCycleSpec(
            work_product="wp",
            author="a",
            reviewers=["r"],
            memory_manager=mm,
        )
    )
    review.status = "approved"
    review.quality_score = 0.9
    review.reviews["r"] = ReviewDecision(
        decision_id="d-1",
        reviewer="r",
        approved=True,
        notes="solid",
        score=0.9,
        metadata={"criteria_results": {"accuracy": True}},
    )

    with patch(
        "devsynth.application.collaboration."
        "collaboration_memory_utils.store_with_retry",
        return_value="id123",
    ) as mock_store:
        item_id = review.store_in_memory()

    assert item_id == "id123"
    mock_store.assert_called_once()
    payload = mock_store.call_args.args[1]
    assert isinstance(payload, _PeerReviewRecordStorage)
    assert isinstance(payload.record, PeerReviewRecord)
    assert payload.record.metadata["review_id"] == review.review_id
    assert payload.to_dict()["record"]["metadata"]["review_id"] == review.review_id

    metadata = payload.memory_metadata()
    assert metadata["review_id"] == review.review_id
    assert metadata["quality_score"] == pytest.approx(review.quality_score)
    assert mm.flushed is True


@pytest.mark.fast
def test_collect_reviews_returns_review_decisions() -> None:
    """ReqID: N/A"""

    class FriendlyReviewer:
        name = "friendly"

        def process(self, payload):
            return {
                "feedback": "great job",
                "approved": True,
                "metrics_results": {"accuracy": 0.95},
            }

    mm = DummyMemoryManager()
    reviewer = FriendlyReviewer()
    review = PeerReview(
        cycle=ReviewCycleSpec(
            work_product={},
            author="author",
            reviewers=[reviewer],
            memory_manager=mm,
        )
    )

    with patch(
        "devsynth.application.collaboration."
        "collaboration_memory_utils.store_with_retry",
        return_value="stored",
    ):
        decisions = review.collect_reviews()

    assert all(isinstance(decision, ReviewDecision) for decision in decisions.values())
    decision = next(iter(decisions.values()))
    assert decision.notes == "great job"
    metrics = decision.metadata.get("metrics_results")
    assert isinstance(metrics, dict)
    assert metrics["accuracy"] == pytest.approx(0.95)


@pytest.mark.fast
def test_collect_reviews_failure_yields_error_decision() -> None:
    """ReqID: N/A"""

    class FailingReviewer:
        name = "failing"

        def process(self, payload):
            raise RuntimeError("boom")

    mm = DummyMemoryManager()
    review = PeerReview(
        cycle=ReviewCycleSpec(
            work_product={},
            author="author",
            reviewers=[FailingReviewer()],
            memory_manager=mm,
        )
    )

    with patch(
        "devsynth.application.collaboration."
        "collaboration_memory_utils.store_with_retry",
        return_value="stored",
    ):
        decisions = review.collect_reviews()

    decision = next(iter(decisions.values()))
    assert isinstance(decision, ReviewDecision)
    assert "Error processing review" in (decision.notes or "")
    assert decision.approved is None


@pytest.mark.fast
def test_collect_reviews_wraps_consensus_error_with_serialized_outcome() -> None:
    """ReqID: N/A"""

    class CooperativeReviewer:
        name = "cooperative"

        def process(self, payload):
            return {"feedback": "ok", "approved": True}

    mm = DummyMemoryManager()
    reviewer = CooperativeReviewer()
    review = PeerReview(
        cycle=ReviewCycleSpec(
            work_product={},
            author="author",
            reviewers=[reviewer],
            memory_manager=mm,
        )
    )

    consensus = ConsensusOutcome(
        consensus_id="cid-collect",
        task_id="tid",
        method="majority_opinion",
        agent_opinions=(AgentOpinionRecord(agent_id="alpha", opinion="approve"),),
        majority_opinion="approve",
    )

    class StubTeam:
        def add_solution(self, *_args, **_kwargs):
            return None

        def build_consensus(self, *_args, **_kwargs):
            error = CollaborationConsensusError("targeted failure")
            error.consensus_result = consensus.to_dict()
            raise error

    review.team = StubTeam()

    with (
        patch(
            "devsynth.application.collaboration.collaboration_memory_utils.store_with_retry",
            return_value="stored",
        ),
        patch(
            "devsynth.application.collaboration.peer_review.log_consensus_failure"
        ) as mock_log,
    ):
        review.collect_reviews()

    mock_log.assert_called_once()
    error = mock_log.call_args.args[1]
    assert isinstance(error, PeerReviewConsensusError)
    payload = error.as_dict()
    assert payload["consensus"]["dto_type"] == "ConsensusOutcome"
    assert payload["consensus"]["majority_opinion"] == "approve"
    assert payload["message"].endswith(f"[review_id={review.review_id}]")
    assert review.consensus_outcome is not None
    assert review.consensus_outcome.majority_opinion == "approve"
