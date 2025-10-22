"""Shared helpers for Textual-enabled wizard workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from devsynth.interface.ux_bridge import UXBridge, sanitize_output


BACK_COMMANDS: set[str] = {"back", "previous", "prev"}
KEYBOARD_BACK_COMMANDS: set[str] = {
    "←",
    "left",
    "arrow_left",
    "key_left",
    "<left>",
    "shift+tab",
    "ctrl+b",
    "alt+left",
    "hotkey_back",
}


def is_back_command(reply: str, *, keyboard_shortcuts: bool) -> bool:
    """Return ``True`` when ``reply`` should navigate backwards."""

    normalized = reply.strip().lower()
    if normalized in BACK_COMMANDS:
        return True
    if not keyboard_shortcuts:
        return False
    return normalized in KEYBOARD_BACK_COMMANDS


@dataclass(slots=True)
class _FieldRecord:
    key: str
    label: str
    value: str


@dataclass(slots=True)
class TextualWizardViewModel:
    """Maintain wizard state for bridges that expose Textual layouts."""

    bridge: UXBridge
    steps: Sequence[str]
    contextual_help: Mapping[str, str | Mapping[str, str]] = field(default_factory=dict)
    keyboard_shortcuts: bool = False
    _layout: Any | None = field(init=False, repr=False)
    _steps: list[str] = field(init=False, repr=False)
    _active_step: int = field(init=False, repr=False)
    _content_lines: list[str] = field(init=False, repr=False)
    _activity_log: list[str] = field(init=False, repr=False)
    _field_records: dict[str, _FieldRecord] = field(init=False, repr=False)
    _summary_lines: list[str] = field(init=False, repr=False)
    _keyboard_hint: str | None = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._layout = getattr(self.bridge, "layout", None)
        self._steps = [sanitize_output(step) for step in self.steps]
        self._active_step = 0
        self._content_lines: list[str] = []
        self._activity_log: list[str] = []
        self._field_records: dict[str, _FieldRecord] = {}
        self._summary_lines: list[str] = []
        self._keyboard_hint = (
            sanitize_output("Shortcuts: ← Back | → Next")
            if self.keyboard_shortcuts
            else None
        )
        self._render_sidebar()

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render_sidebar(self) -> None:
        if not self._layout:
            return
        lines = []
        for index, title in enumerate(self._steps):
            prefix = "➤" if index == self._active_step else "•"
            lines.append(f"{prefix} {title}")
        self._layout.sidebar.lines = lines

    def _render_content(self) -> None:
        if not self._layout:
            return
        self._layout.content.lines = list(self._content_lines)

    def _render_log(self) -> None:
        if not self._layout:
            return
        lines = list(self._activity_log)
        if self._field_records:
            lines.append(sanitize_output("Current selections:"))
            for record in self._field_records.values():
                lines.append(f"{record.label}: {record.value}")
        if self._summary_lines:
            lines.append(sanitize_output("Summary:"))
            lines.extend(self._summary_lines)
        self._layout.log.lines = lines

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_active_step(self, index: int) -> None:
        self._active_step = max(0, min(index, len(self._steps) - 1))
        self._render_sidebar()

    def log_progress(self, description: str, status: str | None = None) -> None:
        desc = sanitize_output(description)
        if status:
            status_text = sanitize_output(status)
            desc = f"{desc} [{status_text}]"
        self._activity_log.append(desc)
        self._render_log()

    def resolve_help(self, topic: str, subtopic: str | None = None) -> str | None:
        entry = self.contextual_help.get(topic)
        if isinstance(entry, Mapping):
            if subtopic is None:
                return None
            help_text = entry.get(subtopic)
        else:
            help_text = entry
        if help_text is None:
            return None
        return sanitize_output(help_text)

    def present_question(
        self,
        topic: str,
        question: str,
        *,
        subtopic: str | None = None,
        help_text: str | None = None,
    ) -> None:
        base_help = help_text or self.resolve_help(topic, subtopic)
        lines: list[str] = []
        if base_help:
            lines.append(base_help)
        lines.append(sanitize_output(question))
        if self._keyboard_hint:
            lines.append(self._keyboard_hint)
        self._content_lines = lines
        self._render_content()

    def record_field(self, key: str, label: str, value: object | None) -> None:
        display_value = "—"
        if isinstance(value, bool):
            display_value = "Enabled" if value else "Disabled"
        elif value not in (None, ""):
            display_value = str(value)
        record = _FieldRecord(
            key=key,
            label=sanitize_output(label),
            value=sanitize_output(display_value),
        )
        self._field_records[key] = record
        self._render_log()

    def set_summary_lines(self, lines: Sequence[str]) -> None:
        self._summary_lines = [sanitize_output(line) for line in lines]
        self._render_log()

    def record_activity(self, message: str) -> None:
        self._activity_log.append(sanitize_output(message))
        self._render_log()


__all__ = ["TextualWizardViewModel", "is_back_command"]

