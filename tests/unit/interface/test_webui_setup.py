from unittest.mock import MagicMock

import pytest

from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.interface.ux_bridge import UXBridge
from devsynth.interface.webui_setup import WebUISetupWizard

pytestmark = pytest.mark.requires_resource("webui")


@pytest.mark.medium
def test_webui_setup_wizard_runs(monkeypatch):
    bridge = MagicMock(spec=UXBridge)
    run_mock = MagicMock()
    monkeypatch.setattr(SetupWizard, "run", run_mock)
    WebUISetupWizard(bridge).run()
    run_mock.assert_called_once()
