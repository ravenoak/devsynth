"""Behavioral tests for WebUI progress tracking utilities."""

from __future__ import annotations

import importlib

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui_bridge
from tests.fixtures.fake_streamlit import FakeSessionState


class _SanitizeSpy:
    """Callable spy that tracks sanitize invocations and supports failures."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail_on: set[str] = set()

    def __call__(self, value: str) -> str:
        self.calls.append(value)
        if value in self.fail_on:
            raise ValueError("sanitize failure for testing")
        return f"sanitized::{value}"


@pytest.fixture()
def sanitize_spy(monkeypatch: pytest.MonkeyPatch) -> _SanitizeSpy:
    spy = _SanitizeSpy()
    monkeypatch.setattr(webui_bridge, "sanitize_output", spy)
    return spy


def _assert_default_status_cycle(
    indicator: webui_bridge.WebUIProgressIndicator,
) -> None:
    """Advance ``indicator`` through threshold updates asserting status text."""

    indicator.update(advance=15)
    assert indicator._status == "Starting..."

    indicator.update(advance=0)
    assert indicator._status == "Processing..."

    indicator.update(advance=25)
    indicator.update(advance=0)
    assert indicator._status == "Halfway there..."

    indicator.update(advance=25)
    indicator.update(advance=0)
    assert indicator._status == "Almost done..."

    indicator.update(advance=24)
    indicator.update(advance=0)
    assert indicator._status == "Finalizing..."

    indicator.update(advance=1)
    indicator.update(advance=0)
    assert indicator._status == "Complete"


def _install_tagging_sanitizer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch sanitizer hooks with a tagging implementation for assertions."""

    def _tag(value: str) -> str:
        return f"<sanitized::{value}>"

    monkeypatch.setattr(webui_bridge, "sanitize_output", _tag)

    ux_bridge = importlib.import_module("devsynth.interface.ux_bridge")
    monkeypatch.setattr(ux_bridge, "sanitize_output", _tag)

    shared_bridge = importlib.import_module("devsynth.interface.shared_bridge")
    monkeypatch.setattr(shared_bridge, "sanitize_output", _tag)

    output_formatter = importlib.import_module("devsynth.interface.output_formatter")
    monkeypatch.setattr(output_formatter, "global_sanitize_output", _tag)


def _extract_payload_text(payload: object) -> str:
    """Return the textual payload from Rich objects used in the WebUI bridge."""

    plain = getattr(payload, "plain", None)
    if plain is not None:
        return plain

    renderable = getattr(payload, "renderable", None)
    if renderable is not None:
        return _extract_payload_text(renderable)

    return str(payload)


@pytest.mark.fast
def test_progress_indicator_update_paths(sanitize_spy: _SanitizeSpy) -> None:
    """``update`` sanitizes supplied text and cycles default status thresholds.

    ReqID: N/A
    """

    indicator = webui_bridge.WebUIProgressIndicator("initial", 100)

    indicator.update(description="desc-1", status="status-1", advance=10)
    assert sanitize_spy.calls[:2] == ["desc-1", "status-1"]
    assert indicator._description == "sanitized::desc-1"
    assert indicator._status == "sanitized::status-1"

    indicator.update(description="desc-2", advance=0)
    assert sanitize_spy.calls[2] == "desc-2"
    assert indicator._description == "sanitized::desc-2"
    assert indicator._status == "Starting..."

    indicator.update(status="status-2", advance=0)
    assert sanitize_spy.calls[3] == "status-2"
    assert indicator._status == "sanitized::status-2"

    indicator.update(description="desc-3", status="status-3", advance=0)
    assert sanitize_spy.calls[4:6] == ["desc-3", "status-3"]
    assert indicator._description == "sanitized::desc-3"
    assert indicator._status == "sanitized::status-3"

    _assert_default_status_cycle(indicator)
    assert sanitize_spy.calls == [
        "desc-1",
        "status-1",
        "desc-2",
        "status-2",
        "desc-3",
        "status-3",
    ]


