"""Textual-inspired UX bridge with multi-pane awareness.

The bridge exposes capability metadata so orchestration wizards can detect
available Textual features without coupling to a specific UI implementation.
It purposely degrades gracefully when the optional ``textual`` dependency is
missing, enabling the CLI to continue operating with the baseline Rich/Typer
stack while still supporting richer layouts when Textual is installed.

When Textual is available the bridge can launch a lightweight event loop that
mirrors the recorded pane content. The loop favours accessibility by allowing
colorblind-friendly palettes negotiated by the CLI layer and falls back to a
no-op when automated tests disable interactive sessions via the
``DEVSYNTH_TUI_AUTOMATED`` flag.
"""

from __future__ import annotations

import copy
import os
from collections import deque
from dataclasses import dataclass
from importlib import util as import_util
from types import MappingProxyType
from typing import Any, Deque
from collections.abc import Mapping, Sequence

from devsynth.interface.ux_bridge import (
    PROGRESS_STATUS_VALUES,
    ProgressIndicator,
    ProgressStatusText,
    SubtaskProgressSnapshot,
    SupportsNestedSubtasks,
    UXBridge,
    sanitize_output,
)

# Type ignore for complex optional dependency typing issues
# The code works correctly at runtime, mypy struggles with conditional imports


_TEXTUAL_SPEC = import_util.find_spec("textual")
TEXTUAL_AVAILABLE: bool = _TEXTUAL_SPEC is not None


@dataclass
class LayoutPane:
    """Simple container representing a pane within the Textual layout."""

    title: str
    lines: list[str]

    def log(self, message: str) -> None:
        """Append a message to the pane's history."""

        self.lines.append(message)

    def clear(self) -> None:
        """Clear all recorded lines."""

        self.lines.clear()


@dataclass
class MultiPaneLayout:
    """Logical representation of the Textual multi-pane layout."""

    sidebar: LayoutPane
    content: LayoutPane
    log: LayoutPane

    @classmethod
    def default(cls) -> MultiPaneLayout:
        """Create a layout with sensible defaults for wizards."""

        return cls(
            sidebar=LayoutPane(title="Navigation", lines=[]),
            content=LayoutPane(title="Content", lines=[]),
            log=LayoutPane(title="Activity Log", lines=[]),
        )

    def snapshot(self) -> Mapping[str, list[str]]:
        """Return a shallow copy of the pane histories for inspection."""

        return {
            "sidebar": list(self.sidebar.lines),
            "content": list(self.content.lines),
            "log": list(self.log.lines),
        }


