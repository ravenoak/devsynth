import importlib
import sys
from types import ModuleType


def test_webui_import_without_cli(monkeypatch):
    """Importing webui should succeed even if CLI commands are missing."""
    cli_module = ModuleType("devsynth.application.cli")
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)
    import devsynth.application

    monkeypatch.setattr(devsynth.application, "cli", cli_module, raising=False)

    import devsynth.interface.webui as webui

    importlib.reload(webui)

    assert webui.code_cmd is None
    assert webui.spec_cmd is None
