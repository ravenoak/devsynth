from __future__ import annotations

"""Data transfer objects and protocols for CLI infrastructure."""

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, TypeAlias, overload, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from rich.console import RenderableType
else:  # pragma: no cover - fallback for runtime when Rich is unavailable
    RenderableType = object

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from typer import Context

    from devsynth.application.cli.command_output_formatter import (
        CommandOutputStyle,
        CommandOutputType,
    )


@runtime_checkable
class SupportsBridgeErrorPayload(Protocol):
    """Protocol for objects that can be converted into a bridge error payload."""

    def to_bridge_error(self) -> Mapping[str, object]:
        """Return a mapping compatible with :meth:`UXBridge.handle_error`."""


@dataclass(frozen=True, slots=True)
class BridgeErrorDetails:
    """Structured payload describing an error for bridge consumption."""

    message: str
    context: Mapping[str, object] = field(default_factory=dict)
    suggestions: Sequence[str] = field(default_factory=tuple)

    def to_bridge_error(self) -> Mapping[str, object]:
        """Render the error details as an immutable mapping."""

        payload: dict[str, object] = {"message": self.message}
        if self.context:
            payload["context"] = dict(self.context)
        if self.suggestions:
            payload["suggestions"] = tuple(self.suggestions)
        return MappingProxyType(payload)


BridgeErrorPayload: TypeAlias = (
    Exception | SupportsBridgeErrorPayload | BridgeErrorDetails | str
)
"""Payload accepted by UX bridge error handlers."""


@dataclass(frozen=True, slots=True, init=False)
class CommandTableRow(Mapping[str, object]):
    """Immutable mapping representing a row for tabular CLI output."""

    _data: Mapping[str, object]

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        **values: object,
    ) -> None:
        combined: dict[str, object] = {}
        if data:
            combined.update({str(key): value for key, value in data.items()})
        combined.update({str(key): value for key, value in values.items()})
        object.__setattr__(self, "_data", MappingProxyType(combined))

    def __getitem__(self, key: str) -> object:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: str, default: object | None = None) -> object | None:
        """Return ``default`` when *key* is missing to mirror ``dict.get``."""

        return self._data.get(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        """Return the value for *key* converted to ``str`` when available."""

        value = self._data.get(key, default)
        return str(value)

    def to_dict(self) -> dict[str, object]:
        """Return a mutable copy of the underlying mapping."""

        return dict(self._data)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> CommandTableRow:
        """Create a row from an arbitrary mapping."""

        return cls(data=data)


@dataclass(frozen=True, slots=True)
class CommandTableData(Sequence[CommandTableRow]):
    """Immutable sequence of :class:`CommandTableRow` entries."""

    rows: tuple[CommandTableRow, ...] = field(default_factory=tuple)

    def __iter__(self) -> Iterator[CommandTableRow]:
        return iter(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    @overload
    def __getitem__(
        self, index: int
    ) -> CommandTableRow:  # pragma: no cover - typing only
        ...

    @overload
    def __getitem__(
        self, index: slice
    ) -> tuple[CommandTableRow, ...]:  # pragma: no cover - typing only
        ...

    def __getitem__(
        self, index: int | slice
    ) -> CommandTableRow | tuple[CommandTableRow, ...]:
        return self.rows[index]

    @classmethod
    def from_iterable(
        cls, rows: Sequence[CommandTableRow | Mapping[str, object]]
    ) -> CommandTableData:
        """Coerce raw mappings into a structured table sequence."""

        coerced = tuple(
            (
                row
                if isinstance(row, CommandTableRow)
                else CommandTableRow.from_mapping(row)
            )
            for row in rows
        )
        return cls(rows=coerced)


@dataclass(frozen=True, slots=True)
class CommandListData(Sequence[object]):
    """Immutable representation of list-style output."""

    items: tuple[object, ...] = field(default_factory=tuple)

    def __iter__(self) -> Iterator[object]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    @overload
    def __getitem__(self, index: int) -> object:  # pragma: no cover - typing only
        ...

    @overload
    def __getitem__(
        self, index: slice
    ) -> tuple[object, ...]:  # pragma: no cover - typing only
        ...

    def __getitem__(self, index: int | slice) -> object | tuple[object, ...]:
        return self.items[index]

    @classmethod
    def from_iterable(cls, items: Sequence[object]) -> CommandListData:
        return cls(items=tuple(items))


@dataclass(frozen=True, slots=True)
class ManifestSummary:
    """Lightweight summary information about a project manifest."""

    path: Path
    version: str | None = None
    is_valid: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def as_table(self) -> CommandTableData:
        """Render the manifest summary as tabular rows for display."""

        rows = [
            CommandTableRow({"Field": "Path", "Value": str(self.path)}),
            CommandTableRow({"Field": "Version", "Value": self.version or "Unknown"}),
            CommandTableRow(
                {"Field": "Valid", "Value": "Yes" if self.is_valid else "No"}
            ),
        ]
        for key, value in self.metadata.items():
            rows.append(CommandTableRow({"Field": str(key), "Value": value}))
        return CommandTableData(rows=tuple(rows))


@dataclass(frozen=True, slots=True)
class CommandDisplay:
    """Representation of formatted CLI content ready for rendering."""

    renderable: RenderableType
    output_type: CommandOutputType
    output_style: CommandOutputStyle
    title: str | None = None
    subtitle: str | None = None


@dataclass(frozen=True, slots=True)
class ProgressHistoryEntry:
    """Capture of a status transition for a long running task."""

    time: float
    status: str
    completed: float

    def __getitem__(self, key: str) -> float | str:
        if key == "time":
            return self.time
        if key == "status":
            return self.status
        if key == "completed":
            return self.completed
        raise KeyError(key)


@dataclass(frozen=True, slots=True)
class ProgressCheckpoint:
    """Checkpoint recorded during long running progress updates."""

    time: float
    progress: float
    eta: float

    def __getitem__(self, key: str) -> float:
        if key == "time":
            return self.time
        if key == "progress":
            return self.progress
        if key == "eta":
            return self.eta
        raise KeyError(key)


@dataclass(frozen=True, slots=True)
class ProgressSnapshot:
    """Immutable snapshot of current progress state."""

    description: str
    progress: float
    elapsed: float
    elapsed_str: str
    subtasks: int
    history: Sequence[ProgressHistoryEntry] = field(default_factory=tuple)
    checkpoints: Sequence[ProgressCheckpoint] = field(default_factory=tuple)
    eta: float | None = None
    eta_str: str | None = None
    remaining: float | None = None
    remaining_str: str | None = None

    def _mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "description": self.description,
                "progress": self.progress,
                "elapsed": self.elapsed,
                "elapsed_str": self.elapsed_str,
                "subtasks": self.subtasks,
                "history": self.history,
                "checkpoints": self.checkpoints,
                "eta": self.eta,
                "eta_str": self.eta_str,
                "remaining": self.remaining,
                "remaining_str": self.remaining_str,
            }
        )

    def __getitem__(self, key: str) -> object:
        mapping = self._mapping()
        if key not in mapping:
            raise KeyError(key)
        return mapping[key]

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        value = self._mapping().get(key)
        return value is not None


