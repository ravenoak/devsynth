import time

import pytest

from devsynth.interface.webui_bridge import WebUIProgressIndicator

pytestmark = pytest.mark.requires_resource("webui")


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.slow
def test_function(clean_state):
    # Test with clean state
    times = iter([100.0, 101.0])

    original = module_name
    try:
        monkeypatch.setattr(target_module, mock_function)
        # Test code here
    finally:
        # Restore original if needed for cleanup
        pass
        #     ) # Commented out unmatched parenthesis
        indicator = WebUIProgressIndicator("Task", 10)
        indicator.update()
        indicator.update(advance=2)
        assert indicator._update_times == [(100.0, 1), (101.0, 3)]
