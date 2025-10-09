from __future__ import annotations

import pytest

from devsynth.interface import webui_bridge
from tests.helpers.dummies import DummySessionState, DummyStreamlit, DummyWizardManager


@pytest.mark.fast
def test_webui_bridge_get_wizard_manager_uses_session_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_streamlit = DummyStreamlit()
    monkeypatch.setattr(webui_bridge, "st", dummy_streamlit)
    monkeypatch.setattr(webui_bridge, "_require_streamlit", lambda: None)

    bridge = webui_bridge.WebUIBridge()
    captured: dict[str, object] = {}

    def fake_create(
        self,
        session_state: DummySessionState,
        wizard_name: str,
        *,
        steps: int,
        initial_state: dict | None = None,
    ) -> DummyWizardManager:
        captured["session_state"] = session_state
        captured["wizard_name"] = wizard_name
        captured["steps"] = steps
        captured["initial_state"] = initial_state
        return DummyWizardManager(session_state, wizard_name, steps, initial_state)

    monkeypatch.setattr(webui_bridge.WebUIBridge, "create_wizard_manager", fake_create)

    manager = bridge.get_wizard_manager(
        "onboarding", steps=3, initial_state={"ready": True}
    )

    assert isinstance(manager, DummyWizardManager)
    assert captured["session_state"] is dummy_streamlit.session_state
    assert captured["wizard_name"] == "onboarding"
    assert captured["steps"] == 3
    assert captured["initial_state"] == {"ready": True}


@pytest.mark.fast
def test_webui_bridge_create_wizard_manager_instantiates_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import devsynth.interface.wizard_state_manager as wizard_state_module

    dummy_state = DummySessionState()
    recorded: dict[str, object] = {}

    class RecorderWizardManager(DummyWizardManager):
        def __init__(
            self, session_state, wizard_name, steps, initial_state=None
        ):  # noqa: ANN001 - interface
            super().__init__(session_state, wizard_name, steps, initial_state)
            recorded["session_state"] = session_state
            recorded["wizard_name"] = wizard_name
            recorded["steps"] = steps
            recorded["initial_state"] = initial_state

    monkeypatch.setattr(
        wizard_state_module, "WizardStateManager", RecorderWizardManager
    )

    bridge = webui_bridge.WebUIBridge()
    manager = bridge.create_wizard_manager(
        dummy_state, "alignment", steps=4, initial_state={"step": 1}
    )

    assert isinstance(manager, RecorderWizardManager)
    assert recorded == {
        "session_state": dummy_state,
        "wizard_name": "alignment",
        "steps": 4,
        "initial_state": {"step": 1},
    }


@pytest.mark.fast
def test_webui_bridge_session_helpers_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel_state = DummySessionState()
    sentinel_state["existing"] = "value"

    captured_get: list[tuple[object, str, object]] = []
    captured_set: list[tuple[object, str, object]] = []

    def fake_get(session_state, key, default):
        captured_get.append((session_state, key, default))
        return "retrieved"

    def fake_set(session_state, key, value):
        captured_set.append((session_state, key, value))
        return True

    monkeypatch.setattr(webui_bridge, "_get_session_value", fake_get)
    monkeypatch.setattr(webui_bridge, "_set_session_value", fake_set)

    result = webui_bridge.WebUIBridge.get_session_value(
        sentinel_state, "existing", default="missing"
    )
    updated = webui_bridge.WebUIBridge.set_session_value(sentinel_state, "new", "data")

    assert result == "retrieved"
    assert captured_get == [(sentinel_state, "existing", "missing")]
    assert captured_set == [(sentinel_state, "new", "data")]
    assert updated is True
