"""Typed helpers wrapping the legacy dialectical reasoning workflow."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime
from typing import Any
from uuid import uuid4

from devsynth.logging_setup import DevSynthLogger

from . import wsde_dialectical as _legacy

logger = DevSynthLogger(__name__)


class DialecticalTask(Mapping[str, Any]):
    """Structured representation of a task entering the dialectical loop."""

    __slots__ = ("identifier", "solution", "metadata", "_payload")

    def __init__(
        self,
        *,
        identifier: str,
        solution: Any,
        payload: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.identifier = identifier
        self.solution = solution
        self.metadata = dict(metadata or {})
        base_payload = dict(payload or {})
        base_payload.setdefault("id", identifier)
        base_payload["solution"] = solution
        self._payload: dict[str, Any] = base_payload

    def __getitem__(self, key: str) -> Any:
        return self._payload[key]

    def __iter__(self) -> Iterator[str]:  # pragma: no cover - trivial
        return iter(self._payload)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._payload)

    def copy(self) -> dict[str, Any]:
        return dict(self._payload)

    def get(self, key: str, default: Any = None) -> Any:  # pragma: no cover - trivial
        return self._payload.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return self.copy()

    def with_solution(self, solution: Any) -> DialecticalTask:
        payload = dict(self._payload)
        payload["solution"] = solution
        return DialecticalTask(
            identifier=self.identifier,
            solution=solution,
            payload=payload,
            metadata=self.metadata,
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> DialecticalTask:
        identifier = str(payload.get("id", uuid4()))
        solution = payload.get("solution")
        metadata = payload.get("metadata", {})
        return cls(
            identifier=identifier,
            solution=solution,
            payload=payload,
            metadata=metadata,
        )


def ensure_dialectical_task(
    task: DialecticalTask | Mapping[str, Any],
) -> DialecticalTask:
    if isinstance(task, DialecticalTask):
        return task
    if isinstance(task, Mapping):
        return DialecticalTask.from_mapping(task)
    msg = f"Unsupported task payload type: {type(task)!r}"
    raise TypeError(msg)


def apply_dialectical_reasoning(
    self: _legacy.WSDETeam,
    task: DialecticalTask | Mapping[str, Any],
    critic_agent: Any,
    memory_integration: Any = None,
) -> _legacy.DialecticalSequence:
    """Typed façade around the legacy dialectical reasoning implementation."""

    task_obj = ensure_dialectical_task(task)
    if task_obj.solution is None:
        logger.warning("Cannot apply dialectical reasoning: no solution provided")
        return _legacy.DialecticalSequence.failed(reason="no_solution")

    if isinstance(task_obj.solution, Mapping):
        thesis_payload = dict(task_obj.solution)
    else:
        thesis_payload = {"content": task_obj.solution}

    antithesis = self._generate_antithesis(thesis_payload, critic_agent)

    critic_id = antithesis.critic_id
    critique_messages = list(antithesis.critiques)
    domain_mapping = self._categorize_critiques_by_domain(critique_messages)
    message_domains = _legacy._invert_domain_mapping(domain_mapping)

    critiques: list[_legacy.Critique] = []
    for ordinal, message in enumerate(critique_messages):
        critiques.append(
            _legacy.Critique.from_message(
                reviewer_id=critic_id,
                ordinal=ordinal,
                message=message,
                domains=message_domains.get(message, ()),
                metadata={"antithesis_id": antithesis.identifier},
            )
        )

    resolution = self._generate_synthesis(
        thesis_payload,
        antithesis,
        tuple(critiques),
        domain_mapping,
    )

    step = _legacy.DialecticalStep(
        step_id=str(uuid4()),
        timestamp=datetime.now(),
        task_id=task_obj.identifier,
        thesis=thesis_payload,
        critiques=tuple(critiques),
        resolution=resolution,
        critic_id=critic_id,
        antithesis_id=antithesis.identifier,
        antithesis_generated_at=antithesis.timestamp,
        improvement_suggestions=antithesis.improvement_suggestions,
        alternative_approaches=antithesis.alternative_approaches,
    )

    sequence = _legacy.DialecticalSequence(
        sequence_id=str(uuid4()),
        steps=(step,),
    )

    for hook in self.dialectical_hooks:
        hook(task_obj, (sequence,))

    if memory_integration:
        memory_integration.store_dialectical_result(task_obj, sequence)

    return sequence


_legacy.WSDETeam.apply_dialectical_reasoning = apply_dialectical_reasoning
