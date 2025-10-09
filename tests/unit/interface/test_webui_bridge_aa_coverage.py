from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("force_webui_available"),
]


@pytest.fixture()
def bridge_live(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Expose the cached bridge module with a Streamlit stub and no reload."""

    from devsynth.interface import webui_bridge as bridge

    fake_streamlit = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setattr(bridge, "st", None, raising=False)
    return SimpleNamespace(module=bridge, streamlit=fake_streamlit)


def test_z_progress_indicator_extensive_paths_cover_hierarchy(
    bridge_live: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SpecRef: docs/specifications/webui-integration.md §Progress indicators;
    docs/developer_guides/progress_indicators.md §Testing with Progress Indicators.

    Exercises fallback descriptions, nested subtasks, and default status
    thresholds so the hierarchy mirrors the documented UX affordances.
    """

    bridge = bridge_live.module

    class Explodes:
        def __str__(self) -> str:
            raise ValueError("cannot stringify")

    sanitize_inputs: list[str] = []

    def fake_sanitize(value: str) -> str:
        sanitize_inputs.append(value)
        if value == "raise":
            raise ValueError("boom")
        return f"san::{value}"

    monkeypatch.setattr(bridge, "sanitize_output", fake_sanitize)
    tick = iter(range(1000))
    monkeypatch.setattr(bridge.time, "time", lambda: next(tick))

    indicator = bridge.WebUIProgressIndicator("start", 12)

    indicator.update(description="step-1", status="ok", advance=2)
    assert indicator._description == "san::step-1"
    assert indicator._status == "san::ok"

    indicator.update(description=Explodes(), advance=0)
    assert indicator._description == "san::step-1"

    indicator.update(status="raise", advance=0)
    assert indicator._status == "In progress..."

    statuses: list[str] = []
    for current in (0, 3, 6, 9, 11.88, 12):
        indicator._current = current
        indicator.update(advance=0)
        statuses.append(indicator._status)

    indicator.complete()
    assert indicator._current == indicator._total

    sub_good = indicator.add_subtask("alpha", total=5)
    sub_fallback = indicator.add_subtask(Explodes())
    assert indicator._subtasks[sub_fallback]["description"] == "<subtask>"
    assert indicator._subtasks[sub_good]["description"] == "san::alpha"

    indicator.update_subtask(sub_good, description="update", advance=2)
    indicator.update_subtask(sub_good, description=Explodes())
    assert indicator._subtasks[sub_good]["description"] == "san::update"
    indicator.update_subtask("missing", description="skip")

    missing_nested = indicator.add_nested_subtask("missing", "noop")
    assert missing_nested == ""

    nested = indicator.add_nested_subtask(sub_good, Explodes(), total=4, status="init")
    nested_data = indicator._subtasks[sub_good]["nested_subtasks"][nested]
    assert nested_data["description"] == "<nested subtask>"
    assert nested_data["status"] == "init"
    indicator.update_nested_subtask(
        sub_good, nested, description="nested-update", status="clean"
    )
    indicator.update_nested_subtask(sub_good, nested, status="raise")
    assert (
        indicator._subtasks[sub_good]["nested_subtasks"][nested]["status"]
        == "In progress..."
    )
    indicator.update_nested_subtask(sub_good, nested, description=Explodes())
    assert (
        indicator._subtasks[sub_good]["nested_subtasks"][nested]["description"]
        == "san::nested-update"
    )

    nested_statuses: list[str] = []
    for current in (0, 1, 2, 3, 3.96, 4):
        indicator._subtasks[sub_good]["nested_subtasks"][nested]["current"] = current
        indicator.update_nested_subtask(sub_good, nested, advance=0, status=None)
        nested_statuses.append(
            indicator._subtasks[sub_good]["nested_subtasks"][nested]["status"]
        )

    indicator.update_nested_subtask("missing", nested, description="skip")
    indicator.update_nested_subtask(sub_good, "missing", description="skip")

    indicator.complete_nested_subtask("missing", "missing")
    indicator.complete_nested_subtask(sub_good, nested)
    indicator.complete_subtask("missing")
    indicator.complete_subtask(sub_good)
    nested_result = indicator._subtasks[sub_good]["nested_subtasks"][nested]
    assert nested_result["completed"] is True
    assert nested_result["status"] == "Complete"
    assert indicator._subtasks[sub_good]["completed"] is True
    assert (
        indicator._subtasks[sub_good]["current"]
        == indicator._subtasks[sub_good]["total"]
    )

    assert sanitize_inputs == [
        "step-1",
        "ok",
        "raise",
        "alpha",
        "update",
        "nested-update",
        "clean",
        "raise",
    ]
    assert statuses == [
        "Starting...",
        "Processing...",
        "Halfway there...",
        "Almost done...",
        "Finalizing...",
        "Complete",
    ]
    assert nested_statuses == [
        "Starting...",
        "Processing...",
        "Halfway there...",
        "Almost done...",
        "Finalizing...",
        "Complete",
    ]


def test_z_bridge_accessors_and_wizard_paths_cover_invariants(
    bridge_live: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """SpecRef: docs/implementation/requirements_wizard_wizardstate_integration.md §Summary;
    docs/implementation/webui_invariants.md §Bounded Step Navigation;
    docs/implementation/output_formatter_invariants.md §Formatting Rules.

    Wizard navigation, session helpers, and Streamlit display channels follow
    the published invariants and reuse the shared OutputFormatter pipeline.
    """

    bridge = bridge_live.module
    bridge.st = None
    bridge._require_streamlit()
    assert bridge.st is bridge_live.streamlit

    ui = bridge.WebUIBridge()

    with caplog.at_level("WARNING"):
        assert (
            bridge.WebUIBridge.adjust_wizard_step("1", direction="next", total=2) == 1
        )
    caplog.clear()
    with caplog.at_level("WARNING"):
        assert (
            bridge.WebUIBridge.adjust_wizard_step(0, direction="back", total="bad") == 0
        )
    caplog.clear()
    with caplog.at_level("WARNING"):
        assert (
            bridge.WebUIBridge.adjust_wizard_step(0, direction="sideways", total=1) == 0
        )

    assert bridge.WebUIBridge.normalize_wizard_step(1.2, total=3) == 1
    assert bridge.WebUIBridge.normalize_wizard_step(" 2 ", total=3) == 2
    caplog.clear()
    with caplog.at_level("WARNING"):
        assert bridge.WebUIBridge.normalize_wizard_step("bad", total=3) == 0

    assert ui.ask_question("Q?", default="answer") == "answer"
    assert ui.confirm_choice("Continue?", default=False) is False

    formatter_calls: list[tuple[str, str | None, bool]] = []

    def fake_format(
        message: str, message_type: str | None = None, highlight: bool = False
    ) -> str:
        formatter_calls.append((message, message_type, highlight))
        return f"{message_type or 'normal'}::{highlight}"

    monkeypatch.setattr(
        ui,
        "formatter",
        SimpleNamespace(format_message=fake_format),
        raising=False,
    )

    st = bridge_live.streamlit
    for name in ("error", "warning", "success", "info", "write"):
        getattr(st, name).reset_mock()

    ui.display_result("serious", message_type="error", highlight=True)
    ui.display_result("heads-up", message_type="warning")
    ui.display_result("victory", message_type="success")
    ui.display_result("note", message_type="info")
    ui.display_result("progress", highlight=True)
    ui.display_result("plain")

    assert formatter_calls == [
        ("serious", "error", True),
        ("heads-up", "warning", False),
        ("victory", "success", False),
        ("note", "info", False),
        ("progress", None, True),
        ("plain", None, False),
    ]
    assert st.error.call_args[0][0] == "error::True"
    assert st.warning.call_args[0][0] == "warning::False"
    assert st.success.call_args[0][0] == "success::False"
    assert st.info.call_count == 2
    assert st.info.call_args_list[0][0][0] == "info::False"
    assert st.info.call_args_list[1][0][0] == "normal::True"
    assert st.write.call_args[0][0] == "normal::False"
    assert ui.messages == [
        "error::True",
        "warning::False",
        "success::False",
        "info::False",
        "normal::True",
        "normal::False",
    ]

    progress = ui.create_progress("Task", total=3)
    assert isinstance(progress, bridge.WebUIProgressIndicator)

    st.session_state.clear()
    manager = ui.get_wizard_manager("wiz", steps=2, initial_state={"foo": "bar"})
    state = manager.get_wizard_state()
    assert state.get("foo") == "bar"
    state.set("foo", "baz")
    assert ui.get_wizard_state("wiz", steps=2).get("foo") == "baz"

    with pytest.raises(bridge.DevSynthError):
        bridge.WebUIBridge.create_wizard_manager(None, "oops", steps=1)

    assert (
        bridge.WebUIBridge.get_session_value(st.session_state, "missing", default=1)
        == 1
    )
    assert bridge.WebUIBridge.get_session_value(st.session_state, "wiz_foo") == "baz"
    assert bridge.WebUIBridge.set_session_value(st.session_state, "new", 5) is True
    assert bridge.WebUIBridge.get_session_value(st.session_state, "new") == 5
    assert getattr(st.session_state, "new") == 5
    assert st.session_state["new"] == 5