@pytest.mark.fast
def test_progress_indicator_subtasks_and_nested_operations(
    sanitize_spy: _SanitizeSpy,
) -> None:
    """Subtask lifecycle sanitizes text, handles fallbacks, and ignores invalid IDs.

    ReqID: N/A
    """

    indicator = webui_bridge.WebUIProgressIndicator("main", 100)

    task_id = indicator.add_subtask("alpha", total=10)
    assert sanitize_spy.calls[-1] == "alpha"
    assert indicator._subtasks[task_id]["description"] == "sanitized::alpha"

    indicator.update_subtask(task_id, advance=2, description="beta")
    assert sanitize_spy.calls[-1] == "beta"
    assert indicator._subtasks[task_id]["current"] == 2
    assert indicator._subtasks[task_id]["description"] == "sanitized::beta"

    sanitize_spy.fail_on.add("bad-desc")
    indicator.update_subtask(task_id, description="bad-desc")
    assert indicator._subtasks[task_id]["description"] == "sanitized::beta"
    sanitize_spy.fail_on.remove("bad-desc")

    before = list(sanitize_spy.calls)
    indicator.update_subtask("missing", description="gamma")
    assert sanitize_spy.calls == before

    nested_id = indicator.add_nested_subtask(task_id, "nested", total=4, status="init")
    assert sanitize_spy.calls[-1] == "nested"
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["description"] == "sanitized::nested"
    assert nested["status"] == "init"

    indicator.update_nested_subtask(
        task_id, nested_id, advance=1, description="n-desc", status="n-status"
    )
    assert sanitize_spy.calls[-2:] == ["n-desc", "n-status"]
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["current"] == 1
    assert nested["description"] == "sanitized::n-desc"
    assert nested["status"] == "sanitized::n-status"

    sanitize_spy.fail_on.add("bad-status")
    indicator.update_nested_subtask(task_id, nested_id, status="bad-status")
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["status"] == "In progress..."
    sanitize_spy.fail_on.remove("bad-status")

    before = list(sanitize_spy.calls)
    indicator.update_nested_subtask("missing", nested_id, description="skip")
    indicator.update_nested_subtask(task_id, "missing", description="skip")
    assert sanitize_spy.calls == before

    sanitize_spy.fail_on.add("fail-sub")
    fallback_id = indicator.add_subtask("fail-sub")
    assert indicator._subtasks[fallback_id]["description"] == "<subtask>"

    sanitize_spy.fail_on.add("fail-nested")
    fallback_nested = indicator.add_nested_subtask(fallback_id, "fail-nested")
    assert fallback_nested
    nested = indicator._subtasks[fallback_id]["nested_subtasks"][fallback_nested]
    assert nested["description"] == "<nested subtask>"

    missing_nested = indicator.add_nested_subtask("missing", "noop")
    assert missing_nested == ""

    indicator.complete_nested_subtask(task_id, nested_id)
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["completed"] is True
    assert nested["current"] == nested["total"]
    assert nested["status"] == "Complete"

    pending_nested = indicator.add_nested_subtask(task_id, "pending")
    assert pending_nested
    assert sanitize_spy.calls[-1] == "pending"
    indicator.complete_subtask(task_id)
    subtask = indicator._subtasks[task_id]
    assert subtask["completed"] is True
    assert subtask["current"] == subtask["total"]
    for nested in subtask.get("nested_subtasks", {}).values():
        assert nested["completed"] is True
        assert nested["status"] == "Complete"

    indicator.complete_subtask("missing")
    indicator.complete_nested_subtask("missing", "missing")

    assert sanitize_spy.calls == [
        "alpha",
        "beta",
        "bad-desc",
        "nested",
        "n-desc",
        "n-status",
        "bad-status",
        "fail-sub",
        "fail-nested",
        "pending",
    ]


