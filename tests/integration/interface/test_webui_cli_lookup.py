from types import SimpleNamespace

from devsynth.interface import webui


def test_cli_fallback_to_cli_module(monkeypatch):
    dummy = object()
    cli_mod = SimpleNamespace(sample_cmd=dummy)
    monkeypatch.setattr(webui, "_cli_mod", cli_mod, raising=False)
    monkeypatch.delattr(webui, "sample_cmd", raising=False)
    assert webui._cli("sample_cmd") is dummy
