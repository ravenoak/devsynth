"""Integration test for the WebUI using a stubbed Streamlit runtime."""

from types import SimpleNamespace
from typing import Any
from collections.abc import Callable

import pytest

from devsynth.interface import webui

pytestmark = [pytest.mark.requires_resource("webui"), pytest.mark.medium]


class FakeSessionState(dict):
    """Dictionary-like session state supporting attribute access."""

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class _Recorder:
    """Utility to record arbitrary method calls for later inspection."""

    def __init__(self, name: str, calls: list[tuple]):
        self._name = name
        self._calls = calls

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self._calls.append((self._name, args, kwargs))


class FakeExpander:
    """Context manager mirroring ``st.expander``."""

    def __init__(self, label: str, calls: list[tuple], **kwargs: Any) -> None:
        self._label = label
        self._calls = calls
        self._calls.append(("expander", label, kwargs))

    def __enter__(self) -> "FakeExpander":
        self._calls.append(("expander_enter", self._label))
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001 - interface parity
        self._calls.append(("expander_exit", self._label, exc_type))
        return False

    def __getattr__(self, name: str) -> Callable[..., None]:
        return _Recorder(f"expander_{name}", self._calls)


class FakeSpinner:
    """Context manager mirroring ``st.spinner``."""

    def __init__(self, message: str, calls: list[tuple]) -> None:
        self._message = message
        self._calls = calls
        self._calls.append(("spinner", message))

    def __enter__(self) -> "FakeSpinner":
        self._calls.append(("spinner_enter", self._message))
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001 - interface parity
        self._calls.append(("spinner_exit", self._message, exc_type))
        return False


