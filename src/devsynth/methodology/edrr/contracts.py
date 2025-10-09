"""Shared protocols and helper dataclasses for EDRR orchestration."""

from __future__ import annotations

"""Typed contracts shared across EDRR orchestration components."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.domain.models.wsde_dialectical_types import DialecticalTask

SyncHook = Callable[[Any | None], None]


@runtime_checkable
class MemoryIntegration(Protocol):
    """Protocol describing the memory interface used by the reasoning loop."""

    def store_dialectical_result(
        self,
        task: DialecticalTask,
        result: DialecticalSequence | Mapping[str, Any],
    ) -> None:
        """Persist a dialectical reasoning result for later retrieval."""


@runtime_checkable
class MemoryManager(Protocol):
    """Protocol describing memory managers that support synchronization hooks."""

    def register_sync_hook(self, hook: SyncHook) -> None:
        """Register a callback that should run after updates are flushed."""

    def flush_updates(self) -> None:
        """Flush pending updates to durable storage."""


@runtime_checkable
class EDRRCoordinatorProtocol(Protocol):
    """Protocol for coordinator implementations consumed by the reasoning loop."""

    def record_consensus_failure(self, error: Exception) -> None:
        """Record a consensus failure raised by the dialectical reasoning step."""

    def record_expand_results(self, result: dict[str, Any]) -> dict[str, Any]:
        """Persist results produced during the Expand phase."""

    def record_differentiate_results(self, result: dict[str, Any]) -> dict[str, Any]:
        """Persist results produced during the Differentiate phase."""

    def record_refine_results(self, result: dict[str, Any]) -> dict[str, Any]:
        """Persist results produced during the Refine phase."""


@runtime_checkable
class WSDETeamProtocol(Protocol):
    """Minimal protocol exposing the hooks used by dialectical reasoning."""

    dialectical_hooks: list[Callable[..., Any]]


@dataclass(slots=True)
class NullWSDETeam:
    """Simple WSDE team stub satisfying :class:`WSDETeamProtocol`."""

    dialectical_hooks: list[Callable[..., Any]] = field(default_factory=list)


@dataclass(slots=True)
class CoordinatorRecorder:
    """Dataclass collecting coordinator interactions for assertions in tests."""

    records: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    failures: list[Exception] = field(default_factory=list)

    def record_consensus_failure(self, error: Exception) -> None:
        self.failures.append(error)

    def record_expand_results(self, result: dict[str, Any]) -> dict[str, Any]:
        self.records.append(("expand", result))
        return result

    def record_differentiate_results(self, result: dict[str, Any]) -> dict[str, Any]:
        self.records.append(("differentiate", result))
        return result

    def record_refine_results(self, result: dict[str, Any]) -> dict[str, Any]:
        self.records.append(("refine", result))
        return result


@dataclass(slots=True)
class MemoryIntegrationLog:
    """Dataclass capturing calls made to the memory integration."""

    calls: list[tuple[dict[str, Any], dict[str, Any]]] = field(default_factory=list)

    def store_dialectical_result(
        self,
        task: DialecticalTask,
        result: DialecticalSequence | Mapping[str, Any],
    ) -> None:
        if isinstance(task, DialecticalTask):
            task_payload = task.to_dict()
        elif isinstance(task, Mapping):
            task_payload = dict(task)
        else:  # pragma: no cover - defensive guard for unexpected payloads
            task_payload = {"value": task}

        if isinstance(result, DialecticalSequence):
            result_payload = result.to_dict()
        elif isinstance(result, Mapping):
            result_payload = dict(result)
        else:  # pragma: no cover - defensive guard for unexpected payloads
            result_payload = {"value": result}

        self.calls.append((task_payload, result_payload))
