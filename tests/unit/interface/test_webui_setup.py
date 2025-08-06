from unittest.mock import MagicMock

from devsynth.interface.webui_setup import WebUISetupWizard
from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.interface.ux_bridge import UXBridge
import pytest


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.slow
def test_function(clean_state):
    # Test with clean state
    bridge = MagicMock(spec=UXBridge)
    run_called = {}

    def fake_run(self):
        run_called["called"] = True

    original = module_name
    try:
        monkeypatch.setattr(target_module, mock_function)
        # Test code here
    finally:
        # Restore original if needed for cleanup
        pass

        wizard = WebUISetupWizard(bridge)
        wizard.run()
        assert run_called.get("called") is True
