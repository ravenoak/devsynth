import sys
from types import ModuleType

import pytest

import devsynth.interface.webui.commands as commands
from devsynth.exceptions import DevSynthError
from devsynth.interface import webui
from devsynth.interface.webui.commands import CommandHandlingMixin
from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("force_webui_available"),
]


class DummyCommands(CommandHandlingMixin):
    def __init__(self):
        self.results: list[str] = []

    def display_result(self, message: str, **_kwargs: object) -> None:
        self.results.append(message)

    def _format_error_message(self, error: Exception) -> str:
        return f"{error.__class__.__name__}: {error}"

    def _render_traceback(self, text: str) -> None:
        self.results.append(text)


def test_cli_returns_module_attribute(monkeypatch):
    """ReqID: FR-203 prefer WebUI overrides when resolving commands."""
    dummy = DummyCommands()

    def sentinel():
        return "ok"

    monkeypatch.setattr(webui, "dummy_cmd", sentinel, raising=False)
    assert dummy._cli("dummy_cmd") is sentinel


def test_cli_returns_none_when_missing():
    """ReqID: FR-204 return ``None`` for missing CLI commands."""
    dummy = DummyCommands()
    assert dummy._cli("nonexistent") is None


def test_handle_command_errors_pass_through(monkeypatch):
    """ReqID: FR-205 propagate successful command results unchanged."""
    dummy = DummyCommands()
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    assert dummy._handle_command_errors(lambda value: value + 1, "unused", 2) == 3
    assert dummy.results == []


@pytest.mark.parametrize(
    "factory, expected",
    [
        (lambda: FileNotFoundError(2, "missing", "config.yaml"), "File not found"),
        (lambda: PermissionError(13, "denied", "secrets.env"), "Permission denied"),
        (lambda: ValueError("bad"), "Invalid value"),
        (lambda: KeyError("api_key"), "Missing key"),
        (lambda: TypeError("wrong"), "Type error"),
    ],
)
def test_handle_command_errors_specific_exceptions(factory, expected, monkeypatch):
    """ReqID: FR-206 map common exceptions to actionable guidance."""
    dummy = DummyCommands()
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    def raising():
        raise factory()

    assert dummy._handle_command_errors(raising, "ignored") is None
    assert any(expected in message for message in dummy.results)


def test_handle_command_errors_generic_exception(monkeypatch):
    """ReqID: FR-207 expose unexpected exceptions with traceback."""
    dummy = DummyCommands()
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    class Boom(RuntimeError):
        pass

    def raising():
        raise Boom("kaboom")

    assert dummy._handle_command_errors(raising, "While performing task") is None
    assert any("While performing task" in message for message in dummy.results)
    assert any("Boom" in message for message in dummy.results)


def test_cli_uses_cli_module_when_available(monkeypatch):
    """ReqID: FR-215 resolve commands from the CLI module when present."""

    dummy = DummyCommands()

    module = ModuleType("devsynth.application.cli")

    def sentinel():
        return "cli"

    module.cli_command = sentinel
    monkeypatch.setattr(commands, "_cli_mod", module, raising=False)

    assert dummy._cli("cli_command") is sentinel


def test_handle_command_errors_reraises_devsynth_error(monkeypatch):
    """ReqID: FR-216 propagate DevSynthError without interception."""

    dummy = DummyCommands()
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    class Boom(DevSynthError):
        """Sentinel exception for propagation checks."""

    def raising():
        raise Boom("fail")

    with pytest.raises(Boom):
        dummy._handle_command_errors(raising, "ignored")

    assert dummy.results == []
