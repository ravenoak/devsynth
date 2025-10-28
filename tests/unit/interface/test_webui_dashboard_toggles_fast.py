"""Focused coverage for WebUI layout toggles and error guidance."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Tuple
from collections.abc import Iterator
from unittest.mock import MagicMock, call

import pytest

from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def reloaded_webui(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[object, object]]:
    """Reload ``devsynth.interface.webui`` with a deterministic Streamlit stub."""

    st = _mock_streamlit()
    st.markdown.reset_mock()
    st.error.reset_mock()

    stub_argon2 = ModuleType("argon2")
    stub_argon2.PasswordHasher = MagicMock()
    stub_exceptions = ModuleType("argon2.exceptions")

    class _VerifyMismatchError(Exception):
        pass

    stub_exceptions.VerifyMismatchError = _VerifyMismatchError
    stub_argon2.exceptions = stub_exceptions
    monkeypatch.setitem(sys.modules, "argon2", stub_argon2)
    monkeypatch.setitem(sys.modules, "argon2.exceptions", stub_exceptions)

    stub_config = ModuleType("devsynth.config")
    stub_config.load_project_config = MagicMock(return_value={})
    stub_config.save_config = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.config", stub_config)

    stub_yaml = ModuleType("yaml")
    stub_yaml.safe_dump = MagicMock(return_value="{}")
    monkeypatch.setitem(sys.modules, "yaml", stub_yaml)

    stub_output_formatter = ModuleType("devsynth.interface.output_formatter")

    class _Formatter:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def format_message(
            self,
            message: str,
            *,
            message_type: str | None = None,
            highlight: bool = False,
        ) -> str:
            return message

    stub_output_formatter.OutputFormatter = _Formatter
    monkeypatch.setitem(
        sys.modules, "devsynth.interface.output_formatter", stub_output_formatter
    )

    stub_shared_bridge = ModuleType("devsynth.interface.shared_bridge")

    class _SharedBridgeMixin:
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)  # type: ignore[misc]
            self.formatter = _Formatter(None)

        def _format_for_output(
            self,
            message: str,
            *,
            highlight: bool = False,
            message_type: str | None = None,
        ) -> str:
            return message

    stub_shared_bridge.SharedBridgeMixin = _SharedBridgeMixin
    monkeypatch.setitem(
        sys.modules, "devsynth.interface.shared_bridge", stub_shared_bridge
    )

    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    try:
        yield webui, st
    finally:
        sys.modules.pop("streamlit", None)
        sys.modules.pop("argon2", None)
        sys.modules.pop("argon2.exceptions", None)
        sys.modules.pop("devsynth.config", None)
        sys.modules.pop("yaml", None)
        sys.modules.pop("devsynth.interface.output_formatter", None)
        sys.modules.pop("devsynth.interface.shared_bridge", None)


@pytest.mark.fast
def test_webui_layout_breakpoints_toggle_between_modes(
    reloaded_webui: tuple[object, object],
) -> None:
    """Mobile, tablet, and desktop dashboards set distinct layout toggles."""

    webui, st = reloaded_webui
    ui = webui.WebUI()

    st.session_state.screen_width = 640
    mobile = ui.get_layout_config()
    assert mobile["columns"] == 1
    assert mobile["is_mobile"] is True
    assert mobile["sidebar_width"] == "100%"

    st.session_state.screen_width = 800
    tablet = ui.get_layout_config()
    assert tablet["columns"] == 2
    assert tablet["is_mobile"] is False
    assert tablet["sidebar_width"] == "30%"

    st.session_state.screen_width = 1280
    desktop = ui.get_layout_config()
    assert desktop["columns"] == 3
    assert desktop["is_mobile"] is False
    assert desktop["sidebar_width"] == "20%"


@pytest.mark.fast
def test_webui_error_guidance_surfaces_suggestions_and_docs(
    reloaded_webui: tuple[object, object],
) -> None:
    """Error rendering includes guidance and documentation links for dashboard users."""

    webui, st = reloaded_webui
    ui = webui.WebUI()

    ui.display_result("ERROR: File not found: config.yaml", message_type="error")

    assert st.error.call_args[0][0] == "ERROR: File not found: config.yaml"

    markdown_calls = [call.args[0] for call in st.markdown.call_args_list]
    assert "**Suggestions:**" in markdown_calls
    assert any(
        line.startswith("- Check that the file path is correct")
        for line in markdown_calls
    )
    assert "**Documentation:**" in markdown_calls
    assert any(line.startswith("- [File Handling Guide]") for line in markdown_calls)
