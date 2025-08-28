from types import SimpleNamespace

import pytest

from devsynth.interface import webui


@pytest.mark.medium
def test_cli_fallback_to_cli_module(monkeypatch):
    dummy = object()
    cli_mod = SimpleNamespace(sample_cmd=dummy)
    monkeypatch.setattr(webui, "_cli_mod", cli_mod, raising=False)
    monkeypatch.delattr(webui, "sample_cmd", raising=False)
    assert webui._cli("sample_cmd") is dummy