@pytest.mark.medium
def test_display_result_routes_and_message_capture(
    streamlit_bridge_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Streamlit display paths sanitize output and record formatted messages."""

    _install_tagging_sanitizer(monkeypatch)
    bridge = webui_bridge.WebUIBridge()

    bridge.display_result("error-text", message_type="error")
    error_payload = streamlit_bridge_stub.error_calls[-1]
    assert _extract_payload_text(error_payload) == "<sanitized::error-text>"
    assert bridge.messages[-1] is error_payload

    bridge.display_result("success-text", message_type="success")
    success_payload = streamlit_bridge_stub.success_calls[-1]
    assert _extract_payload_text(success_payload) == "<sanitized::success-text>"
    assert bridge.messages[-1] is success_payload

    bridge.display_result("info-text", highlight=True, message_type="info")
    info_payload = streamlit_bridge_stub.info_calls[-1]
    assert _extract_payload_text(info_payload) == "<sanitized::info-text>"
    assert bridge.messages[-1] is info_payload


@pytest.mark.medium
def test_create_progress_thresholds_use_default_status(
    streamlit_bridge_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Progress indicators created by the bridge honor default status updates."""

    _install_tagging_sanitizer(monkeypatch)
    bridge = webui_bridge.WebUIBridge()

    indicator = bridge.create_progress("initial", total=100)
    indicator.update(description="phase-1", status="custom", advance=10)
    assert indicator._description == "<sanitized::phase-1>"
    assert indicator._status == "<sanitized::custom>"

    _assert_default_status_cycle(indicator)


@pytest.mark.medium
def test_wizard_step_bounds_and_session_state_validation(
    streamlit_bridge_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Wizard helpers clamp invalid inputs and enforce session state availability."""

    _install_tagging_sanitizer(monkeypatch)
    bridge = webui_bridge.WebUIBridge()

    assert bridge.adjust_wizard_step(0, direction="next", total=-5) == 0
    assert bridge.adjust_wizard_step("2", direction="back", total=3) == 1
    assert bridge.adjust_wizard_step(1, direction="sideways", total=2) == 1

    streamlit_bridge_stub.session_state = None
    with pytest.raises(DevSynthError):
        bridge.get_wizard_manager("wizard", steps=3)

    streamlit_bridge_stub.session_state = FakeSessionState()
    manager = bridge.create_wizard_manager(
        streamlit_bridge_stub.session_state, "wizard", steps=2
    )

    wizard_state_manager = importlib.import_module(
        "devsynth.interface.wizard_state_manager"
    )
    assert isinstance(manager, wizard_state_manager.WizardStateManager)


@pytest.mark.fast
def test_require_streamlit_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_require_streamlit`` raises ``DevSynthError`` when import fails.

    ReqID: N/A
    """

    monkeypatch.setattr(webui_bridge, "st", None)
    seen = []

    def fake_import(name: str):
        seen.append(name)
        raise ImportError("no module named streamlit")

    monkeypatch.setattr(importlib, "import_module", fake_import)
    with pytest.raises(DevSynthError):
        webui_bridge._require_streamlit()
    assert seen == ["streamlit"]


@pytest.mark.fast
def test_adjust_wizard_step_edges() -> None:
    """Edge cases clamp wizard step navigation within valid bounds.

    ReqID: N/A
    """

    adjust = webui_bridge.WebUIBridge.adjust_wizard_step

    assert adjust(0, direction="back", total=0) == 0
    assert adjust(0, direction="next", total=0) == 0
    assert adjust("2", direction="next", total=5) == 3
    assert adjust("abc", direction="back", total=3) == 0
    assert adjust(2, direction="back", total=5) == 1
    assert adjust(2, direction="next", total=3) == 2
    assert adjust(0, direction="back", total=3) == 0
    assert adjust(1, direction="next", total=2.5) == 0
    assert adjust(1, direction="stay", total=2) == 1


@pytest.mark.fast
def test_nested_subtask_default_status_cycle(sanitize_spy: _SanitizeSpy) -> None:
    """Nested subtasks update status text according to default progress thresholds.

    ReqID: N/A
    """

    indicator = webui_bridge.WebUIProgressIndicator("root", 100)

    subtask_id = indicator.add_subtask("outer", total=100)
    nested_id = indicator.add_nested_subtask(subtask_id, "inner", total=100)

    # Descriptions are sanitized through the shared spy helper.
    assert sanitize_spy.calls[-2:] == ["outer", "inner"]

    nested = indicator._subtasks[subtask_id]["nested_subtasks"][nested_id]
    statuses = [nested["status"]]

    indicator.update_nested_subtask(subtask_id, nested_id, advance=25)
    indicator.update_nested_subtask(subtask_id, nested_id, advance=0)
    statuses.append(nested["status"])

    indicator.update_nested_subtask(subtask_id, nested_id, advance=25)
    indicator.update_nested_subtask(subtask_id, nested_id, advance=0)
    statuses.append(nested["status"])

    indicator.update_nested_subtask(subtask_id, nested_id, advance=25)
    indicator.update_nested_subtask(subtask_id, nested_id, advance=0)
    statuses.append(nested["status"])

    indicator.update_nested_subtask(subtask_id, nested_id, advance=24)
    indicator.update_nested_subtask(subtask_id, nested_id, advance=0)
    statuses.append(nested["status"])

    indicator.update_nested_subtask(subtask_id, nested_id, advance=1)
    indicator.update_nested_subtask(subtask_id, nested_id, advance=0)
    statuses.append(nested["status"])

    assert statuses == [
        "Starting...",
        "Processing...",
        "Halfway there...",
        "Almost done...",
        "Finalizing...",
        "Complete",
    ]


@pytest.mark.fast
def test_webui_bridge_display_result_routes_and_sanitizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``display_result`` routes by message type and records sanitized payloads.

    ReqID: N/A
    """

    class StreamlitRecorder:
        def __init__(self) -> None:
            self.calls = []

        def error(self, value):
            self.calls.append(("error", value))

        def warning(self, value):
            self.calls.append(("warning", value))

        def success(self, value):
            self.calls.append(("success", value))

        def info(self, value):
            self.calls.append(("info", value))

        def write(self, value):
            self.calls.append(("write", value))

    monkeypatch.setattr(webui_bridge, "_require_streamlit", lambda: None)
    recorder = StreamlitRecorder()
    monkeypatch.setattr(webui_bridge, "st", recorder)

    bridge = webui_bridge.WebUIBridge()

    bridge.display_result("<script>", message_type="error")
    bridge.display_result("warn", message_type="warning")
    bridge.display_result("done", message_type="success")
    bridge.display_result("spotlight", highlight=True)
    bridge.display_result("plain")

    assert [name for name, _ in recorder.calls] == [
        "error",
        "warning",
        "success",
        "info",
        "write",
    ]
    assert len(bridge.messages) == 5

    first_message = recorder.calls[0][1]
    sanitized_text = getattr(first_message, "plain", str(first_message))
    assert "<" not in sanitized_text
    assert "script" in sanitized_text
    assert recorder.calls[0][1] is bridge.messages[0]


@pytest.mark.fast
def test_webui_bridge_session_access_wrappers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Session wrapper helpers delegate to the shared state access module.

    ReqID: N/A
    """

    sentinel_session = object()
    seen = {}

    def fake_get(session_state, key, default=None):
        seen["get"] = (session_state, key, default)
        return "value"

    def fake_set(session_state, key, value):
        seen.setdefault("set", []).append((session_state, key, value))
        return True

    monkeypatch.setattr(webui_bridge, "_get_session_value", fake_get)
    monkeypatch.setattr(webui_bridge, "_set_session_value", fake_set)

    assert (
        webui_bridge.WebUIBridge.get_session_value(
            sentinel_session, "answer", default="fallback"
        )
        == "value"
    )
    assert seen["get"] == (sentinel_session, "answer", "fallback")

    assert webui_bridge.WebUIBridge.set_session_value(sentinel_session, "answer", 42)
    assert seen["set"] == [(sentinel_session, "answer", 42)]


@pytest.mark.fast
def test_webui_bridge_prompt_aliases_and_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prompt aliases reuse core UX methods and progress factory returns indicators.

    ReqID: N/A
    """

    bridge = webui_bridge.WebUIBridge()

    recorded = []

    def record_display(message, **kwargs):
        recorded.append((message, kwargs))

    monkeypatch.setattr(bridge, "display_result", record_display)

    assert bridge.ask_question("Question?", default="answer") == "answer"
    assert bridge.ask_question("No default") == ""
    assert bridge.prompt("Prompt?", default=2) == "2"
    assert bridge.confirm_choice("Confirm?", default=True) is True
    assert bridge.confirm("Confirm alias?", default=False) is False

    bridge.print("payload", highlight=True, message_type="info")
    assert recorded == [("payload", {"highlight": True, "message_type": "info"})]

    progress = bridge.create_progress("task", total=5)
    assert isinstance(progress, webui_bridge.WebUIProgressIndicator)


@pytest.mark.fast
def test_normalize_wizard_step_varied_inputs() -> None:
    """``normalize_wizard_step`` coerces diverse inputs into clamped indices.

    ReqID: N/A
    """

    normalize = webui_bridge.WebUIBridge.normalize_wizard_step

    assert normalize(2, total=5) == 2
    assert normalize(7, total=3) == 2
    assert normalize(1.9, total=4) == 1
    assert normalize(" 3 ", total=4) == 3
    assert normalize("", total=4) == 0
    assert normalize("bad", total=4) == 0
    assert normalize(None, total=4) == 0
    assert normalize(1, total=0) == 0
