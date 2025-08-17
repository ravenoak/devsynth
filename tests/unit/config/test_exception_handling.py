import os
from pathlib import Path

import pytest

from devsynth.config.loader import ConfigModel, load_config
from devsynth.config.settings import Settings, is_devsynth_managed_project
from devsynth.config.unified_loader import UnifiedConfig
from devsynth.exceptions import ConfigurationError


@pytest.mark.fast
def test_is_devsynth_managed_project_invalid_toml_returns_false(tmp_path: Path) -> None:
    """Invalid pyproject files are ignored.

    ReqID: N/A"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.devsynth\ninvalid")
    assert not is_devsynth_managed_project(str(tmp_path))


@pytest.mark.fast
def test_unified_config_exists_returns_false_on_invalid_toml(tmp_path: Path) -> None:
    """Unified config existence check handles bad TOML.

    ReqID: N/A"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.devsynth\ninvalid")
    cfg = ConfigModel(project_root=str(tmp_path))
    unified = UnifiedConfig(cfg, pyproject, use_pyproject=True)
    assert not unified.exists()


@pytest.mark.fast
def test_load_config_malformed_toml_raises_configuration_error(tmp_path: Path) -> None:
    """Malformed TOML raises a ConfigurationError.

    ReqID: N/A"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.devsynth\ninvalid")
    with pytest.raises(ConfigurationError):
        load_config(tmp_path)


@pytest.mark.fast
def test_load_config_invalid_values_raises_configuration_error(tmp_path: Path) -> None:
    """Invalid configuration values surface as ConfigurationError.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    yaml_file = cfg_dir / "project.yaml"
    yaml_file.write_text("kuzu_embedded: 'not_bool'\n")
    with pytest.raises(ConfigurationError):
        load_config(tmp_path)


@pytest.mark.fast
def test_set_default_memory_dir_handles_configuration_error(
    monkeypatch, tmp_path: Path
) -> None:
    """Configuration errors fall back to default memory path.

    ReqID: N/A"""
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\n")
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    def boom(_path: str) -> ConfigModel:  # type: ignore[override]
        raise ConfigurationError("boom")

    monkeypatch.setattr("devsynth.config.settings.load_config", boom)
    settings = Settings()
    expected = os.path.join(tmp_path, ".devsynth", "memory")
    assert settings.memory_file_path == expected
