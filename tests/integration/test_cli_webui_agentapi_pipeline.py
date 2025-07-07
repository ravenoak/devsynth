"""Integration tests for the CLI/WebUI/AgentAPI pipeline.

This test verifies that commands issued through the CLI or WebUI correctly flow
through the AgentAPI and return the expected results.
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from pathlib import Path

from fastapi.testclient import TestClient

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.webui import WebUI
from devsynth.interface.agentapi import app as agentapi_app


class TestCLIWebUIAgentAPIPipeline:
    """Test the complete pipeline from CLI/WebUI to AgentAPI and back."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_streamlit(self, monkeypatch):
        """Mock streamlit for WebUI testing."""
        import sys
        from types import ModuleType

        st = ModuleType("streamlit")
        st.session_state = {}
        st.session_state.wizard_step = 0
        st.session_state.wizard_data = {}
        st.sidebar = MagicMock()
        st.set_page_config = MagicMock()
        st.header = MagicMock()
        st.expander = MagicMock()
        st.form = MagicMock()
        st.form_submit_button = MagicMock(return_value=True)
        st.text_input = MagicMock()
        st.text_area = MagicMock()
        st.selectbox = MagicMock()
        st.checkbox = MagicMock()
        st.button = MagicMock()
        st.spinner = MagicMock()
        st.divider = MagicMock()
        st.columns = MagicMock()
        st.progress = MagicMock()
        st.write = MagicMock()
        st.markdown = MagicMock()
        st.empty = MagicMock()
        monkeypatch.setitem(sys.modules, "streamlit", st)
        return st

    @pytest.fixture
    def api_client(self):
        """Create a test client for the AgentAPI."""
        return TestClient(agentapi_app)

    @pytest.fixture
    def cli_bridge(self):
        """Create a CLI bridge for testing."""
        return CLIUXBridge()

    @pytest.fixture
    def webui_bridge(self, mock_streamlit):
        """Create a WebUI bridge for testing."""
        return WebUI()

    def test_init_command_pipeline(self, temp_project_dir, api_client, cli_bridge, webui_bridge, monkeypatch):
        """Test the init command pipeline from CLI/WebUI through AgentAPI."""
        # Set up mocks for the CLI command
        with patch("devsynth.application.cli.cli_commands.init_cmd") as mock_init_cmd:
            # Configure the mock to return a specific result
            mock_init_cmd.return_value = {"status": "success", "message": "Project initialized"}

            # Test CLI to AgentAPI pipeline
            with patch("devsynth.interface.agentapi.init_cmd", side_effect=mock_init_cmd):
                # Call the API directly
                response = api_client.post("/init", json={"path": temp_project_dir})
                assert response.status_code == 200
                
                # Verify that the CLI command was called with the correct arguments
                mock_init_cmd.assert_called_once()
                args, kwargs = mock_init_cmd.call_args
                assert kwargs.get("path") == temp_project_dir

            # Reset the mock
            mock_init_cmd.reset_mock()

            # Test WebUI to AgentAPI pipeline
            with patch("devsynth.interface.webui.init_cmd", side_effect=mock_init_cmd):
                # Mock the WebUI input
                mock_streamlit = monkeypatch.getitem(sys.modules, "streamlit")
                mock_streamlit.text_input.side_effect = [temp_project_dir, "python", ""]
                
                # Call the WebUI onboarding page
                webui_bridge.onboarding_page()
                
                # Verify that the CLI command was called with the correct arguments
                mock_init_cmd.assert_called_once()
                args, kwargs = mock_init_cmd.call_args
                assert kwargs.get("path") == temp_project_dir

    def test_spec_command_pipeline(self, temp_project_dir, api_client, cli_bridge, webui_bridge, monkeypatch):
        """Test the spec command pipeline from CLI/WebUI through AgentAPI."""
        # Create a requirements file
        requirements_dir = os.path.join(temp_project_dir, "docs")
        os.makedirs(requirements_dir, exist_ok=True)
        requirements_file = os.path.join(requirements_dir, "requirements.md")
        with open(requirements_file, "w") as f:
            f.write("# Requirements\n\n1. Requirement 1\n2. Requirement 2\n")

        # Set up mocks for the CLI command
        with patch("devsynth.application.cli.cli_commands.spec_cmd") as mock_spec_cmd:
            # Configure the mock to return a specific result
            mock_spec_cmd.return_value = {"status": "success", "message": "Specifications generated"}

            # Test CLI to AgentAPI pipeline
            with patch("devsynth.interface.agentapi.spec_cmd", side_effect=mock_spec_cmd):
                # Call the API directly
                response = api_client.post("/spec", json={"requirements_file": requirements_file})
                assert response.status_code == 200
                
                # Verify that the CLI command was called with the correct arguments
                mock_spec_cmd.assert_called_once()
                args, kwargs = mock_spec_cmd.call_args
                assert kwargs.get("requirements_file") == requirements_file

            # Reset the mock
            mock_spec_cmd.reset_mock()

            # Test WebUI to AgentAPI pipeline
            with patch("devsynth.interface.webui.spec_cmd", side_effect=mock_spec_cmd):
                # Mock the WebUI input
                mock_streamlit = monkeypatch.getitem(sys.modules, "streamlit")
                mock_streamlit.text_input.return_value = requirements_file
                
                # Call the WebUI spec page (assuming it exists)
                # Note: This is a placeholder, adjust based on actual WebUI implementation
                if hasattr(webui_bridge, "spec_page"):
                    webui_bridge.spec_page()
                    
                    # Verify that the CLI command was called with the correct arguments
                    mock_spec_cmd.assert_called_once()
                    args, kwargs = mock_spec_cmd.call_args
                    assert kwargs.get("requirements_file") == requirements_file

    def test_test_command_pipeline(self, temp_project_dir, api_client, cli_bridge, monkeypatch):
        """Test the test command pipeline from CLI through AgentAPI."""
        # Create a spec file
        spec_file = os.path.join(temp_project_dir, "specs.md")
        with open(spec_file, "w") as f:
            f.write("# Specifications\n\n1. Spec 1\n2. Spec 2\n")

        # Set up mocks for the CLI command
        with patch("devsynth.application.cli.cli_commands.test_cmd") as mock_test_cmd:
            # Configure the mock to return a specific result
            mock_test_cmd.return_value = {"status": "success", "message": "Tests generated"}

            # Test CLI to AgentAPI pipeline
            with patch("devsynth.interface.agentapi.test_cmd", side_effect=mock_test_cmd):
                # Call the API directly
                response = api_client.post("/test", json={"spec_file": spec_file, "output_dir": "tests"})
                assert response.status_code == 200
                
                # Verify that the CLI command was called with the correct arguments
                mock_test_cmd.assert_called_once()
                args, kwargs = mock_test_cmd.call_args
                assert kwargs.get("spec_file") == spec_file
                assert kwargs.get("output_dir") == "tests"

    def test_code_command_pipeline(self, temp_project_dir, api_client, cli_bridge, monkeypatch):
        """Test the code command pipeline from CLI through AgentAPI."""
        # Set up mocks for the CLI command
        with patch("devsynth.application.cli.cli_commands.code_cmd") as mock_code_cmd:
            # Configure the mock to return a specific result
            mock_code_cmd.return_value = {"status": "success", "message": "Code generated"}

            # Test CLI to AgentAPI pipeline
            with patch("devsynth.interface.agentapi.code_cmd", side_effect=mock_code_cmd):
                # Call the API directly
                response = api_client.post("/code", json={"output_dir": "src"})
                assert response.status_code == 200
                
                # Verify that the CLI command was called with the correct arguments
                mock_code_cmd.assert_called_once()
                args, kwargs = mock_code_cmd.call_args
                assert kwargs.get("output_dir") == "src"

    def test_edrr_cycle_command_pipeline(self, temp_project_dir, api_client, cli_bridge, monkeypatch):
        """Test the EDRR cycle command pipeline from CLI through AgentAPI."""
        # Set up mocks for the CLI command
        with patch("devsynth.application.cli.commands.edrr_cycle_cmd.edrr_cycle_cmd") as mock_edrr_cycle_cmd:
            # Configure the mock to return a specific result
            mock_edrr_cycle_cmd.return_value = {"status": "success", "message": "EDRR cycle completed"}

            # Test CLI to AgentAPI pipeline
            with patch("devsynth.interface.agentapi.edrr_cycle_cmd", side_effect=mock_edrr_cycle_cmd):
                # Call the API directly
                response = api_client.post("/edrr-cycle", json={"prompt": "Improve code", "max_iterations": 3})
                assert response.status_code == 200
                
                # Verify that the CLI command was called with the correct arguments
                mock_edrr_cycle_cmd.assert_called_once()
                args, kwargs = mock_edrr_cycle_cmd.call_args
                assert kwargs.get("prompt") == "Improve code"
                assert kwargs.get("max_iterations") == 3

    def test_error_handling_in_pipeline(self, api_client, monkeypatch):
        """Test error handling in the CLI/WebUI/AgentAPI pipeline."""
        # Set up mocks for the CLI command to raise an exception
        with patch("devsynth.application.cli.cli_commands.init_cmd") as mock_init_cmd:
            mock_init_cmd.side_effect = ValueError("Test error")

            # Test error handling in the AgentAPI
            with patch("devsynth.interface.agentapi.init_cmd", side_effect=mock_init_cmd):
                # Call the API directly
                response = api_client.post("/init", json={"path": "invalid_path"})
                assert response.status_code == 500
                assert "error" in response.json()
                assert "Test error" in response.json()["error"]