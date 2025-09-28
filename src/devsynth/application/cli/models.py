from __future__ import annotations

"""Data transfer objects and protocols for CLI infrastructure."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias

from rich.console import RenderableType

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from typer import Context

    from devsynth.application.cli.command_output_formatter import (
        CommandOutputStyle,
        CommandOutputType,
    )


BridgeErrorPayload: TypeAlias = Exception | Mapping[str, object] | str
"""Payload accepted by UX bridge error handlers."""


CommandTableRow: TypeAlias = Mapping[str, object]
CommandTableData: TypeAlias = Sequence[CommandTableRow]
CommandListData: TypeAlias = Sequence[object]


@dataclass(frozen=True, slots=True)
class CommandDisplay:
    """Representation of formatted CLI content ready for rendering."""

    renderable: RenderableType
    output_type: "CommandOutputType"
    output_style: "CommandOutputStyle"
    title: str | None = None
    subtitle: str | None = None


@dataclass(frozen=True, slots=True)
class ProgressHistoryEntry:
    """Capture of a status transition for a long running task."""

    time: float
    status: str
    completed: float


@dataclass(frozen=True, slots=True)
class ProgressCheckpoint:
    """Checkpoint recorded during long running progress updates."""

    time: float
    progress: float
    eta: float


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


@dataclass(slots=True)
class SubtaskState:
    """Runtime information tracked for each subtask."""

    task_id: int
    total: float


@dataclass(frozen=True, slots=True)
class ProgressSubtaskSpec:
    """Configuration for a subtask provided when starting progress."""

    name: str
    total: int = 100
    status: str = "Starting..."


ProgressSubtaskLike: TypeAlias = ProgressSubtaskSpec | Mapping[str, object]
ProgressUpdate: TypeAlias = Callable[[float, str | None, str | None, str | None], None]
TyperAutocomplete: TypeAlias = Callable[["Context", str], list[str]]
CommandResultData: TypeAlias = (
    str
    | CommandTableRow
    | CommandTableData
    | CommandListData
    | CommandDisplay
)
"""Supported input values for standardized command formatting."""

