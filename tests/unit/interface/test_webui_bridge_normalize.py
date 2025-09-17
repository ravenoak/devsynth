"""Additional coverage for WebUI bridge helpers."""

from __future__ import annotations

import importlib
import sys

import pytest

from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("force_webui_available"),
]


@pytest.fixture
def bridge_module(monkeypatch):
    """Reload the bridge with a mocked Streamlit dependency."""

    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui_bridge as bridge

    importlib.reload(bridge)
    return bridge


def test_normalize_wizard_step_handles_varied_inputs(bridge_module):
    """Values are coerced to valid step indices and clamped to bounds."""

    normalize = bridge_module.WebUIBridge.normalize_wizard_step

    assert normalize(" 2 ", total=5) == 2
    assert normalize("4.9", total=4) == 3
    assert normalize(None, total=3) == 0
    assert normalize("", total=3) == 0
    assert normalize("not-a-number", total=3) == 0


def test_normalize_wizard_step_invalid_total_defaults_to_zero(bridge_module):
    """Non-positive totals fall back to a single-step wizard."""

    normalize = bridge_module.WebUIBridge.normalize_wizard_step
    assert normalize(5, total=0) == 0
    assert normalize(-1, total=-2) == 0


def test_progress_indicator_rejects_missing_parent(bridge_module):
    """Adding nested subtasks without a parent yields an empty identifier."""

    indicator = bridge_module.WebUIProgressIndicator("Task", 100)
    assert indicator.add_nested_subtask("missing", "Nested") == ""


def test_display_result_routes_messages_to_streamlit(bridge_module):
    """Successful messages use the Streamlit success channel and are stored."""

    streamlit_stub = sys.modules["streamlit"]
    bridge = bridge_module.WebUIBridge()

    bridge.display_result("All good", message_type="success")

    streamlit_stub.success.assert_called_once()
    assert "All good" in bridge.messages[0]
