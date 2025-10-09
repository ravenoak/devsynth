"""WebUI error handling tests focusing on `_handle_command_errors`."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock

import pytest

from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("force_webui_available"),
]


@pytest.fixture
def webui_module(monkeypatch):
    """Reload the WebUI module with a mocked Streamlit dependency."""

    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    return webui


def test_handle_command_errors_passthrough(webui_module, monkeypatch):
    """Successful calls return their result without touching the UI."""

    ui = webui_module.WebUI()
    monkeypatch.setattr(ui, "display_result", MagicMock())

    assert ui._handle_command_errors(lambda value: value + 1, "unused", 2) == 3
    ui.display_result.assert_not_called()


@pytest.mark.parametrize(
    "factory, expected, hint",
    [
        (
            lambda: FileNotFoundError(2, "missing", "config.yaml"),
            "ERROR: File not found: config.yaml",
            "Make sure the file exists",
        ),
        (
            lambda: PermissionError(13, "denied", "secrets.env"),
            "ERROR: Permission denied: secrets.env",
            "necessary permissions",
        ),
        (
            lambda: ValueError("bad input"),
            "ERROR: Invalid value: bad input",
            "Please check your input",
        ),
        (
            lambda: KeyError("api_key"),
            "ERROR: Missing key: 'api_key'",
            "Verify that the referenced key exists",
        ),
        (
            lambda: TypeError("wrong type"),
            "ERROR: Type error: wrong type",
            "Check that all inputs",
        ),
    ],
)
def test_handle_command_errors_known_exceptions(
    webui_module, factory, expected, hint, monkeypatch
):
    """Each specific exception surfaces user guidance via ``display_result``."""

    ui = webui_module.WebUI()
    calls: list[tuple[str, dict[str, object]]] = []

    def record(message: str, **kwargs: object) -> None:
        calls.append((message, kwargs))

    monkeypatch.setattr(ui, "display_result", record)

    def raising() -> None:
        raise factory()

    assert ui._handle_command_errors(raising, "ignored") is None
    assert any(expected in message for message, _ in calls)
    assert any(hint in message for message, _ in calls)


def test_handle_command_errors_generic_exception(webui_module, monkeypatch):
    """Unexpected errors include traceback details via Streamlit widgets."""

    streamlit_stub = sys.modules["streamlit"]
    ui = webui_module.WebUI()
    recorded: list[str] = []

    def capture(message: str, **_kwargs: object) -> None:
        recorded.append(message)

    monkeypatch.setattr(ui, "display_result", capture)

    class Boom(RuntimeError):
        pass

    def raising() -> None:
        raise Boom("kaboom")

    assert ui._handle_command_errors(raising, "While performing task") is None
    assert any("While performing task" in message for message in recorded)
    assert any("Boom" in message for message in recorded)
    assert streamlit_stub.code.called
