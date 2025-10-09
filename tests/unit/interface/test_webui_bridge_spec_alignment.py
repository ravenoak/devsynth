from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest
from rich.text import Text

from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("force_webui_available"),
]


@pytest.fixture()
def bridge_env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Reload the bridge against a Streamlit stub for deterministic tests."""

    fake_streamlit = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    import devsynth.interface.webui_bridge as bridge

    module = importlib.reload(bridge)
    return SimpleNamespace(module=module, streamlit=fake_streamlit)


def test_require_streamlit_missing_dependency_surfaces_install_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SpecRef: docs/resources_matrix.md §Extras → Env Flags → Example Enablement (webui);
    docs/specifications/webui-integration.md §Specification.

    `_require_streamlit` should surface actionable installation instructions when
    Streamlit is unavailable so coverage reflects the lazy-loader invariant.
    """

    import importlib

    from devsynth.interface import webui_bridge as bridge

    monkeypatch.delitem(sys.modules, "streamlit", raising=False)
    monkeypatch.setattr(bridge, "st", None, raising=False)

    def fail_import(name: str):  # pragma: no cover - defensive guard
        raise ModuleNotFoundError(f"missing {name}")

    monkeypatch.setattr(importlib, "import_module", fail_import)

    with pytest.raises(bridge.DevSynthError) as excinfo:
        bridge._require_streamlit()

    message = str(excinfo.value)
    assert "poetry install --with dev --extras webui" in message
    assert "Streamlit is required" in message
    assert bridge.st is None


