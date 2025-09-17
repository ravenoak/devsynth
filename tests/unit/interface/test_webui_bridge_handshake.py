from __future__ import annotations

import importlib
from typing import Any

import pytest

from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [pytest.mark.fast]


class RaisingStr:
    """Object whose string conversion triggers the fallback branches."""

    def __str__(self) -> str:  # pragma: no cover - behavior exercised in tests
        raise RuntimeError("string conversion not supported")


def extract_plain(renderable: Any) -> str:
    """Return a plain representation from Rich renderables or strings."""

    plain = getattr(renderable, "plain", None)
    if plain is not None:
        return plain

    inner = getattr(renderable, "renderable", None)
    if inner is not None and inner is not renderable:
        inner_plain = getattr(inner, "plain", None)
        if inner_plain is not None:
            return inner_plain
        return str(inner)

    return str(renderable)


@pytest.fixture
def bridge_module():
    """Reload the bridge to provide a clean module instance for each test."""

    import devsynth.interface.webui_bridge as bridge

    importlib.reload(bridge)
    return bridge


def test_require_streamlit_uses_cached_stub(monkeypatch, bridge_module):
    """The optional dependency is not re-imported when already cached."""

    sentinel = object()
    monkeypatch.setattr(bridge_module, "st", sentinel, raising=False)

    def fail_import(name: str):  # pragma: no cover - should not execute
        raise AssertionError(f"importlib should not import {name}")

    monkeypatch.setattr("importlib.import_module", fail_import)

    bridge_module._require_streamlit()
    assert bridge_module.st is sentinel


def test_require_streamlit_imports_when_missing(monkeypatch, bridge_module):
    """The Streamlit module is imported once when the cache is empty."""

    fake_streamlit = make_streamlit_mock()
    calls: list[str] = []

    def fake_import(name: str):
        calls.append(name)
        return fake_streamlit

    monkeypatch.setattr("importlib.import_module", fake_import)

    bridge_module._require_streamlit()
    bridge_module._require_streamlit()

    assert calls == ["streamlit"], "Streamlit should be imported exactly once"
    assert bridge_module.st is fake_streamlit


def test_adjust_wizard_step_handles_invalid_inputs(bridge_module):
    """Directions and totals are validated and results are clamped."""

    adjust = bridge_module.WebUIBridge.adjust_wizard_step

    assert adjust(5, direction="next", total=0) == 0  # total defaults to 1
    assert adjust("bad", direction="back", total=4) == 0  # invalid current -> 0
    assert adjust("2", direction="invalid", total=3) == 2  # direction unchanged


def test_normalize_wizard_step_handles_varied_inputs(bridge_module):
    """Float, blank string, and bad values coerce to safe step indices."""

    normalize = bridge_module.WebUIBridge.normalize_wizard_step

    assert normalize(2.7, total=5) == 2
    assert normalize("   ", total=4) == 0
    assert normalize(object(), total=3) == 0


def test_progress_indicator_nested_tasks_cover_fallbacks(bridge_module):
    """Nested subtasks use safe placeholders and default statuses."""

    indicator = bridge_module.WebUIProgressIndicator("Task", 4)

    parent_id = indicator.add_subtask(RaisingStr(), total=4)
    parent = indicator._subtasks[parent_id]
    assert parent["description"] == "<subtask>"

    nested_id = indicator.add_nested_subtask(parent_id, RaisingStr(), total=4)
    nested = parent["nested_subtasks"][nested_id]
    assert nested["description"] == "<nested subtask>"

    status_history = []
    for _ in range(4):
        indicator.update_nested_subtask(parent_id, nested_id)
        status_history.append(nested["status"])

    assert status_history[0] == "Starting..."
    assert status_history[1] == "Processing..."
    assert status_history[-1] == "Almost done..."

    indicator.complete_nested_subtask(parent_id, nested_id)
    assert nested["completed"] is True
    assert nested["status"] == "Complete"

    indicator.complete_subtask(parent_id)
    assert parent["completed"] is True
    assert parent["current"] == parent["total"]


