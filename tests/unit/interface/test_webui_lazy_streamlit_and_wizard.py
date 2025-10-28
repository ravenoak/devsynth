"""Focused coverage for WebUI lazy loading and wizard clamps."""

from __future__ import annotations

import importlib
import sys
from typing import List

import pytest

from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("force_webui_available")]


@pytest.fixture
def reloaded_webui(monkeypatch: pytest.MonkeyPatch):
    """Reload ``devsynth.interface.webui`` with a fresh Streamlit stub."""

    streamlit_stub = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_stub)

    import devsynth.interface.webui as webui

    module = importlib.reload(webui)
    return module, streamlit_stub


@pytest.fixture
def reloaded_webui_bridge(monkeypatch: pytest.MonkeyPatch):
    """Reload ``devsynth.interface.webui_bridge`` with a Streamlit stub."""

    streamlit_stub = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_stub)

    import devsynth.interface.webui_bridge as bridge

    module = importlib.reload(bridge)
    return module, streamlit_stub


def test_lazy_streamlit_import_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """Feature: webui_core.feature Scenario: Lazy Streamlit loader caches module."""

    from devsynth.interface import webui

    call_log: list[str] = []
    streamlit_stub = make_streamlit_mock()

    original_import = importlib.import_module

    def fake_import(name: str, package: str | None = None):
        call_log.append(name)
        if name == "streamlit":
            return streamlit_stub
        return original_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    module = importlib.reload(webui)
    module._STREAMLIT = None
    module.st.selectbox("Question", ["a", "b"], key="question")
    module.st.text_input("Prompt", key="prompt")

    assert call_log.count("streamlit") == 1
    module.st.selectbox("Another", ["x", "y"], key="another")
    assert call_log.count("streamlit") == 1


def test_display_result_translates_markup_to_html(
    reloaded_webui, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Feature: webui_rendering_invariants.feature Scenario: Rich markup renders via markdown."""

    module, streamlit_stub = reloaded_webui
    recorded: list[str] = []

    def echo(text: str) -> str:
        recorded.append(text)
        return text

    monkeypatch.setattr(module, "sanitize_output", echo)

    ui = module.WebUI()
    ui.display_result("[yellow]Heads up[/yellow]")

    streamlit_stub.markdown.assert_called_with(
        '<span style="color:orange">Heads up</span>', unsafe_allow_html=True
    )
    assert recorded == ["[yellow]Heads up[/yellow]"]


def test_normalize_step_logs_warning_on_invalid_value(
    reloaded_webui_bridge, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Feature: webui_gather_wizard.feature Scenario: Invalid wizard values clamp to zero."""

    module, _ = reloaded_webui_bridge
    warnings: list[str] = []

    monkeypatch.setattr(
        module.logger, "warning", lambda message: warnings.append(message)
    )

    result = module.WebUIBridge.normalize_wizard_step("not-a-number", total=3)

    assert result == 0
    assert any("Failed to normalize step value" in entry for entry in warnings)


def test_adjust_step_warns_on_invalid_direction(
    reloaded_webui_bridge, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Feature: webui_gather_wizard.feature Scenario: Invalid direction preserves current step."""

    module, _ = reloaded_webui_bridge
    warnings: list[str] = []

    monkeypatch.setattr(
        module.logger, "warning", lambda message: warnings.append(message)
    )

    step = module.WebUIBridge.adjust_wizard_step("bad", direction="sideways", total="0")
    assert step == 0
    assert len(warnings) >= 2  # total coercion and direction warnings