def test_nested_progress_status_defaults_follow_spec(
    bridge_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SpecRef: docs/specifications/webui-integration.md §Progress indicators;
    docs/developer_guides/progress_indicators.md §UXBridge Integration.

    Nested subtasks surface the documented status thresholds and cascade
    completion through parent subtasks.
    """

    bridge = bridge_env.module
    tick = iter(range(1000))
    monkeypatch.setattr(bridge.time, "time", lambda: next(tick))

    indicator = bridge.WebUIProgressIndicator("Collect", 100)
    parent_id = indicator.add_subtask("Gather", total=40)
    nested_id = indicator.add_nested_subtask(parent_id, "Validate", total=8)

    expectations = [
        (0, "Starting..."),
        (2, "Processing..."),
        (4, "Halfway there..."),
        (6, "Almost done..."),
        (8 * 0.99, "Finalizing..."),
        (8, "Complete"),
    ]

    for progress, status in expectations:
        indicator._subtasks[parent_id]["nested_subtasks"][nested_id][
            "current"
        ] = progress
        indicator.update_nested_subtask(parent_id, nested_id, advance=0, status=None)
        nested = indicator._subtasks[parent_id]["nested_subtasks"][nested_id]
        assert nested["status"] == status

    indicator.complete_subtask(parent_id)
    subtask = indicator._subtasks[parent_id]
    assert subtask["completed"] is True
    assert subtask["current"] == subtask["total"]
    assert all(nested["completed"] for nested in subtask["nested_subtasks"].values())


def test_wizard_navigation_normalization_matches_state_invariants(
    bridge_env: SimpleNamespace, caplog: pytest.LogCaptureFixture
) -> None:
    """SpecRef: docs/implementation/webui_invariants.md §Bounded Step Navigation;
    docs/specifications/webui-integration.md §Wizard navigation.

    Adjust and normalize cooperate to clamp navigation and surface warnings for
    invalid totals or directions.
    """

    bridge = bridge_env.module
    adjust = bridge.WebUIBridge.adjust_wizard_step
    normalize = bridge.WebUIBridge.normalize_wizard_step

    assert adjust(0, direction="next", total=3) == 1
    assert adjust(2, direction="next", total=3) == 2
    assert adjust(0, direction="back", total=3) == 0

    with caplog.at_level("WARNING"):
        clamped = adjust("two", direction="next", total=2)
    assert clamped == 1
    assert any("Invalid current step" in message for message in caplog.messages)

    caplog.clear()
    with caplog.at_level("WARNING"):
        fallback = adjust(1, direction="forward", total=0)
    assert fallback == 0
    assert any("Invalid direction" in message for message in caplog.messages)
    assert any("Invalid total steps" in message for message in caplog.messages)

    assert normalize(5.7, total=4) == 3
    assert normalize(" 1 ", total=3) == 1
    assert normalize(None, total=3) == 0

    caplog.clear()
    with caplog.at_level("WARNING"):
        assert normalize("nan", total=3) == 0
    assert any("Failed to normalize" in message for message in caplog.messages)


def test_wizard_manager_accessors_follow_integration_guide(
    bridge_env: SimpleNamespace,
) -> None:
    """SpecRef: docs/implementation/requirements_wizard_wizardstate_integration.md §Summary;
    docs/specifications/webui-integration.md §Wizard state wiring.

    Session-backed managers persist WizardState across calls and guard missing
    session_state inputs with DevSynthError.
    """

    bridge = bridge_env.module
    bridge_env.streamlit.session_state.clear()
    ui = bridge.WebUIBridge()

    manager = ui.get_wizard_manager(
        "requirements", steps=2, initial_state={"title": "Draft"}
    )
    state = manager.get_wizard_state()
    assert state.get("title") == "Draft"

    state.set("title", "Refined")
    fetched = ui.get_wizard_state("requirements", steps=2)
    assert fetched.get("title") == "Refined"

    with pytest.raises(bridge.DevSynthError):
        bridge.WebUIBridge.create_wizard_manager(None, "bad", steps=1)


def test_prompt_defaults_align_with_uxbridge_contract(
    bridge_env: SimpleNamespace,
) -> None:
    """SpecRef: docs/developer_guides/uxbridge_testing.md §Unit Testing UXBridge Implementations.

    Prompt helpers mirror CLI defaults and legacy aliases for parity.
    """

    bridge = bridge_env.module
    ui = bridge.WebUIBridge()

    assert (
        ui.ask_question(
            "Select step", choices=("one", "two"), default="two", show_default=True
        )
        == "two"
    )
    assert ui.confirm_choice("Continue?", default=True) is True
    assert ui.prompt("Legacy prompt", default="fallback") == "fallback"
    assert ui.confirm("Legacy confirm", default=False) is False


def test_display_result_channels_respect_output_formatter_contract(
    bridge_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SpecRef: docs/implementation/output_formatter_invariants.md §Formatting Rules;
    docs/specifications/webui-integration.md §Wizard messaging.

    Error routing and highlight toggles delegate to OutputFormatter before
    hitting the appropriate Streamlit channels.
    """

    bridge = bridge_env.module
    ui = bridge.WebUIBridge()
    recorded: list[tuple[str, str | None, bool]] = []

    def fake_format(
        message: str, message_type: str | None = None, highlight: bool = False
    ) -> Text:
        recorded.append((message, message_type, highlight))
        return Text(f"{message_type or 'normal'}::{highlight}")

    monkeypatch.setattr(
        ui,
        "formatter",
        SimpleNamespace(format_message=fake_format),
        raising=False,
    )

    st = bridge_env.streamlit
    for name in ("error", "warning", "success", "info", "write"):
        getattr(st, name).reset_mock()

    ui.display_result("Failure occurred", message_type="error", highlight=True)
    assert recorded[0] == ("Failure occurred", "error", True)
    st.error.assert_called_once()
    assert ui.messages[-1] is st.error.call_args[0][0]

    ui.display_result("Heads up", message_type="warning")
    assert recorded[1] == ("Heads up", "warning", False)
    st.warning.assert_called_once()
    assert ui.messages[-1] is st.warning.call_args[0][0]

    ui.display_result("Great success", message_type="success")
    assert recorded[2] == ("Great success", "success", False)
    st.success.assert_called_once()

    ui.display_result("Progress note", highlight=True)
    assert recorded[3] == ("Progress note", None, True)
    st.info.assert_called_once()
    assert ui.messages[-1] is st.info.call_args[0][0]

    ui.display_result("Plain text")
    assert recorded[4] == ("Plain text", None, False)
    st.write.assert_called_once()
