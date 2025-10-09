"""Focused rendering tests for CLI help utilities."""

from __future__ import annotations

import pytest
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from devsynth.application.cli.autocomplete import COMMANDS
from devsynth.application.cli.help import (
    display_all_commands_help,
    display_command_help,
    display_command_help_markdown,
    display_command_table,
)


class RecordingConsole(Console):
    """Console subclass that records renderables passed to ``print``."""

    def __init__(self) -> None:
        super().__init__(record=True, width=120)
        self.rendered: list[object] = []

    def print(self, *objects: object, **kwargs: object) -> None:  # type: ignore[override]
        self.rendered.extend(objects)
        super().print(*objects, **kwargs)


@pytest.fixture
def recording_console() -> RecordingConsole:
    """Provide a console that records printed renderables for inspection."""

    return RecordingConsole()


@pytest.mark.medium
def test_display_command_help_renders_panel(
    recording_console: RecordingConsole,
) -> None:
    """Command-specific help should render within a Rich panel."""

    command = next(iter(COMMANDS))
    display_command_help(command, recording_console)

    assert recording_console.rendered, "Console did not record any renderables"
    first_renderable = recording_console.rendered[0]
    assert isinstance(first_renderable, Panel)
    title_text = "" if first_renderable.title is None else str(first_renderable.title)
    body_text = str(first_renderable.renderable)
    assert command in title_text or command in body_text


@pytest.mark.medium
def test_display_all_commands_help_renders_panel(
    recording_console: RecordingConsole,
) -> None:
    """The command overview should render a panel summary."""

    display_all_commands_help(recording_console)

    assert recording_console.rendered, "Console did not record any renderables"
    first_renderable = recording_console.rendered[0]
    assert isinstance(first_renderable, Panel)
    title_text = "" if first_renderable.title is None else str(first_renderable.title)
    assert "DevSynth" in title_text


@pytest.mark.medium
def test_display_command_table_renders_table(
    recording_console: RecordingConsole,
) -> None:
    """Tables should be emitted as Rich Table instances for further styling."""

    display_command_table(None, recording_console)

    assert recording_console.rendered, "Console did not record any renderables"
    first_renderable = recording_console.rendered[0]
    assert isinstance(first_renderable, Table)


@pytest.mark.medium
def test_display_command_help_markdown_renders_markdown(
    recording_console: RecordingConsole,
) -> None:
    """Markdown help should emit a Rich Markdown renderable."""

    command = next(iter(COMMANDS))
    display_command_help_markdown(command, recording_console)

    assert recording_console.rendered, "Console did not record any renderables"
    first_renderable = recording_console.rendered[0]
    assert isinstance(first_renderable, Markdown)
    assert command in first_renderable.source
