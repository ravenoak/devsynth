"""Targeted coverage for :mod:`devsynth.interface.webui` gaps."""

from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.fast


@pytest.fixture
def webui_under_test(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Reload ``devsynth.interface.webui`` with a rich Streamlit double."""

    from tests.unit.interface.test_webui_enhanced import _mock_streamlit

    fake_streamlit = _mock_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    import devsynth.interface.webui as webui

    module = importlib.reload(webui)
    return SimpleNamespace(module=module, streamlit=fake_streamlit)


def test_ask_question_selectbox_indexes_default(
    webui_under_test: SimpleNamespace,
) -> None:
    """Choice prompts honour defaults even when not first in the list.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module
    ui = webui.WebUI()

    result = ui.ask_question(
        "Choose", choices=("alpha", "beta", "gamma"), default="beta"
    )

    assert result == webui_under_test.streamlit.selectbox.return_value
    webui_under_test.streamlit.selectbox.assert_called_once_with(
        "Choose", ["alpha", "beta", "gamma"], index=1, key="Choose"
    )


def test_ask_question_text_input_when_no_choices(
    webui_under_test: SimpleNamespace,
) -> None:
    """Freeform prompts fall back to ``st.text_input`` with sanitized default.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module
    ui = webui.WebUI()

    result = ui.ask_question("Your name", default="Ada")

    assert result == webui_under_test.streamlit.text_input.return_value
    webui_under_test.streamlit.text_input.assert_called_once_with(
        "Your name", value="Ada", key="Your name"
    )


def test_confirm_choice_returns_checkbox_value(
    webui_under_test: SimpleNamespace,
) -> None:
    """Confirmation prompts proxy ``st.checkbox`` directly.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module
    ui = webui.WebUI()

    webui_under_test.streamlit.checkbox.return_value = False
    assert ui.confirm_choice("Proceed?", default=True) is False
    webui_under_test.streamlit.checkbox.assert_called_once_with(
        "Proceed?", value=True, key="Proceed?"
    )


def test_display_result_error_surfaces_suggestions_and_docs(
    monkeypatch: pytest.MonkeyPatch, webui_under_test: SimpleNamespace
) -> None:
    """Error messages surface actionable suggestions and documentation links.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module
    ui = webui.WebUI()

    monkeypatch.setattr(ui, "_get_error_type", lambda message: "file_not_found")
    monkeypatch.setattr(
        ui,
        "_get_error_suggestions",
        lambda _: ["Check the filename", "Verify the path"],
    )
    monkeypatch.setattr(
        ui,
        "_get_documentation_links",
        lambda _: {"Troubleshooting": "https://docs/tips"},
    )

    ui.display_result("ERROR: File not found: config.yml", message_type="error")

    webui_under_test.streamlit.error.assert_called_once_with(
        "ERROR: File not found: config.yml"
    )
    markdown_calls = [
        call[0][0] for call in webui_under_test.streamlit.markdown.call_args_list
    ]
    assert "**Suggestions:**" in markdown_calls[0]
    assert "- Check the filename" in markdown_calls[1]
    assert "**Documentation:**" in markdown_calls[3]
    assert "- [Troubleshooting](https://docs/tips)" in markdown_calls[4]


def test_render_traceback_expander_renders_code(
    webui_under_test: SimpleNamespace,
) -> None:
    """Traceback rendering uses an expander and syntax-highlighted code block.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module
    ui = webui.WebUI()

    ui._render_traceback("Traceback: boom")

    webui_under_test.streamlit.expander.assert_called_once_with(
        "Technical Details (for debugging)"
    )
    webui_under_test.streamlit.code.assert_called_once_with(
        "Traceback: boom", language="python"
    )


def test_ui_progress_sanitizes_updates(
    monkeypatch: pytest.MonkeyPatch, webui_under_test: SimpleNamespace
) -> None:
    """Progress updates sanitize descriptions and status text.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module

    sanitized: list[str] = []

    def spy_sanitize(value: str) -> str:
        sanitized.append(value)
        return f"safe::{value}"

    monkeypatch.setattr(webui, "sanitize_output", spy_sanitize)

    ui = webui.WebUI()
    progress = ui.create_progress("<b>Work</b>", total=10)

    progress.update(advance=5, description="desc", status="status")

    assert sanitized == ["<b>Work</b>", "desc", "status"]
    assert progress._description == "safe::desc"
    assert progress._status == "safe::status"


def test_ensure_router_memoizes_instance(
    monkeypatch: pytest.MonkeyPatch, webui_under_test: SimpleNamespace
) -> None:
    """Router construction runs once and cached instance is reused.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module

    created = []

    class DummyRouter:
        def __init__(self, owner, items) -> None:
            created.append((owner, tuple(items)))

        def run(self) -> None:  # pragma: no cover - invoked in other tests
            return None

    monkeypatch.setattr(webui, "Router", DummyRouter)

    ui = webui.WebUI()
    first = ui._ensure_router()
    second = ui._ensure_router()

    assert first is second
    assert len(created) == 1


def test_run_handles_page_config_errors(
    monkeypatch: pytest.MonkeyPatch, webui_under_test: SimpleNamespace
) -> None:
    """``run`` surfaces configuration errors via ``display_result`` and aborts early.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module
    ui = webui.WebUI()

    boom = RuntimeError("cannot configure")
    webui_under_test.streamlit.set_page_config.side_effect = boom
    ui.display_result = MagicMock()

    ui.run()

    ui.display_result.assert_called_once()
    (message,) = ui.display_result.call_args[0]
    assert "ERROR" in message
    assert "cannot configure" in message


def test_run_renders_layout_and_router(
    monkeypatch: pytest.MonkeyPatch, webui_under_test: SimpleNamespace
) -> None:
    """Successful ``run`` execution wires JS bridge, sidebar, and router.

    ReqID: coverage-webui-targeted
    """

    webui = webui_under_test.module

    router_run = []

    class DummyRouter:
        def __init__(self, owner, items) -> None:
            self.owner = owner
            self.items = items

        def run(self) -> None:
            router_run.append(self.owner)

    monkeypatch.setattr(webui, "Router", DummyRouter)

    html_mock = webui_under_test.streamlit.components.v1.html
    html_mock.side_effect = None

    ui = webui.WebUI()
    ui.run()

    webui_under_test.streamlit.set_page_config.assert_called_once()
    assert html_mock.called, "Expected Streamlit components HTML injection"
    assert router_run == [ui], "Router.run should execute once"
    state = webui_under_test.streamlit.session_state
    assert state.screen_width == 1200
    assert state.screen_height == 800
