"""
Unit tests for the configuration settings module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from devsynth.config.settings import get_llm_settings, get_settings, load_dotenv
from devsynth.exceptions import ConfigurationError


class TestConfigSettings:
    """Tests for the configuration settings module."""

    def test_get_settings_default_values(self):
        """Test that get_settings returns default values when environment variables are not set."""
        # Clear any existing environment variables that might affect the test
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()

            # Check default values
            assert settings["memory_store_type"] == "memory"
            assert settings["llm_provider"] == "lmstudio"
            assert settings["llm_api_base"] == "http://localhost:1234/v1"
            assert settings["llm_temperature"] == 0.7

    def test_get_settings_from_environment_variables(self):
        """Test that get_settings uses values from environment variables when they are set."""
        # Set environment variables for the test
        env_vars = {
            "DEVSYNTH_MEMORY_STORE": "file",
            "DEVSYNTH_LLM_PROVIDER": "openai",
            "DEVSYNTH_LLM_API_BASE": "https://api.openai.com/v1",
            "DEVSYNTH_LLM_MODEL": "gpt-4",
            "DEVSYNTH_LLM_TEMPERATURE": "0.5",
        }

        with patch.dict(os.environ, env_vars):
            settings = get_settings()

            # Check that values from environment variables are used
            assert settings["memory_store_type"] == "file"
            assert settings["llm_provider"] == "openai"
            assert settings["llm_api_base"] == "https://api.openai.com/v1"
            assert settings["llm_model"] == "gpt-4"
            assert settings["llm_temperature"] == 0.5

    def test_get_llm_settings(self):
        """Test that get_llm_settings returns the correct LLM settings."""
        # Set environment variables for the test
        env_vars = {
            "DEVSYNTH_LLM_PROVIDER": "openai",
            "DEVSYNTH_LLM_API_BASE": "https://api.openai.com/v1",
            "DEVSYNTH_LLM_MODEL": "gpt-4",
            "DEVSYNTH_LLM_MAX_TOKENS": "2000",
            "DEVSYNTH_LLM_TEMPERATURE": "0.5",
            "DEVSYNTH_LLM_AUTO_SELECT_MODEL": "false",
        }

        with patch.dict(os.environ, env_vars):
            llm_settings = get_llm_settings()

            # Check that the correct LLM settings are returned
            assert llm_settings["provider"] == "openai"
            assert llm_settings["api_base"] == "https://api.openai.com/v1"
            assert llm_settings["model"] == "gpt-4"
            assert llm_settings["max_tokens"] == 2000
            assert llm_settings["temperature"] == 0.5
            assert llm_settings["auto_select_model"] is False

    @pytest.mark.parametrize(
        "env_var,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
        ],
    )
    def test_boolean_environment_variables(self, env_var, expected):
        """Test that boolean environment variables are parsed correctly."""
        with patch.dict(os.environ, {"DEVSYNTH_LLM_AUTO_SELECT_MODEL": env_var}):
            settings = get_settings()
            assert settings["llm_auto_select_model"] is expected

    def test_load_dotenv(self):
        """Test that load_dotenv loads environment variables from a .env file."""
        # Create a mock .env file content
        env_content = """
        OPENAI_API_KEY=sk-test-key-12345
        SERPER_API_KEY=serper-test-key-67890
        DEVSYNTH_LLM_MODEL=gpt-3.5-turbo
        DEVSYNTH_LLM_TEMPERATURE=0.8
        """

        # Mock the open function to return our mock .env content
        with patch("builtins.open", mock_open(read_data=env_content)):
            # Mock os.path.exists to return True for the .env file
            with patch("os.path.exists", return_value=True):
                # Mock os.environ to track changes
                with patch.dict(os.environ, {}, clear=True):
                    # Call load_dotenv
                    load_dotenv()

                    # Check that environment variables were loaded
                    assert os.environ.get("OPENAI_API_KEY") == "sk-test-key-12345"
                    assert os.environ.get("SERPER_API_KEY") == "serper-test-key-67890"
                    assert os.environ.get("DEVSYNTH_LLM_MODEL") == "gpt-3.5-turbo"
                    assert os.environ.get("DEVSYNTH_LLM_TEMPERATURE") == "0.8"

    def test_load_dotenv_file_not_found(self):
        """Test that load_dotenv handles the case where the .env file is not found."""
        # Mock os.path.exists to return False for the .env file
        with patch("os.path.exists", return_value=False):
            # Mock os.environ to track changes
            with patch.dict(os.environ, {}, clear=True):
                # Call load_dotenv
                load_dotenv()

                # Check that no environment variables were loaded
                assert "OPENAI_API_KEY" not in os.environ
                assert "SERPER_API_KEY" not in os.environ

    def test_get_settings_with_dotenv(self):
        """Test that get_settings uses values from a .env file."""
        # Create a mock .env file content
        env_content = """
        OPENAI_API_KEY=sk-test-key-12345
        SERPER_API_KEY=serper-test-key-67890
        DEVSYNTH_LLM_MODEL=gpt-3.5-turbo
        DEVSYNTH_LLM_TEMPERATURE=0.8
        """

        # Mock the open function to return our mock .env content
        with patch("builtins.open", mock_open(read_data=env_content)):
            # Mock os.path.exists to return True for the .env file
            with patch("os.path.exists", return_value=True):
                # Mock os.environ to track changes
                with patch.dict(os.environ, {}, clear=True):
                    # Call get_settings, which should load from .env
                    settings = get_settings()

                    # Check that values from .env file are used
                    assert settings["openai_api_key"] == "sk-test-key-12345"
                    assert settings["serper_api_key"] == "serper-test-key-67890"
                    assert settings["llm_model"] == "gpt-3.5-turbo"
                    assert settings["llm_temperature"] == 0.8

    def test_invalid_security_boolean_raises(self):
        """Invalid boolean values for security settings should raise errors."""
        with patch.dict(os.environ, {"DEVSYNTH_AUTHENTICATION_ENABLED": "maybe"}):
            with pytest.raises(ConfigurationError):
                get_settings(reload=True)

    def test_empty_openai_api_key_raises(self):
        """Empty API keys should be rejected."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": " "}):
            with pytest.raises(ConfigurationError):
                get_settings(reload=True)

    def test_kuzu_settings_defaults(self):
        """kuzu settings should use defaults when env vars are not set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings(reload=True)
            assert settings["kuzu_db_path"] is None
            assert settings["kuzu_embedded"] is True

    def test_kuzu_settings_from_env(self):
        """kuzu settings should respect environment variables."""
        env = {
            "DEVSYNTH_KUZU_DB_PATH": "/tmp/kuzu.db",
            "DEVSYNTH_KUZU_EMBEDDED": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(reload=True)
            assert settings["kuzu_db_path"] == "/tmp/kuzu.db"
            assert settings["kuzu_embedded"] is False
