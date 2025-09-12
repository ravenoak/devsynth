import importlib

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui_bridge


@pytest.mark.fast
def test_require_streamlit_raises(monkeypatch):
    """Missing Streamlit triggers DevSynthError.

    ReqID: N/A"""
    monkeypatch.setattr(webui_bridge, "st", None)

    def _raise(name):
        raise ImportError("missing")

    monkeypatch.setattr(importlib, "import_module", _raise)
    with pytest.raises(DevSynthError):
        webui_bridge._require_streamlit()


@pytest.mark.fast
def test_progress_indicator_status_transitions():
    """Progress indicator updates status without explicit messages.

    ReqID: N/A"""
    ind = webui_bridge.WebUIProgressIndicator("task", 100)
    ind.update(advance=25)
    ind.update(advance=0)
    assert ind._status == "Processing..."
    ind.update(advance=25)
    ind.update(advance=0)
    assert ind._status == "Halfway there..."
    ind.update(advance=25)
    ind.update(advance=0)
    assert ind._status == "Almost done..."
    ind.update(advance=24)
    ind.update(advance=0)
    assert ind._status == "Finalizing..."
    ind.update(advance=1)
    ind.update(advance=0)
    assert ind._status == "Complete"
