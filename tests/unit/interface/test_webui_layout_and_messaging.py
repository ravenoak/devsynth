from __future__ import annotations

import importlib
import sys
from typing import Tuple

import pytest

from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [pytest.mark.usefixtures("force_webui_available")]


@pytest.fixture
def webui_module(monkeypatch: pytest.MonkeyPatch) -> tuple[object, object]:
    """Reload ``devsynth.interface.webui`` with a fresh Streamlit stub."""

    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    return webui, st


@pytest.mark.fast
def test_get_layout_config_respects_breakpoints(
    webui_module: tuple[object, object],
) -> None:
    webui, st = webui_module
    ui = webui.WebUI()

    st.session_state["screen_width"] = 640
    st.session_state.screen_width = 640
    config = ui.get_layout_config()
    assert config["columns"] == 1
    assert config["is_mobile"] is True

    st.session_state["screen_width"] = 800
    st.session_state.screen_width = 800
    config = ui.get_layout_config()
    assert config["columns"] == 2
    assert config["is_mobile"] is False

    st.session_state["screen_width"] = 1400
    st.session_state.screen_width = 1400
    config = ui.get_layout_config()
    assert config["columns"] == 3
    assert config["sidebar_width"] == "20%"


@pytest.mark.fast
def test_ask_question_and_confirm_choice_use_streamlit_controls(
    webui_module: tuple[object, object],
) -> None:
    webui, st = webui_module
    ui = webui.WebUI()

    st.selectbox.return_value = "beta"
    answer = ui.ask_question("Pick", choices=["alpha", "beta"], default="beta")
    st.selectbox.assert_called_once_with("Pick", ["alpha", "beta"], index=1, key="Pick")
    assert answer == "beta"

    st.selectbox.reset_mock()
    st.text_input.return_value = "typed"
    answer = ui.ask_question("Describe")
    st.text_input.assert_called_once_with("Describe", value="", key="Describe")
    assert answer == "typed"

    st.checkbox.return_value = True
    assert ui.confirm_choice("Proceed?", default=True) is True
    st.checkbox.assert_called_once_with("Proceed?", value=True, key="Proceed?")


@pytest.mark.fast
def test_display_result_message_types_provide_guidance(
    webui_module: tuple[object, object],
) -> None:
    webui, st = webui_module
    ui = webui.WebUI()

    ui.display_result("File not found: config.yaml", message_type="error")
    st.error.assert_called_once_with(
        webui.sanitize_output("File not found: config.yaml")
    )
    markdown_texts = [call.args[0] for call in st.markdown.call_args_list]
    assert any("Suggestions" in text for text in markdown_texts)
    assert any("Documentation" in text for text in markdown_texts)
    assert any("file_handling.html" in text for text in markdown_texts)

    st.markdown.reset_mock()

    ui.display_result("Heads up", message_type="warning")
    assert st.warning.call_args[0][0] == webui.sanitize_output("Heads up")

    ui.display_result("Great job", message_type="success")
    assert st.success.call_args[0][0] == webui.sanitize_output("Great job")

    ui.display_result("FYI", message_type="info")
    assert st.info.call_args[0][0] == webui.sanitize_output("FYI")


@pytest.mark.fast
def test_display_result_markup_and_keyword_routing(
    webui_module: tuple[object, object],
) -> None:
    webui, st = webui_module
    ui = webui.WebUI()

    ui.display_result("[bold]Important[/bold]")
    st.markdown.assert_called_with("**Important**", unsafe_allow_html=True)

    st.markdown.reset_mock()

    ui.display_result("ERROR: Permission denied")
    st.error.assert_called_with("ERROR: Permission denied")
    permission_calls = [call.args[0] for call in st.markdown.call_args_list]
    assert any("Permission Issues" in text for text in permission_calls)

    st.markdown.reset_mock()

    ui.display_result("WARNING: Check configuration")
    st.warning.assert_called_with("WARNING: Check configuration")

    ui.display_result("SUCCESS Operation complete")
    ui.display_result("The run completed successfully")
    success_messages = [call.args[0] for call in st.success.call_args_list]
    assert "SUCCESS Operation complete" in success_messages
    assert "The run completed successfully" in success_messages

    ui.display_result("# Heading One")
    st.header.assert_called_with("Heading One")

    ui.display_result("## Heading Two")
    st.subheader.assert_called_with("Heading Two")

    ui.display_result("### Heading Three")
    st.markdown.assert_called_with("**Heading Three**")

    ui.display_result("Focus here", highlight=True)
    st.info.assert_called_with(webui.sanitize_output("Focus here"))


@pytest.mark.fast
@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("File not found", "file_not_found"),
        ("Permission denied", "permission_denied"),
        ("Invalid parameter", "invalid_parameter"),
        ("Invalid format", "invalid_format"),
        ("Missing key", "key_error"),
        ("Type error", "type_error"),
        ("TypeError", "type_error"),
        ("Configuration error", "config_error"),
        ("Connection error", "connection_error"),
        ("API error", "api_error"),
        ("Validation error", "validation_error"),
        ("Syntax error", "syntax_error"),
        ("Import error", "import_error"),
        ("Completely different", ""),
    ],
)
def test_get_error_type_matches_keywords(
    webui_module: tuple[object, object], message: str, expected: str
) -> None:
    webui, _ = webui_module
    ui = webui.WebUI()

    assert ui._get_error_type(message) == expected


@pytest.mark.fast
def test_error_suggestions_and_docs_cover_known_and_unknown(
    webui_module: tuple[object, object],
) -> None:
    webui, _ = webui_module
    ui = webui.WebUI()

    suggestions = ui._get_error_suggestions("permission_denied")
    assert any("permissions" in suggestion.lower() for suggestion in suggestions)
    assert ui._get_error_suggestions("unknown") == []

    links = ui._get_documentation_links("config_error")
    assert "Configuration Guide" in links
    assert ui._get_documentation_links("unknown") == {}
