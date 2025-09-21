import pytest
import toml

from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.exceptions import ConfigurationError


@pytest.mark.medium
def test_unified_loader_detects_yaml_succeeds(tmp_path):
    """use_pyproject is False when only YAML config exists.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("language: python\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert not unified.use_pyproject


@pytest.mark.medium
def test_unified_loader_detects_pyproject_succeeds(tmp_path):
    """use_pyproject is True when pyproject.toml exists.

    ReqID: N/A"""
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject


@pytest.mark.medium
def test_unified_loader_prefers_pyproject_succeeds(tmp_path):
    """pyproject.toml is used when both config files exist.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("language: python\n")
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject
    assert unified.config.language == "python"


@pytest.mark.medium
def test_unified_config_save_updates_pyproject_succeeds(tmp_path):
    """Saving config with use_pyproject=True updates the TOML table.

    ReqID: N/A"""
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    unified.set_language("python")
    unified.save()
    data = toml.load(tmp_path / "pyproject.toml")
    assert data["tool"]["devsynth"]["language"] == "python"


@pytest.mark.medium
def test_unified_config_exists_for_both_formats_returns_expected_result(tmp_path):
    """exists() returns True for YAML and TOML configurations.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("language: python\n")
    assert UnifiedConfigLoader.load(tmp_path).exists()
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='python'\n")
    assert UnifiedConfigLoader.load(tmp_path).exists()


@pytest.mark.medium
def test_unified_loader_falls_back_when_pyproject_missing_section_succeeds(tmp_path):
    """Loader selects YAML path when pyproject lacks DevSynth table.

    ReqID: N/A
    Issue: issues/configuration-loader.md"""

    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n")
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("language: ruby\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert not unified.use_pyproject
    assert unified.path == cfg_dir / "project.yaml"
    assert unified.config.language == "ruby"


@pytest.mark.medium
def test_unified_loader_malformed_pyproject_fails(tmp_path):
    """Malformed TOML surfaces as a configuration error.

    ReqID: N/A
    Issue: issues/configuration-loader.md"""

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.devsynth\nlanguage = 'python'\n")

    with pytest.raises(ConfigurationError) as exc_info:
        UnifiedConfigLoader.load(tmp_path)

    assert "Malformed TOML configuration" in str(exc_info.value)
    assert exc_info.value.details["config_key"] == str(pyproject)


@pytest.mark.medium
def test_unified_loader_malformed_yaml_fails(tmp_path):
    """Malformed YAML surfaces as a configuration error.

    ReqID: N/A
    Issue: issues/configuration-loader.md"""

    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    project_yaml = cfg_dir / "project.yaml"
    project_yaml.write_text("language: [python\n")

    with pytest.raises(ConfigurationError) as exc_info:
        UnifiedConfigLoader.load(tmp_path)

    assert "Malformed YAML configuration" in str(exc_info.value)
    assert exc_info.value.details["config_key"] == str(project_yaml)
