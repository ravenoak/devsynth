import importlib
import sys
import pytest
from types import ModuleType

@pytest.mark.medium

@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state

def test_with_clean_state(clean_state):
    """Importing webui should succeed even if CLI commands are missing."""

    cli_module = ModuleType("devsynth.application.cli")
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)
    import devsynth.application

    original = module_name
    try:
        monkeypatch.setattr(target_module, mock_function)
        # Test code here
    finally:
        # Restore original if needed for cleanup
        pass

        import importlib
        from devsynth.interface import webui
        # Reload the module to ensure clean state
        importlib.reload(module)

        importlib.reload(webui)

        assert webui.code_cmd is None
        assert webui.spec_cmd is None