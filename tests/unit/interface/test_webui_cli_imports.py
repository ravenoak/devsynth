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
def stub_empty_cli(monkeypatch):
    cli_module = ModuleType("devsynth.application.cli")
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)
    yield cli_module


@pytest.mark.medium
def test_webui_import_without_cli_commands_succeeds(stub_empty_cli):
    """Importing WebUI succeeds without CLI command modules.

    ReqID: FR-75"""
    import devsynth.interface.webui as webui

    importlib.reload(webui)

    assert webui.spec_cmd is None
    assert webui._cli("code_cmd") is None