@dataclass(slots=True, eq=False)
class SubtaskState:
    """Runtime information tracked for each subtask."""

    task_id: int
    total: float

    def __hash__(self) -> int:
        return hash(self.task_id)

    def __eq__(self, other: object) -> bool:  # pragma: no cover - simple comparison
        if isinstance(other, SubtaskState):
            return (self.task_id, self.total) == (other.task_id, other.total)
        if isinstance(other, int):
            return self.task_id == other
        return NotImplemented

    def __int__(self) -> int:
        return self.task_id

    def __index__(self) -> int:
        return self.task_id


@dataclass(frozen=True, slots=True)
class ProgressSubtaskSpec:
    """Configuration for a subtask provided when starting progress."""

    name: str
    total: int = 100
    status: str = "Starting..."

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> ProgressSubtaskSpec:
        """Build a :class:`ProgressSubtaskSpec` from a generic mapping."""

        def _coerce_total(value: object) -> int:
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:  # pragma: no cover - defensive
                    return 100
            return 100

        return cls(
            name=str(data.get("name", "Subtask")),
            total=_coerce_total(data.get("total", 100)),
            status=str(data.get("status", "Starting...")),
        )


ProgressSubtaskLike: TypeAlias = ProgressSubtaskSpec | Mapping[str, object]


def coerce_subtask_spec(subtask: ProgressSubtaskLike) -> ProgressSubtaskSpec:
    """Return a concrete :class:`ProgressSubtaskSpec` for ``subtask``."""

    if isinstance(subtask, ProgressSubtaskSpec):
        return subtask
    return ProgressSubtaskSpec.from_mapping(subtask)


ProgressUpdate: TypeAlias = Callable[[float, str | None, str | None, str | None], None]
TyperAutocomplete: TypeAlias = Callable[["Context", str], list[str]]
CommandResultData: TypeAlias = (
    str | CommandTableRow | CommandTableData | CommandListData | CommandDisplay
)
"""Supported input values for standardized command formatting."""