class TextualUXBridge(UXBridge):
    """UX bridge that mirrors Textual's panelled interface."""

    def __init__(
        self,
        *,
        question_responses: Sequence[str] | None = None,
        confirm_responses: Sequence[bool] | None = None,
        layout: MultiPaneLayout | None = None,
        require_textual: bool = False,
        colorblind_mode: bool = False,
        theme_overrides: Mapping[str, str] | None = None,
    ) -> None:
        if require_textual and not TEXTUAL_AVAILABLE:
            raise RuntimeError(
                "The 'textual' optional dependency is required for this bridge."
            )

        self._textual_enabled = TEXTUAL_AVAILABLE
        self._question_responses: Deque[str] = deque(question_responses or [])
        self._confirm_responses: Deque[bool] = deque(confirm_responses or [])
        self._layout = layout or MultiPaneLayout.default()
        self._interaction_history: list[dict[str, Any]] = []
        self._progress_snapshots: list[SubtaskProgressSnapshot] = []
        self._colorblind_mode = bool(colorblind_mode)
        self._theme_overrides = dict(theme_overrides or {})

    # ------------------------------------------------------------------
    # UXBridge interface
    # ------------------------------------------------------------------

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        sanitized_message = sanitize_output(message)
        sanitized_choices = (
            [sanitize_output(choice) for choice in choices]
            if choices is not None
            else None
        )
        response = self._next_question_response(default)

        self._layout.content.log(sanitized_message)
        if sanitized_choices:
            self._layout.sidebar.log(", ".join(sanitized_choices))

        self._interaction_history.append(
            {
                "type": "question",
                "message": sanitized_message,
                "choices": sanitized_choices,
                "default": default if show_default else None,
                "response": response,
            }
        )

        return response

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        sanitized_message = sanitize_output(message)
        response = self._next_confirm_response(default)

        self._layout.content.log(sanitized_message)
        self._interaction_history.append(
            {
                "type": "confirm",
                "message": sanitized_message,
                "default": default,
                "response": response,
            }
        )

        return response

    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        sanitized_message = sanitize_output(message)
        self._layout.log.log(sanitized_message)
        self._interaction_history.append(
            {
                "type": "display",
                "message": sanitized_message,
                "highlight": highlight,
                "message_type": message_type,
            }
        )

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return _TextualProgress(self, description=description, total=total)

    # ------------------------------------------------------------------
    # Capability and metadata helpers
    # ------------------------------------------------------------------

    @property
    def capabilities(self) -> Mapping[str, bool]:
        base = {
            "supports_layout_panels": self._textual_enabled,
            "supports_keyboard_shortcuts": self._textual_enabled,
            "supports_progress_updates": True,
            "supports_rich_text": self._textual_enabled,
        }
        return MappingProxyType(base)

    @property
    def layout(self) -> MultiPaneLayout:
        return self._layout

    @property
    def interaction_history(self) -> tuple[dict[str, Any], ...]:
        return tuple(copy.deepcopy(history) for history in self._interaction_history)

    @property
    def progress_snapshots(self) -> tuple[SubtaskProgressSnapshot, ...]:
        return tuple(copy.deepcopy(snapshot) for snapshot in self._progress_snapshots)

    @staticmethod
    def is_textual_available() -> bool:
        return TEXTUAL_AVAILABLE

    # ------------------------------------------------------------------
    # Theme helpers
    # ------------------------------------------------------------------

    @property
    def colorblind_mode(self) -> bool:
        """Return whether the bridge prefers the colorblind-friendly palette."""

        return self._colorblind_mode

    @property
    def theme_overrides(self) -> Mapping[str, str]:
        """Return theme overrides negotiated with the CLI layer."""

        return MappingProxyType(dict(self._theme_overrides))

    def configure_theme(
        self,
        *,
        colorblind_mode: bool | None = None,
        theme_overrides: Mapping[str, str] | None = None,
    ) -> None:
        """Update theme preferences to keep Textual output in sync with the CLI."""

        if colorblind_mode is not None:
            self._colorblind_mode = bool(colorblind_mode)
        if theme_overrides is not None:
            self._theme_overrides = dict(theme_overrides)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_question_response(self, default: str | None) -> str:
        if self._question_responses:
            return self._question_responses.popleft()
        if default is not None:
            return default
        return ""

    def _next_confirm_response(self, default: bool) -> bool:
        if self._confirm_responses:
            return self._confirm_responses.popleft()
        return default

    def _record_progress(self, snapshot: SubtaskProgressSnapshot) -> None:
        self._progress_snapshots.append(copy.deepcopy(snapshot))
        description = snapshot.get("description", "")
        status = snapshot.get("status")
        if status:
            self._layout.log.log(f"[{status}] {description}")
        else:
            self._layout.log.log(str(description))

    # ------------------------------------------------------------------
    # Event loop helpers
    # ------------------------------------------------------------------

    def run_event_loop(self, *, refresh_interval: float = 0.25) -> None:
        """Launch a lightweight Textual event loop to mirror pane content."""

        automated = os.environ.get("DEVSYNTH_TUI_AUTOMATED", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        if automated:
            return

        if not self._textual_enabled:
            raise RuntimeError(
                "Textual support is unavailable. Install the 'textual' extra to "
                "launch the DevSynth TUI."
            )

        try:
            from textual.app import App, ComposeResult
            from textual.containers import Horizontal
            from textual.widgets import Footer, Header, Static
        except Exception as exc:  # pragma: no cover - optional dependency guard
            raise RuntimeError("Failed to import Textual runtime") from exc

        layout = self._layout
        color_accent = "#FF9900" if self._colorblind_mode else "#00A2FF"

        css = (
            "Screen { layout: vertical; }\n"
            "#panes { layout: horizontal; }\n"
            f"#sidebar, #content, #log {{ border: heavy {color_accent}; padding: 1 2; width: 1fr; }}\n"
            "#sidebar { background: rgba(0, 0, 0, 0.25); }\n"
            "#content { background: rgba(0, 0, 0, 0.15); }\n"
            "#log { background: rgba(0, 0, 0, 0.05); }\n"
        )

        overrides = "\n".join(
            f"#{key} {{ {value} }}" for key, value in self._theme_overrides.items()
        )
        if overrides:
            css = f"{css}\n{overrides}"

        class WizardApp(App):  # type: ignore[misc]
            CSS = css
            BINDINGS = [
                ("q", "quit", "Quit"),
                ("escape", "quit", "Quit"),
            ]

            def compose(self) -> ComposeResult:
                yield Header(show_clock=True)
                with Horizontal(id="panes"):
                    yield Static("", id="sidebar")
                    yield Static("", id="content")
                    yield Static("", id="log")
                yield Footer()

            def on_mount(self) -> None:  # pragma: no cover - UI side effect
                self.set_interval(refresh_interval, self.refresh_panes)
                self.refresh_panes()

            def refresh_panes(self) -> None:  # pragma: no cover - UI side effect
                sidebar = "\n".join(layout.sidebar.lines) or "—"
                content = "\n".join(layout.content.lines) or "—"
                log = "\n".join(layout.log.lines) or "—"
                self.query_one("#sidebar", Static).update(sidebar)
                self.query_one("#content", Static).update(content)
                self.query_one("#log", Static).update(log)

        WizardApp().run()


class _TextualProgress(ProgressIndicator, SupportsNestedSubtasks):
    """Progress indicator that mirrors Textual's live progress panels."""

    def __init__(
        self, bridge: TextualUXBridge, *, description: str, total: int
    ) -> None:
        self._bridge = bridge
        self._description = sanitize_output(description)
        self._total = max(total, 1)
        self._current = 0.0
        self._status = "Starting..."
        self._subtasks: dict[str, SubtaskProgressSnapshot] = {}
        self._nested_subtasks: dict[str, dict[str, SubtaskProgressSnapshot]] = {}
        self._counter = 0
        self._emit_snapshot()

    # ------------------------------------------------------------------
    # ProgressIndicator API
    # ------------------------------------------------------------------

    def update(
        self,
        *,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        self._current = min(self._total, max(0.0, self._current + float(advance)))
        if description is not None:
            self._description = sanitize_output(description)
        if status is not None:
            self._status = self._normalise_status(status)
        self._emit_snapshot()

    def complete(self) -> None:
        self._current = float(self._total)
        self._status = "Complete"
        self._emit_snapshot()

    # ------------------------------------------------------------------
    # Subtask helpers
    # ------------------------------------------------------------------

    def add_subtask(
        self,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str:
        task_id = self._next_id("subtask")
        self._subtasks[task_id] = self._build_subtask_snapshot(
            description, total, status
        )
        self._emit_snapshot()
        return task_id

    def update_subtask(
        self,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        snapshot = self._subtasks.get(task_id)
        if snapshot is None:
            raise KeyError(f"Unknown subtask id: {task_id}")

        current = float(snapshot.get("current", 0)) + float(advance)
        total = float(snapshot.get("total", 100)) or 100.0
        snapshot["current"] = min(total, max(0.0, current))
        if description is not None:
            snapshot["description"] = sanitize_output(description)
        if status is not None:
            snapshot["status"] = self._normalise_status(status)

        self._emit_snapshot()

    def complete_subtask(self, task_id: str) -> None:
        snapshot = self._subtasks.get(task_id)
        if snapshot is None:
            raise KeyError(f"Unknown subtask id: {task_id}")
        snapshot["current"] = snapshot.get("total", 100.0)
        snapshot["status"] = "Complete"
        self._emit_snapshot()

    def add_nested_subtask(
        self,
        parent_id: str,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str:
        if parent_id not in self._subtasks:
            raise KeyError(f"Unknown parent subtask id: {parent_id}")

        nested = self._nested_subtasks.setdefault(parent_id, {})
        task_id = self._next_id("nested")
        nested[task_id] = self._build_subtask_snapshot(description, total, status)
        self._emit_snapshot()
        return task_id

    def update_nested_subtask(
        self,
        parent_id: str,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        nested = self._nested_subtasks.get(parent_id)
        if nested is None or task_id not in nested:
            raise KeyError(f"Unknown nested subtask id: {task_id}")

        snapshot = nested[task_id]
        current = float(snapshot.get("current", 0)) + float(advance)
        total = float(snapshot.get("total", 100)) or 100.0
        snapshot["current"] = min(total, max(0.0, current))
        if description is not None:
            snapshot["description"] = sanitize_output(description)
        if status is not None:
            snapshot["status"] = self._normalise_status(status)

        self._emit_snapshot()

    def complete_nested_subtask(self, parent_id: str, task_id: str) -> None:
        nested = self._nested_subtasks.get(parent_id)
        if nested is None or task_id not in nested:
            raise KeyError(f"Unknown nested subtask id: {task_id}")
        snapshot = nested[task_id]
        snapshot["current"] = snapshot.get("total", 100.0)
        snapshot["status"] = "Complete"
        self._emit_snapshot()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def _normalise_status(self, status: str) -> ProgressStatusText:
        if status in PROGRESS_STATUS_VALUES:
            return status
        return "In progress..."

    def _build_subtask_snapshot(
        self, description: str, total: int, status: str
    ) -> SubtaskProgressSnapshot:
        return {
            "description": sanitize_output(description),
            "total": float(total),
            "current": 0.0,
            "status": self._normalise_status(status),
        }

    def _compose_subtasks(self) -> dict[str, SubtaskProgressSnapshot]:
        composed: dict[str, SubtaskProgressSnapshot] = {}
        for task_id, snapshot in self._subtasks.items():
            combined = dict(snapshot)
            nested = self._nested_subtasks.get(task_id)
            if nested:
                combined["nested_subtasks"] = {
                    nested_id: nested_snapshot
                    for nested_id, nested_snapshot in nested.items()
                }
            composed[task_id] = combined
        return composed

    def _emit_snapshot(self) -> None:
        snapshot: SubtaskProgressSnapshot = {
            "description": self._description,
            "total": float(self._total),
            "current": float(self._current),
            "status": self._status,
        }

        subtasks = self._compose_subtasks()
        if subtasks:
            snapshot["nested_subtasks"] = subtasks

        self._bridge._record_progress(snapshot)


__all__ = [
    "LayoutPane",
    "MultiPaneLayout",
    "TextualUXBridge",
    "TEXTUAL_AVAILABLE",
]
