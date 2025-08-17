import importlib
import sys
from types import ModuleType

import pytest

from tests.fixtures.streamlit_mocks import make_streamlit_mock


@pytest.fixture(autouse=True)
def stub_streamlit(monkeypatch):
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def clean_state():
    """Set up and tear down a clean application state."""
    yield
    # Clean up state


@pytest.mark.medium
def test_with_clean_state(clean_state, monkeypatch):
    """Importing WebUI succeeds without CLI command modules.

    ReqID: FR-75"""
    cli_module = ModuleType("devsynth.application.cli")
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)

    import devsynth.interface.webui as webui

    importlib.reload(webui)

    assert webui.spec_cmd is None
    assert webui._cli("code_cmd") is None
