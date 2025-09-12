import importlib
import types

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui


@pytest.mark.fast
def test_require_streamlit_returns_module(monkeypatch):
    """Successful import returns module.

    ReqID: N/A"""
    module = types.SimpleNamespace()
    monkeypatch.setattr(webui, "_STREAMLIT", None)
    monkeypatch.setattr(importlib, "import_module", lambda name: module)
    assert webui._require_streamlit() is module


@pytest.mark.fast
def test_require_streamlit_raises(monkeypatch):
    """Import failure raises DevSynthError.

    ReqID: N/A"""
    monkeypatch.setattr(webui, "_STREAMLIT", None)

    def _raise(name):
        raise ImportError("missing")

    monkeypatch.setattr(importlib, "import_module", _raise)
    with pytest.raises(DevSynthError):
        webui._require_streamlit()
