from __future__ import annotations

from io import StringIO
from typing import Any

import pytest
from rich.console import Console

from devsynth.interface.command_output import CommandOutput, MessageType


class DummyFormatter:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    def format_message(
        self, message: str, message_type: str | None = None, highlight: bool = False
    ) -> str:
        self.calls.append(("format_message", message, message_type, highlight))
        return f"{message_type}:{message}"

    def _list_to_rich(self, items: list[Any], title: str | None = None) -> Any:
        self.calls.append(("_list_to_rich", items, title))
        return ("rich", items, title)

    def format_structured(self, data: Any, fmt: Any, title: str | None = None) -> Any:
        self.calls.append(("format_structured", data, fmt, title))
        return ("struct", fmt, data, title)

    def format_command_output(
        self,
        result: Any,
        format_name: str | None = None,
        title: str | None = None,
    ) -> Any:
        self.calls.append(("format_command_output", result, format_name, title))
        return ("cmd", format_name, result, title)

    def set_console(self, console: Console) -> None:  # pragma: no cover - simple setter
        self.calls.append(("set_console", console))


@pytest.fixture
def cmd_output() -> tuple[CommandOutput, DummyFormatter, Console]:
    console = Console(file=StringIO())
    co = CommandOutput(console)
    formatter = DummyFormatter()
    co.formatter = formatter
    return co, formatter, console


@pytest.mark.fast
def test_format_and_display_message(cmd_output) -> None:
    """Messages format and display via the formatter.

    ReqID: N/A"""

    co, formatter, console = cmd_output
    assert co.format_message("hi", MessageType.INFO) == "info:hi"
    co.display_message("hi", MessageType.SUCCESS)
    assert "success:hi" in console.file.getvalue()


@pytest.mark.fast
def test_format_error_suggestions(cmd_output) -> None:
    """Error formatting appends suggestions.

    ReqID: N/A"""

    co, formatter, _ = cmd_output
    err = co.format_error("permission denied")
    assert "Check file permissions" in err
    err2 = co.format_error("file not found")
    assert "not found" in err2
    assert "Suggestion" in err2


@pytest.mark.fast
def test_list_and_structured_outputs(cmd_output) -> None:
    """Structured output helpers delegate to formatter.

    ReqID: N/A"""

    co, formatter, console = cmd_output
    assert co.format_list([1, 2], title="nums")[0] == "rich"
    co.display_list([1])
    assert "rich" in console.file.getvalue()
    console.file = StringIO()
    assert co.format_json({"a": 1})[0] == "struct"
    co.display_json({"a": 1})
    assert "struct" in console.file.getvalue()
    console.file = StringIO()
    assert co.format_yaml({"a": 1})[0] == "struct"
    co.display_yaml({"a": 1})
    assert "struct" in console.file.getvalue()
    console.file = StringIO()
    assert co.format_command_result({"a": 1}, format_name="json")[0] == "cmd"
    co.display_command_result({"a": 1}, format_name="json")
    assert "cmd" in console.file.getvalue()


@pytest.mark.fast
def test_set_console(cmd_output) -> None:
    """Console setter swaps the output target.

    ReqID: N/A"""

    co, formatter, _ = cmd_output
    new_console = Console(file=StringIO())
    co.set_console(new_console)
    assert co.console is new_console
