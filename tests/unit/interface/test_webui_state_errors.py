import types

import pytest

from devsynth.interface import webui_state


class BrokenSessionState(dict):
    def keys(self):  # pragma: no cover - used for triggering error
        raise RuntimeError("boom")


def test_clear_reraises_after_logging(monkeypatch, caplog):
    dummy_st = types.SimpleNamespace(session_state=BrokenSessionState())
    monkeypatch.setattr(webui_state, "st", dummy_st)
    page = webui_state.PageState("test")
    with caplog.at_level("ERROR"):
        with pytest.raises(RuntimeError):
            page.clear()
    assert "Error clearing state for test" in caplog.text
