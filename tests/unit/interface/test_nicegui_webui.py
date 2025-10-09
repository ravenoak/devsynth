"""Unit tests for NiceGUI WebUI implementation."""

import pytest

from devsynth.interface.nicegui_webui import (
    NiceGUIBridge,
    NiceGUIProgressIndicator,
    main,
)


class TestNiceGUIWebUI:
    """Test NiceGUI WebUI components."""

    @pytest.mark.fast
    def test_nicegui_progress_indicator_initialization(self):
        """Test NiceGUIProgressIndicator initialization."""
        indicator = NiceGUIProgressIndicator("Test progress", 100)
        assert indicator._total == 100
        assert indicator._current == 0

    @pytest.mark.fast
    def test_nicegui_progress_indicator_update(self):
        """Test NiceGUIProgressIndicator update functionality."""
        indicator = NiceGUIProgressIndicator("Test progress", 100)

        # Test basic update
        indicator.update(advance=50)
        assert indicator._current == 50

    @pytest.mark.fast
    def test_nicegui_progress_indicator_complete(self):
        """Test NiceGUIProgressIndicator completion."""
        indicator = NiceGUIProgressIndicator("Test progress", 100)

        indicator.complete()
        # complete() doesn't update _current, just sets bar to 1.0
        assert indicator._current == 0  # This is expected behavior

    @pytest.mark.fast
    def test_nicegui_bridge_initialization(self):
        """Test NiceGUIBridge initialization."""
        bridge = NiceGUIBridge()
        assert bridge is not None
        assert hasattr(bridge, "messages")

    @pytest.mark.fast
    def test_nicegui_bridge_create_progress(self):
        """Test NiceGUIBridge progress creation."""
        bridge = NiceGUIBridge()
        progress = bridge.create_progress("Test", total=50)

        assert isinstance(progress, NiceGUIProgressIndicator)
        assert progress._total == 50

    @pytest.mark.fast
    def test_main_function_exists(self):
        """Test that main function exists."""
        # Just test that the function exists, don't actually call it
        # as it requires NiceGUI which may not be available
        assert callable(main)