class FakeStreamlit:
    """Minimal Streamlit replacement capturing WebUI interactions."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.session_state = FakeSessionState()
        self._selectbox_value: Any = None
        self._text_input_values: list[Any] = []
        self._checkbox_value: bool = True
        self._radio_value: str | None = None
        self.components = SimpleNamespace(
            v1=SimpleNamespace(
                html=lambda content, **kwargs: self.calls.append(
                    ("components_html", content, kwargs)
                )
            )
        )
        self.sidebar = SimpleNamespace(
            title=lambda text: self.calls.append(("sidebar_title", text)),
            markdown=lambda text, **kwargs: self.calls.append(
                ("sidebar_markdown", text, kwargs)
            ),
        )
        self.sidebar.radio = self._sidebar_radio

    # ------------------------------------------------------------------
    # Sidebar helpers
    # ------------------------------------------------------------------
    def _sidebar_radio(self, label: str, options: list[str], index: int = 0) -> str:
        self.calls.append(("sidebar_radio", label, tuple(options), index))
        if self._radio_value is not None:
            return self._radio_value
        return options[index]

    # ------------------------------------------------------------------
    # Streamlit API
    # ------------------------------------------------------------------
    def set_page_config(self, **kwargs: Any) -> None:
        self.calls.append(("set_page_config", kwargs))

    def markdown(self, content: str, **kwargs: Any) -> None:
        self.calls.append(("markdown", content, kwargs))

    def header(self, content: str) -> None:
        self.calls.append(("header", content))

    def selectbox(
        self, message: str, options: list[str], index: int = 0, key: str | None = None
    ) -> Any:
        self.calls.append(("selectbox", message, tuple(options), index, key))
        if self._selectbox_value is not None:
            return self._selectbox_value
        return options[index]

    def text_input(self, message: str, value: str = "", key: str | None = None) -> str:
        self.calls.append(("text_input", message, value, key))
        if self._text_input_values:
            return self._text_input_values.pop(0)
        return value

    def checkbox(
        self, message: str, value: bool = False, key: str | None = None
    ) -> bool:
        self.calls.append(("checkbox", message, value, key))
        return self._checkbox_value

    def info(self, message: str) -> None:
        self.calls.append(("info", message))

    def write(self, message: str) -> None:
        self.calls.append(("write", message))

    def error(self, message: str) -> None:
        self.calls.append(("error", message))

    def warning(self, message: str) -> None:
        self.calls.append(("warning", message))

    def success(self, message: str) -> None:
        self.calls.append(("success", message))

    def expander(self, label: str, **kwargs: Any) -> FakeExpander:
        return FakeExpander(label, self.calls, **kwargs)

    def spinner(self, message: str) -> FakeSpinner:
        return FakeSpinner(message, self.calls)

    def empty(self) -> SimpleNamespace:
        self.calls.append(("empty",))
        return SimpleNamespace(write=_Recorder("empty_write", self.calls))

    def progress(self, *args: Any, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(("progress", args, kwargs))
        return SimpleNamespace(update=_Recorder("progress_update", self.calls))

    def divider(self) -> None:
        self.calls.append(("divider",))

    def toggle(self, label: str, value: bool = False) -> bool:
        self.calls.append(("toggle", label, value))
        return value

    def button(self, label: str, **kwargs: Any) -> bool:
        self.calls.append(("button", label, kwargs))
        return False

    def text_area(self, label: str, value: str = "", height: int | None = None) -> str:
        self.calls.append(("text_area", label, value, height))
        return value

    def columns(self, count: int) -> tuple[SimpleNamespace, ...]:
        self.calls.append(("columns", count))
        return tuple(
            SimpleNamespace(button=lambda *_a, **_k: False) for _ in range(count)
        )


@pytest.fixture()
def fake_streamlit(monkeypatch: pytest.MonkeyPatch) -> FakeStreamlit:
    """Install a fake Streamlit module that captures WebUI calls."""

    fake = FakeStreamlit()
    monkeypatch.setattr(webui, "st", fake)
    return fake


def test_webui_navigation_prompt_and_command(
    fake_streamlit: FakeStreamlit, monkeypatch
):
    """WebUI run should drive navigation, prompts, and commands via the stub."""

    ui = webui.WebUI()

    visited = []
    monkeypatch.setattr(ui, "diagnostics_page", lambda: visited.append("diagnostics"))
    fake_streamlit._radio_value = "Diagnostics"

    ui.run()

    assert visited == ["diagnostics"]
    assert fake_streamlit.session_state["nav"] == "Diagnostics"

    nav_call = next(call for call in fake_streamlit.calls if call[0] == "sidebar_radio")
    assert nav_call[1] == "Navigation"
    assert "Diagnostics" in nav_call[2]

    fake_streamlit._selectbox_value = "Beta"
    choice = ui.ask_question("Pick option", choices=["Alpha", "Beta"], default="Alpha")
    assert choice == "Beta"
    assert fake_streamlit.calls[-1][:2] == ("selectbox", "Pick option")

    fake_streamlit._text_input_values = ["typed"]
    typed = ui.ask_question("Free text", default="prefill")
    assert typed == "typed"

    fake_streamlit._checkbox_value = False
    assert not ui.confirm_choice("Proceed?", default=True)

    ui.display_result("Highlight message", highlight=True)
    assert ("info", "Highlight message") in fake_streamlit.calls

    ui.display_result("Plain message")
    assert ("write", "Plain message") in fake_streamlit.calls

    executed: list[str] = []

    def sample_command(value: str) -> str:
        executed.append(value)
        return f"processed:{value}"

    result = ui._handle_command_errors(sample_command, "unused", "payload")
    assert result == "processed:payload"
    assert executed == ["payload"]
    assert all(call[0] != "error" for call in fake_streamlit.calls)


def test_webui_run_resets_invalid_navigation(
    fake_streamlit: FakeStreamlit, monkeypatch
):
    """Invalid stored navigation falls back to the default page on run."""

    ui = webui.WebUI()
    fake_streamlit.session_state["nav"] = "Nonexistent"

    visited: list[str] = []
    monkeypatch.setattr(ui, "onboarding_page", lambda: visited.append("onboarding"))

    ui.run()

    assert visited == ["onboarding"]
    assert fake_streamlit.session_state["nav"] == "Onboarding"

    nav_calls = [call for call in fake_streamlit.calls if call[0] == "sidebar_radio"]
    assert nav_calls, "Expected sidebar navigation to be invoked"
    _, label, options, index = nav_calls[0]
    assert label == "Navigation"
    assert options[0] == "Onboarding"
    assert index == 0


def test_command_error_feedback_surfaces_actionable_guidance(
    fake_streamlit: FakeStreamlit,
):
    """Command execution failures provide actionable Streamlit feedback."""

    ui = webui.WebUI()

    def failing_command(*_args: Any, **_kwargs: Any) -> None:
        raise FileNotFoundError(2, "missing", "requirements.md")

    result = ui._handle_command_errors(
        failing_command, "processing request", "requirements.md"
    )

    assert result is None

    error_messages = [call[1] for call in fake_streamlit.calls if call[0] == "error"]
    assert any("File not found" in message for message in error_messages)

    written_messages = [call[1] for call in fake_streamlit.calls if call[0] == "write"]
    assert any("Make sure the file exists" in message for message in written_messages)
    assert all(call[0] != "expander" for call in fake_streamlit.calls)
