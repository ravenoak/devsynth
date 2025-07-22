from unittest.mock import MagicMock

from devsynth.interface.webui_setup import WebUISetupWizard
from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.interface.ux_bridge import UXBridge


def test_webui_setup_wizard_runs(monkeypatch):
    bridge = MagicMock(spec=UXBridge)
    run_called = {}

    def fake_run(self):
        run_called['called'] = True

    monkeypatch.setattr(SetupWizard, 'run', fake_run)
    wizard = WebUISetupWizard(bridge)
    wizard.run()
    assert run_called.get('called') is True
