import pytest

from devsynth.interface.nicegui_webui import NiceGUIBridge


@pytest.mark.fast
def test_session_storage_roundtrip():
    bridge = NiceGUIBridge()
    bridge.set_session_value("key", "value")
    assert bridge.get_session_value("key") == "value"
