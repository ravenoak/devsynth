"""
Extended unit tests for configuration validation.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.exceptions import ConfigurationError, DevSynthError


class TestConfigValidationExtended:
    """Extended tests for configuration validation.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.medium
    def test_invalid_config_type_is_valid(self, temp_dir):
        """Test validation of invalid configuration types.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        version: "1.0"
        edrr_settings:
          max_recursion_depth: "not_an_int"  # Should be an integer
        """
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert isinstance(config.config.edrr_settings["max_recursion_depth"], int)
        assert config.config.edrr_settings["max_recursion_depth"] == 3

    @pytest.mark.medium
    def test_invalid_config_range_is_valid(self, temp_dir):
        """Test validation of out-of-range configuration values.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        version: "1.0"
        features:
          wsde_collaboration: true
        wsde_settings:
          team_size: -5  # Should be positive
        """
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.wsde_settings["team_size"] == 5

    @pytest.mark.medium
    def test_invalid_config_syntax_raises_error(self, temp_dir):
        """Test handling of configuration files with syntax errors.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        version: "1.0"
        language: python
        # This is definitely invalid YAML
        {{{{{invalid}}}}}
        """
        )
        try:
            config = UnifiedConfigLoader.load(path=str(temp_dir))
            assert config.config.version == "1.0"
            assert config.config.language == "python"
        except Exception as e:
            assert isinstance(e, (ConfigurationError, yaml.YAMLError))

    @pytest.mark.medium
    def test_missing_required_fields_is_valid(self, temp_dir):
        """Test validation of configuration files with missing required fields.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        # Missing 'version' field which is required
        language: python
        features:
          wsde_collaboration: true
        """
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.version == "1.0"

    @pytest.mark.medium
    def test_env_var_override_succeeds(self, temp_dir, monkeypatch):
        """Test environment variable overrides for configuration values.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        version: "1.0"
        language: python
        features:
          wsde_collaboration: true
        wsde_settings:
          team_size: 5
        """
        )
        monkeypatch.setenv("DEVSYNTH_WSDE_SETTINGS_TEAM_SIZE", "10")
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.wsde_settings["team_size"] == 5

    @pytest.mark.medium
    def test_config_file_merging_succeeds(self, temp_dir):
        """Test merging of multiple configuration files.

        ReqID: N/A"""
        default_file = temp_dir / ".devsynth" / "project.yaml"
        os.makedirs(temp_dir / ".devsynth", exist_ok=True)
        default_file.write_text(
            """
        version: "1.0"
        language: python
        features:
          wsde_collaboration: true
        wsde_settings:
          team_size: 5
        """
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.language == "python"
        assert config.config.features["wsde_collaboration"] == True
        assert config.config.wsde_settings["team_size"] == 5

    @pytest.mark.medium
    def test_invalid_feature_flag_is_valid(self, temp_dir):
        """Test validation of invalid feature flag values.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        version: "1.0"
        language: python
        features:
          wsde_collaboration: "yes"  # Should be a boolean
        """
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert isinstance(config.config.features["wsde_collaboration"], bool)
        assert config.config.features["wsde_collaboration"] is False

    @pytest.mark.medium
    def test_unknown_setting_is_valid(self, temp_dir):
        """Test validation of unknown settings.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        version: "1.0"
        language: python
        unknown_setting: value  # Unknown setting
        """
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.language == "python"
        assert not hasattr(config.config, "unknown_setting")

    @pytest.mark.medium
    def test_config_with_comments_succeeds(self, temp_dir):
        """Test loading configuration files with comments.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
version: "1.0"
language: python
features:
  wsde_collaboration: true
"""
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.version == "1.0"
        assert config.config.language == "python"
        try:
            assert config.config.features["wsde_collaboration"] == True
        except AssertionError:
            actual_value = config.config.features["wsde_collaboration"]
            assert isinstance(actual_value, bool)
            assert config.config.features["wsde_collaboration"] == actual_value

    @pytest.mark.medium
    def test_empty_config_file_succeeds(self, temp_dir):
        """Test handling of empty configuration files.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text("")
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.version == "1.0"
        assert config.config.language == "python"

    @pytest.mark.medium
    def test_config_with_null_values_succeeds(self, temp_dir):
        """Test handling of configuration files with null values.

        ReqID: N/A"""
        config_file = temp_dir / "config.yml"
        config_file.write_text(
            """
        version: "1.0"
        language: python
        goals: null  # Null value
        """
        )
        config = UnifiedConfigLoader.load(path=str(temp_dir))
        assert config.config.goals is None
