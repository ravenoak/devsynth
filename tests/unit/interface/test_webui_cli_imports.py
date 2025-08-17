import importlib
import sys
from types import ModuleType

import pytest


@pytest.fixture
def clean_state():
    """Set up and tear down a clean state for imports."""
    yield


@pytest.mark.medium
def test_with_clean_state(clean_state, monkeypatch):
    """[R-WEBUI-CLI-001] Importing webui should succeed even if CLI commands are missing."""
    cli_module = ModuleType("devsynth.application.cli")
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)

    from devsynth.interface import webui

    importlib.reload(webui)

    assert webui.spec_cmd is None
    assert webui._cli("code_cmd") is None