def test_progress_indicator_status_defaults_and_fallbacks(
    monkeypatch: pytest.MonkeyPatch, bridge_module
) -> None:
    """Status strings fall back to defaults and sanitize valid updates."""

    monkeypatch.setattr(
        bridge_module, "sanitize_output", lambda value: f"S:{value}", raising=False
    )
    indicator = bridge_module.WebUIProgressIndicator("Task", 100)

    indicator.update(description="Start")
    assert indicator._description == "S:Start"

    indicator.update(description=RaisingStr(), status=RaisingStr())
    assert indicator._description == "S:Start"
    assert indicator._status == "In progress..."

    for current, expected in [
        (0, "Starting..."),
        (25, "Processing..."),
        (50, "Halfway there..."),
        (75, "Almost done..."),
        (99, "Finalizing..."),
        (100, "Complete"),
    ]:
        indicator._current = current
        indicator.update(advance=0)
        assert indicator._status == expected

    parent_id = indicator.add_subtask("Parent", total=100)
    nested_id = indicator.add_nested_subtask(parent_id, "Nested", total=100)
    nested = indicator._subtasks[parent_id]["nested_subtasks"][nested_id]

    indicator.update_nested_subtask(parent_id, nested_id, description="Child")
    assert nested["description"] == "S:Child"

    indicator.update_nested_subtask(parent_id, nested_id, status=RaisingStr())
    assert nested["status"] == "In progress..."

    nested["current"] = 99
    indicator.update_nested_subtask(parent_id, nested_id, advance=0)
    assert nested["status"] == "Finalizing..."

    nested["current"] = 100
    indicator.update_nested_subtask(parent_id, nested_id, advance=0)
    assert nested["status"] == "Complete"

    indicator.update_nested_subtask("missing", nested_id, advance=0)


def test_display_result_routes_messages_and_sanitizes(monkeypatch, bridge_module):
    """Messages route through the appropriate Streamlit APIs and are sanitized."""

    fake_streamlit = make_streamlit_mock()
    monkeypatch.setattr(bridge_module, "st", fake_streamlit, raising=False)

    bridge = bridge_module.WebUIBridge()
    progress = bridge.create_progress("Loading", total=10)
    assert isinstance(progress, bridge_module.WebUIProgressIndicator)

    bridge.display_result("<info>", message_type="info")
    bridge.display_result("<warn>", message_type="warning")
    bridge.display_result("<success>", message_type="success")
    bridge.display_result("<highlight>", highlight=True)

    assert fake_streamlit.info.call_count == 2  # info + highlight
    fake_streamlit.warning.assert_called_once()
    fake_streamlit.success.assert_called_once()

    expected_messages = [
        bridge_module.sanitize_output("<info>"),
        bridge_module.sanitize_output("<warn>"),
        bridge_module.sanitize_output("<success>"),
        bridge_module.sanitize_output("<highlight>"),
    ]
    observed = [extract_plain(message) for message in bridge.messages]

    for expected, actual in zip(expected_messages, observed, strict=True):
        assert expected in actual


def test_display_result_error_branch_records_message(monkeypatch, bridge_module):
    """Error messages surface via ``st.error`` and are stored for diagnostics."""

    fake_streamlit = make_streamlit_mock()
    monkeypatch.setattr(bridge_module, "st", fake_streamlit, raising=False)

    bridge = bridge_module.WebUIBridge()
    bridge.display_result("Boom", message_type="error")

    fake_streamlit.error.assert_called_once()
    assert any("Boom" in extract_plain(message) for message in bridge.messages)


def test_bridge_prompt_helpers_return_defaults(bridge_module):
    """Prompt helpers simply echo defaults in the lightweight implementation."""

    bridge = bridge_module.WebUIBridge()

    assert bridge.ask_question("Question?", default=42) == "42"
    assert bridge.ask_question("Empty?", default=None) == ""
    assert bridge.confirm_choice("Confirm?", default=True) is True
