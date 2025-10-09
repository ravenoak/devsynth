"""Focused tests for core OutputFormatter behaviors."""

from __future__ import annotations

import pytest
from rich.panel import Panel
from rich.text import Text

from devsynth.interface.output_formatter import OutputFormatter

pytestmark = pytest.mark.fast


def test_sanitize_output_delegates_and_handles_edge_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure sanitize_output delegates, casts to str, and validates inputs.

    ReqID: N/A
    """

    formatter = OutputFormatter()
    calls: list[str] = []

    def fake_sanitize(value: str) -> str:
        calls.append(value)
        return f"sanitized:{value}"

    monkeypatch.setattr(
        "devsynth.interface.output_formatter.global_sanitize_output",
        fake_sanitize,
    )

    assert formatter.sanitize_output("plain text") == "sanitized:plain text"
    assert formatter.sanitize_output(123) == "sanitized:123"
    assert calls == ["plain text", "123"]

    # Empty strings bypass the delegate and short-circuit to an empty result.
    assert formatter.sanitize_output("") == ""
    assert calls == ["plain text", "123"]

    with pytest.raises(AttributeError):
        formatter.sanitize_output(None)  # type: ignore[arg-type]
    assert calls == ["plain text", "123"]


@pytest.mark.parametrize(
    ("message", "expected"),
    (
        ("ERROR: Disk failure", "error"),
        ("warning: Low memory", "warning"),
        ("Task completed successfully", "success"),
        ("INFO: FYI", "info"),
        ("# Heading", "heading"),
        ("", "normal"),
        ("Routine update", "normal"),
    ),
)
def test_detect_message_type_covers_known_patterns(message: str, expected: str) -> None:
    """detect_message_type should recognize rich semantic categories.

    ReqID: N/A
    """

    formatter = OutputFormatter()
    assert formatter.detect_message_type(message) == expected


def test_format_message_applies_status_styles(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_message should map semantic types to their Rich styles.

    ReqID: N/A
    """

    formatter = OutputFormatter()
    sanitized_calls: list[str] = []

    def fake_sanitize(self: OutputFormatter, text: str) -> str:
        sanitized_calls.append(text)
        return text

    monkeypatch.setattr(OutputFormatter, "sanitize_output", fake_sanitize)

    error_renderable = formatter.format_message("ERROR: Something bad")
    warning_renderable = formatter.format_message("WARNING: Heads up")
    success_renderable = formatter.format_message("SUCCESS: All good")

    assert isinstance(error_renderable, Text)
    assert isinstance(warning_renderable, Text)
    assert isinstance(success_renderable, Text)

    assert str(error_renderable) == "ERROR: Something bad"
    assert str(warning_renderable) == "WARNING: Heads up"
    assert str(success_renderable) == "SUCCESS: All good"

    assert error_renderable.style == "bold red"
    assert warning_renderable.style == "yellow"
    assert success_renderable.style == "green"

    assert sanitized_calls == [
        "ERROR: Something bad",
        "WARNING: Heads up",
        "SUCCESS: All good",
    ]


def test_display_highlight_branch_emits_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    """display should emit a Panel with emphasis styling when highlight is True.

    ReqID: N/A
    """

    formatter = OutputFormatter()
    sanitized: list[str] = []

    def fake_sanitize(self: OutputFormatter, text: str) -> str:
        sanitized.append(text)
        return f"sanitized:{text}"

    monkeypatch.setattr(OutputFormatter, "sanitize_output", fake_sanitize)

    printed: list[tuple[object, str | None]] = []

    class FakeConsole:
        def print(self, renderable, style=None):
            printed.append((renderable, style))

    formatter.set_console(FakeConsole())
    formatter.display("Important alert", highlight=True)

    assert sanitized == ["Important alert"]
    assert printed, "display should forward the panel to the console"

    renderable, style = printed[0]
    assert isinstance(renderable, Panel)
    assert renderable.renderable == "sanitized:Important alert"
    assert style == "bold white on blue"


def test_display_without_console_raises_value_error() -> None:
    """display should fail fast when no console has been configured.

    ReqID: N/A
    """

    formatter = OutputFormatter()

    with pytest.raises(ValueError):
        formatter.display("orphaned message")
