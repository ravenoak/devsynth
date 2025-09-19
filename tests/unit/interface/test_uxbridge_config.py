"""Unit tests for the UXBridge configuration utilities."""

import sys
from types import ModuleType
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

    @staticmethod
    def _make_project_config_mock() -> MagicMock:
        """Create a ``ProjectUnifiedConfig`` mock with nested ``config`` access."""

        mock_config = MagicMock(spec=ProjectUnifiedConfig)
        mock_config.config = MagicMock()
        return mock_config

    @staticmethod
    def _assert_bridge_selection(
        mock_apply: MagicMock, expected_name: str, config: MagicMock
    ) -> None:
        """Assert that ``apply_uxbridge_settings`` was invoked with the expected bridge."""

        mock_apply.assert_called_once()
        args, kwargs = mock_apply.call_args
        assert args[0].__name__ == expected_name
        assert args[1] is config
        assert kwargs == {}

    @pytest.fixture
    def clean_state(self):
        # Set up clean state
        yield
        # Clean up state

    @pytest.mark.medium
    def test_apply_uxbridge_settings(self, clean_state):
        """Test applying UXBridge settings to a bridge implementation.

        ReqID: N/A"""

        mock_config = self._make_project_config_mock()
        mock_config.config.uxbridge_settings = {
            "default_interface": "cli",
            "webui_port": 8501,
            "api_port": 8000,
            "enable_authentication": False,
        }
        bridge = apply_uxbridge_settings(MockUXBridge, mock_config, test_arg="test")
        assert isinstance(bridge, MockUXBridge)
        assert bridge.kwargs == {"test_arg": "test"}

    @patch("devsynth.interface.uxbridge_config.apply_uxbridge_settings")
    @pytest.mark.medium
    def test_get_default_bridge_cli_succeeds(self, mock_apply):
        """Test getting the default bridge when CLI is configured.

        ReqID: N/A"""
        mock_config = self._make_project_config_mock()
        mock_config.config.uxbridge_settings = {"default_interface": "cli"}
        mock_config.config.features = {
            "uxbridge_webui": False,
            "uxbridge_agent_api": False,
        }
        mock_apply.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert bridge is mock_apply.return_value
        self._assert_bridge_selection(mock_apply, "CLIUXBridge", mock_config)

    @patch("devsynth.interface.uxbridge_config.apply_uxbridge_settings")
    @pytest.mark.medium
    def test_get_default_bridge_webui_succeeds(self, mock_apply):
        """Test getting the default bridge when WebUI is configured.

        ReqID: N/A"""
        mock_config = self._make_project_config_mock()
        mock_config.config.uxbridge_settings = {"default_interface": "webui"}
        mock_config.config.features = {
            "uxbridge_webui": True,
            "uxbridge_agent_api": False,
        }
        mock_apply.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert bridge is mock_apply.return_value
        self._assert_bridge_selection(mock_apply, "WebUI", mock_config)

    @patch("devsynth.interface.uxbridge_config.apply_uxbridge_settings")
    @pytest.mark.medium
    def test_get_default_bridge_api_succeeds(self, mock_apply):
        """Test getting the default bridge when API is configured.

        ReqID: N/A"""
        mock_config = self._make_project_config_mock()
        mock_config.config.uxbridge_settings = {"default_interface": "api"}
        mock_config.config.features = {
            "uxbridge_webui": False,
            "uxbridge_agent_api": True,
        }
        mock_apply.return_value = MockUXBridge()
        bridge = get_default_bridge(mock_config)
        assert bridge is mock_apply.return_value
        self._assert_bridge_selection(mock_apply, "APIBridge", mock_config)

    @patch("devsynth.interface.uxbridge_config.apply_uxbridge_settings")
    @pytest.mark.medium
    def test_get_default_bridge_webui_fallback_succeeds(self, mock_apply):
        """Test fallback to CLI when WebUI is configured but not available.

        ReqID: N/A"""
        mock_config = self._make_project_config_mock()
        mock_config.config.uxbridge_settings = {"default_interface": "webui"}
        mock_config.config.features = {
            "uxbridge_webui": True,
            "uxbridge_agent_api": False,
        }
        mock_apply.return_value = MockUXBridge()
        stub_module = ModuleType("devsynth.interface.webui")
        with patch.dict(sys.modules, {"devsynth.interface.webui": stub_module}):
            bridge = get_default_bridge(mock_config)

        assert bridge is mock_apply.return_value
        self._assert_bridge_selection(mock_apply, "CLIUXBridge", mock_config)

    @patch("devsynth.interface.uxbridge_config.apply_uxbridge_settings")
    @pytest.mark.medium
    def test_get_default_bridge_api_fallback_succeeds(self, mock_apply):
        """Test fallback to CLI when API is configured but not available.

        ReqID: N/A"""
        mock_config = self._make_project_config_mock()
        mock_config.config.uxbridge_settings = {"default_interface": "api"}
        mock_config.config.features = {
            "uxbridge_webui": False,
            "uxbridge_agent_api": True,
        }
        mock_apply.return_value = MockUXBridge()
        stub_module = ModuleType("devsynth.interface.agentapi")
        with patch.dict(sys.modules, {"devsynth.interface.agentapi": stub_module}):
            bridge = get_default_bridge(mock_config)

        assert bridge is mock_apply.return_value
        self._assert_bridge_selection(mock_apply, "CLIUXBridge", mock_config)
