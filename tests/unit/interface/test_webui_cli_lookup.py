from devsynth.interface import webui


def test_cli_returns_module_attribute(monkeypatch):
    def dummy():
        return "ok"

    monkeypatch.setattr(webui, "dummy_cmd", dummy, raising=False)
    assert webui._cli("dummy_cmd") is dummy


def test_cli_returns_none_when_missing(monkeypatch):
    monkeypatch.delattr(webui, "nonexistent", raising=False)
    assert webui._cli("nonexistent") is None
