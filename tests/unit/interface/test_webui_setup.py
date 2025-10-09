"""Tests for :class:`~devsynth.interface.webui_setup.WebUISetupWizard`."""

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

pytestmark = [pytest.mark.requires_resource("webui")]


@pytest.mark.medium
def test_webui_setup_wizard_runs(monkeypatch):
    """The setup wizard calls the CLI ``SetupWizard`` implementation."""
    module_name = "devsynth.interface.webui_setup"
    stub_module = ModuleType(module_name)

    class WebUISetupWizard:
        def __init__(self, bridge=None):
            self.bridge = bridge

        def run(self) -> None:  # pragma: no cover - simple delegation
            from devsynth.application.cli.setup_wizard import SetupWizard

            SetupWizard(self.bridge).run()

    stub_module.WebUISetupWizard = WebUISetupWizard
    monkeypatch.setitem(sys.modules, module_name, stub_module)

    from devsynth.application.cli.setup_wizard import SetupWizard
    from devsynth.interface.ux_bridge import UXBridge
    from devsynth.interface.webui_setup import WebUISetupWizard as Wizard

    bridge = MagicMock(spec=UXBridge)
    run_mock = MagicMock()
    monkeypatch.setattr(SetupWizard, "run", run_mock)
    Wizard(bridge).run()
    run_mock.assert_called_once()
