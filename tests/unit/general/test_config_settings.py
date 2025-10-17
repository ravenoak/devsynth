"""
Unit tests for the configuration settings module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from devsynth.config import settings as settings_module
from devsynth.config.settings import get_llm_settings, get_settings, load_dotenv
from devsynth.exceptions import ConfigurationError


class TestConfigSettings:
    """Tests for the configuration settings module.

    ReqID: N/A"""

    def test_get_settings_default_values_returns_expected_result(self):
        """Test that get_settings returns default values when environment variables are not set.

        ReqID: N/A"""
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
            assert settings["memory_store_type"] == "memory"
            assert settings["llm_provider"] == "lmstudio"
            assert settings["llm_api_base"] == "http://localhost:1234"
            assert settings["llm_temperature"] == 0.7

    def test_get_settings_from_environment_variables_succeeds(self):
        """Test that get_settings uses values from environment variables when they are set.

        ReqID: N/A"""
        env_vars = {
            "DEVSYNTH_MEMORY_STORE": "file",
            "DEVSYNTH_LLM_PROVIDER": "openai",
            "DEVSYNTH_LLM_API_BASE": "https://api.openai.com/v1",
            "DEVSYNTH_LLM_MODEL": "gpt-4",
            "DEVSYNTH_LLM_TEMPERATURE": "0.5",
        }
        with patch.dict(os.environ, env_vars):
            settings = get_settings()
            assert settings["memory_store_type"] == "file"
            assert settings["llm_provider"] == "openai"
            assert settings["llm_api_base"] == "https://api.openai.com/v1"
            assert settings["llm_model"] == "gpt-4"
            assert settings["llm_temperature"] == 0.5

    def test_get_llm_settings_returns_expected_result(self):
        """Test that get_llm_settings returns the correct LLM settings.

        ReqID: N/A"""
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
    def test_boolean_environment_variables_succeeds(self, env_var, expected):
        """Test that boolean environment variables are parsed correctly.

        ReqID: N/A"""
        with patch.dict(os.environ, {"DEVSYNTH_LLM_AUTO_SELECT_MODEL": env_var}):
            settings = get_settings()
            assert settings["llm_auto_select_model"] is expected

    def test_load_dotenv_succeeds(self):
        """Test that load_dotenv loads environment variables from a .env file.

        ReqID: N/A"""
        env_content = """
        OPENAI_API_KEY=sk-test-key-12345
        SERPER_API_KEY=serper-test-key-67890
        DEVSYNTH_LLM_MODEL=gpt-3.5-turbo
        DEVSYNTH_LLM_TEMPERATURE=0.8
        """
        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                with patch.dict(os.environ, {}, clear=True):
                    load_dotenv()
                    assert os.environ.get("OPENAI_API_KEY") == "sk-test-key-12345"
                    assert os.environ.get("SERPER_API_KEY") == "serper-test-key-67890"
                    assert os.environ.get("DEVSYNTH_LLM_MODEL") == "gpt-3.5-turbo"
                    assert os.environ.get("DEVSYNTH_LLM_TEMPERATURE") == "0.8"

    def test_load_dotenv_file_not_found_succeeds(self):
        """Test that load_dotenv handles the case where the .env file is not found.

        ReqID: N/A"""
        with patch("os.path.exists", return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                load_dotenv()
                assert "OPENAI_API_KEY" not in os.environ
                assert "SERPER_API_KEY" not in os.environ

    def test_get_settings_with_dotenv_succeeds(self):
        """Test that get_settings uses values from a .env file.

        ReqID: N/A"""
        env_content = """
        OPENAI_API_KEY=sk-test-key-12345
        SERPER_API_KEY=serper-test-key-67890
        DEVSYNTH_LLM_MODEL=gpt-3.5-turbo
        DEVSYNTH_LLM_TEMPERATURE=0.8
        """
        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                with patch.dict(os.environ, {}, clear=True):
                    settings = get_settings()
                    assert settings["openai_api_key"] == "sk-test-key-12345"
                    assert settings["serper_api_key"] == "serper-test-key-67890"
                    assert settings["llm_model"] == "gpt-3.5-turbo"
                    assert settings["llm_temperature"] == 0.8

    def test_invalid_security_boolean_raises(self):
        """Invalid boolean values for security settings should raise errors.

        ReqID: N/A"""
        with patch.dict(os.environ, {"DEVSYNTH_AUTHENTICATION_ENABLED": "maybe"}):
            with pytest.raises(ConfigurationError):
                get_settings(reload=True)

    def test_empty_openai_api_key_raises(self):
        """Empty API keys should be rejected.

        ReqID: N/A"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": " "}):
            with pytest.raises(ConfigurationError):
                get_settings(reload=True)

    def test_kuzu_settings_defaults_succeeds(self):
        """kuzu settings should use defaults when env vars are not set.

        ReqID: N/A"""
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings(reload=True)
            assert settings["kuzu_db_path"] is None
            assert settings["kuzu_embedded"] is True

    def test_kuzu_settings_from_env_succeeds(self):
        """kuzu settings should respect environment variables.

        ReqID: N/A"""
        env = {
            "DEVSYNTH_KUZU_DB_PATH": "/tmp/kuzu.db",
            "DEVSYNTH_KUZU_EMBEDDED": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(reload=True)
            assert settings["kuzu_db_path"] == "/tmp/kuzu.db"
            assert settings["kuzu_embedded"] is False

    def test_kuzu_embedded_attribute_lookup_succeeds(self):
        """Module-level kuzu settings should mirror reloaded values.

        ReqID: N/A"""
        env = {"DEVSYNTH_KUZU_EMBEDDED": "false"}
        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(reload=True)
            assert settings.kuzu_embedded is False
            assert settings["kuzu_embedded"] is False
            assert settings_module.kuzu_embedded is False
            assert settings_module.KUZU_EMBEDDED is False
