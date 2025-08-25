"""Unit tests for the UXBridge configuration utilities."""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.config import ProjectUnifiedConfig
from devsynth.interface.ux_bridge import UXBridge
from devsynth.interface.uxbridge_config import (
    apply_uxbridge_settings,
    get_default_bridge,
)


class MockUXBridge(UXBridge):
    """Mock UXBridge implementation for testing."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def ask_question(self, message, *, choices=None, default=None, show_default=True):
        return default or ""

    def confirm_choice(self, message, *, default=False):
        return default

    def display_result(self, message, *, highlight=False):
        pass


class TestUXBridgeConfig:
    """Tests for the UXBridge configuration utilities.

    ReqID: N/A"""

    @pytest.fixture
    def clean_state(self):
        # Set up clean state
        yield
        # Clean up state

    @pytest.mark.medium
    def test_apply_uxbridge_settings(self, clean_state):
        """Test applying UXBridge settings to a bridge implementation.

        ReqID: N/A"""

        mock_config = MagicMock(spec=ProjectUnifiedConfig)
        mock_config.config.uxbridge_settings = {
            "default_interface": "cli",
            "webui_port": 8501,
            "api_port": 8000,
            "enable_authentication": False,
        }
        bridge = apply_uxbridge_settings(MockUXBridge, mock_config, test_arg="test")
        assert isinstance(bridge, MockUXBridge)
        assert bridge.kwargs == {"test_arg": "test"}

    @patch("devsynth.interface.uxbridge_config.CLIUXBridge")
    @pytest.mark.medium
    def test_get_default_bridge_cli_succeeds(self, mock_cli_bridge):
        """Test getting the default bridge when CLI is configured.

        ReqID: N/A"""
        mock_config = MagicMock(spec=ProjectUnifiedConfig)
        mock_config.config.uxbridge_settings = {"default_interface": "cli"}
        mock_config.config.features = {
            "uxbridge_webui": False,
            "uxbridge_agent_api": False,
        }
        mock_cli_bridge.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert isinstance(bridge, MockUXBridge)
        mock_cli_bridge.assert_called_once()

    @patch("devsynth.interface.uxbridge_config.WebUI", create=True)
    @pytest.mark.medium
    def test_get_default_bridge_webui_succeeds(self, mock_webui):
        """Test getting the default bridge when WebUI is configured.

        ReqID: N/A"""
        mock_config = MagicMock(spec=ProjectUnifiedConfig)
        mock_config.config.uxbridge_settings = {"default_interface": "webui"}
        mock_config.config.features = {
            "uxbridge_webui": True,
            "uxbridge_agent_api": False,
        }
        mock_webui.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert isinstance(bridge, MockUXBridge)
        mock_webui.assert_called_once()

    @patch("devsynth.interface.uxbridge_config.APIBridge", create=True)
    @pytest.mark.medium
    def test_get_default_bridge_api_succeeds(self, mock_api_bridge):
        """Test getting the default bridge when API is configured.

        ReqID: N/A"""
        mock_config = MagicMock(spec=ProjectUnifiedConfig)
        mock_config.config.uxbridge_settings = {"default_interface": "api"}
        mock_config.config.features = {
            "uxbridge_webui": False,
            "uxbridge_agent_api": True,
        }
        mock_api_bridge.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert isinstance(bridge, MockUXBridge)
        mock_api_bridge.assert_called_once()

    @patch("devsynth.interface.uxbridge_config.CLIUXBridge")
    @patch(
        "devsynth.interface.uxbridge_config.WebUI", create=True, side_effect=ImportError
    )
    @pytest.mark.medium
    def test_get_default_bridge_webui_fallback_succeeds(
        self, mock_webui, mock_cli_bridge
    ):
        """Test fallback to CLI when WebUI is configured but not available.

        ReqID: N/A"""
        mock_config = MagicMock(spec=ProjectUnifiedConfig)
        mock_config.config.uxbridge_settings = {"default_interface": "webui"}
        mock_config.config.features = {
            "uxbridge_webui": True,
            "uxbridge_agent_api": False,
        }
        mock_cli_bridge.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert isinstance(bridge, MockUXBridge)
        mock_webui.assert_called_once()
        mock_cli_bridge.assert_called_once()

    @patch("devsynth.interface.uxbridge_config.CLIUXBridge")
    @patch(
        "devsynth.interface.uxbridge_config.APIBridge",
        create=True,
        side_effect=ImportError,
    )
    @pytest.mark.medium
    def test_get_default_bridge_api_fallback_succeeds(
        self, mock_api_bridge, mock_cli_bridge
    ):
        """Test fallback to CLI when API is configured but not available.

        ReqID: N/A"""
        mock_config = MagicMock(spec=ProjectUnifiedConfig)
        mock_config.config.uxbridge_settings = {"default_interface": "api"}
        mock_config.config.features = {
            "uxbridge_webui": False,
            "uxbridge_agent_api": True,
        }
        mock_cli_bridge.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert isinstance(bridge, MockUXBridge)
        mock_api_bridge.assert_called_once()
        mock_cli_bridge.assert_called_once()
