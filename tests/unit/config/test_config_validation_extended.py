"""
Extended unit tests for configuration validation.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.exceptions import DevSynthError, ConfigurationError


class TestConfigValidationExtended:
    """Extended tests for configuration validation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_invalid_config_type(self, temp_dir):
        """Test validation of invalid configuration types."""
        # Create a config file with an invalid type (string instead of int)
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        application:
          name: App
          version: "1.0"
        agents:
          max_agents: "not_an_int"  # Should be an integer
        """)

        # Attempt to load the config
        with pytest.raises(ConfigurationError):
            UnifiedConfigLoader.load(config_dir=str(temp_dir))

    def test_invalid_config_range(self, temp_dir):
        """Test validation of out-of-range configuration values."""
        # Create a config file with an out-of-range value (negative max_agents)
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        application:
          name: App
          version: "1.0"
        agents:
          max_agents: -5  # Should be positive
        """)

        # Attempt to load the config
        with pytest.raises(ConfigurationError):
            UnifiedConfigLoader.load(config_dir=str(temp_dir))

    def test_invalid_config_syntax(self, temp_dir):
        """Test handling of configuration files with syntax errors."""
        # Create a config file with a syntax error
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        application:
          name: App
          version: "1.0"
        agents:
          max_agents: 5
          default_timeout: 10
        # Missing colon after 'security'
        security
          input_validation: true
        """)

        # Attempt to load the config
        with pytest.raises(Exception):  # Could be YAML parsing error or ConfigurationError
            UnifiedConfigLoader.load(config_dir=str(temp_dir))

    def test_missing_required_fields(self, temp_dir):
        """Test validation of configuration files with missing required fields."""
        # Create a config file with missing required fields
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        # Missing 'application' section
        agents:
          max_agents: 5
          default_timeout: 10
        security:
          input_validation: true
        """)

        # Attempt to load the config
        with pytest.raises(ConfigurationError):
            UnifiedConfigLoader.load(config_dir=str(temp_dir))

    def test_env_var_override(self, temp_dir, monkeypatch):
        """Test environment variable overrides for configuration values."""
        # Create a basic config file
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        application:
          name: App
          version: "1.0"
        llm:
          default_provider: openai
          providers:
            openai:
              enabled: true
              model: gpt-3.5-turbo
        """)

        # Set environment variable to override the model
        monkeypatch.setenv("DEVSYNTH_LLM_PROVIDERS_OPENAI_MODEL", "gpt-4")

        # Load the config
        config = UnifiedConfigLoader.load(config_dir=str(temp_dir))

        # Check that the environment variable override was applied
        assert config.llm.providers.openai.model == "gpt-4"

    def test_config_file_merging(self, temp_dir):
        """Test merging of multiple configuration files."""
        # Create a default config file
        default_file = temp_dir / "default.yml"
        default_file.write_text("""
        application:
          name: App
          version: "1.0"
        llm:
          default_provider: openai
          providers:
            openai:
              enabled: true
              model: gpt-3.5-turbo
        """)

        # Create a user config file that overrides some values
        user_file = temp_dir / "user.yml"
        user_file.write_text("""
        llm:
          providers:
            openai:
              model: gpt-4
        """)

        # Load the config with both files
        with patch.object(UnifiedConfigLoader, '_find_config_files', return_value=[default_file, user_file]):
            config = UnifiedConfigLoader.load(config_dir=str(temp_dir))

        # Check that the values were merged correctly
        assert config.application.name == "App"
        assert config.llm.default_provider == "openai"
        assert config.llm.providers.openai.model == "gpt-4"

    def test_invalid_feature_flag(self, temp_dir):
        """Test validation of invalid feature flag values."""
        # Create a config file with an invalid feature flag value (string instead of boolean)
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        application:
          name: App
          version: "1.0"
        features:
          wsde_collaboration: "yes"  # Should be a boolean
        """)

        # Attempt to load the config
        with pytest.raises(ConfigurationError):
            UnifiedConfigLoader.load(config_dir=str(temp_dir))

    def test_unknown_provider(self, temp_dir):
        """Test validation of unknown provider configurations."""
        # Create a config file with an unknown provider
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        application:
          name: App
          version: "1.0"
        llm:
          default_provider: unknown_provider
          providers:
            openai:
              enabled: true
            unknown_provider:
              enabled: true
        """)

        # Attempt to load the config
        # This might not raise an error if unknown providers are allowed,
        # but we should at least check that the config loads
        config = UnifiedConfigLoader.load(config_dir=str(temp_dir))
        assert config.llm.default_provider == "unknown_provider"

    def test_config_with_comments(self, temp_dir):
        """Test loading configuration files with comments."""
        # Create a config file with comments
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        # Application configuration
        application:
          name: App  # The name of the application
          version: "1.0"  # The version of the application
        # LLM configuration
        llm:
          # The default provider to use
          default_provider: openai
          providers:
            # OpenAI configuration
            openai:
              enabled: true
              model: gpt-3.5-turbo
        """)

        # Load the config
        config = UnifiedConfigLoader.load(config_dir=str(temp_dir))

        # Check that the config was loaded correctly
        assert config.application.name == "App"
        assert config.llm.default_provider == "openai"
        assert config.llm.providers.openai.model == "gpt-3.5-turbo"

    def test_empty_config_file(self, temp_dir):
        """Test handling of empty configuration files."""
        # Create an empty config file
        config_file = temp_dir / "config.yml"
        config_file.write_text("")

        # Attempt to load the config
        with pytest.raises(ConfigurationError):
            UnifiedConfigLoader.load(config_dir=str(temp_dir))

    def test_config_with_null_values(self, temp_dir):
        """Test handling of configuration files with null values."""
        # Create a config file with null values
        config_file = temp_dir / "config.yml"
        config_file.write_text("""
        application:
          name: App
          version: "1.0"
        llm:
          default_provider: openai
          providers:
            openai:
              enabled: true
              model: null  # Null value
        """)

        # Load the config
        config = UnifiedConfigLoader.load(config_dir=str(temp_dir))

        # Check that the null value was handled correctly
        assert config.llm.providers.openai.model is None